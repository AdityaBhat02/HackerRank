"""Request Classifier for Ghost Data Still Exists.
Determines whether a user request authorizes account or personal data deletion.
Non-deletion requests (e.g. data export only, updating details while keeping account active,
access requests, billing inquiries, login help, or marketing unsubscribe only) return False -> NOT_APPLICABLE.
Loads prompt template from code/prompts/request_classifier_prompt.txt.

Decision procedure (deterministic, evaluated in order):
  1. Explicit negation / keep-active language            -> NOT a deletion request
  2. Deletion verb targeted at the account / personal data -> deletion request
  3. Multilingual account-deletion phrasing               -> deletion request
  4. Anything else (deletion verb scoped to marketing lists, records, invoices, ...) -> NOT a deletion request
"""

import os
import re
from typing import Dict

_DEL_VERB = r"(?:delet|eras|remov|clos|purg|wip|cancel|terminat)\w*"
_TARGET = r"(?:account|profile|personal[\s-]+(?:data|information)|my\s+data|all\s+(?:of\s+)?my\s+(?:data|information))"


class RequestClassifier:
    def __init__(self, prompt_path: str = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.prompt_path = prompt_path or os.path.join(base_dir, "prompts", "request_classifier_prompt.txt")
        self.prompt_template = ""
        # Counts classifier invocations. The classifier is fully local/deterministic: no model tokens are consumed.
        self.token_usage = {"input": 0, "output": 0, "calls": 0}
        self._load_prompt()

        # 1. Negation / keep-active patterns: the user explicitly does NOT want erasure.
        self.negation_patterns = [
            r"\bnot\s+(?:asking|requesting|a\s+request|looking)\s+(?:for|to)\s+(?:an?\s+)?(?:the\s+)?" + _DEL_VERB,
            r"\bnot\s+a\s+(?:deletion|erasure)\s+request",
            r"\b(?:do\s+not|don'?t|never|please\s+don'?t)\s+(?:\w+\s+){0,2}?" + _DEL_VERB,
            r"\bwithout\s+(?:removing|deleting|erasing|closing)",
            r"\b(?:leave|keep)\s+(?:the|my)\s+(?:account|profile)\b[^.]*\b(?:active|in\s+place|as\s+it\s+is|open)",
            r"\bkeep\s+(?:the|my)\s+account\s+as\s+it\s+is",
            r"\bcontinue\s+using\s+the\s+service",
            r"\bstill\s+(?:need|use|want)\s+(?:the|my|this|it)\b",
            # Multilingual negations
            r"\bno\s+(?:deseo|quiero)\s+(?:eliminar|borrar)",
            r"\bne\s+(?:pas|souhaite\s+pas)\s+supprim",
            r"\bnão\s+(?:quero\s+)?(?:excluir|apagar)",
            r"\bnicht\s+lösch",
            r"削除しないで", r"삭제하지\s*마",
        ]

        # 2. English: deletion verb aimed at the account / personal data (either word order).
        self.targeted_patterns = [
            _DEL_VERB + r"\s+(?:[\w'-]+\s+){0,4}?" + _TARGET,     # "delete this account", "deletion of the account"
            _TARGET + r"[\w\s,'-]{0,50}?\b" + _DEL_VERB,           # "account ... to be erased", "account-deletion"
            r"\bright\s+to\s+(?:erasure|be\s+forgotten)",
            r"\bforget\s+me\b",
        ]

        # 3. Multilingual account-deletion phrasing (ES, PT, FR, IT, DE, JA, KO).
        self.multilingual_patterns = [
            r"(?:eliminaci[oó]n|borrado|eliminar|borrar)\s+(?:\w+\s+){0,3}(?:la\s+)?cuenta",
            r"(?:exclus[aã]o|excluir|apagar|elimina[çc][aã]o)\s+(?:\w+\s+){0,3}(?:da\s+)?conta",
            r"(?:suppression|supprimer|effacement)\s+(?:\w+\s+){0,3}(?:du\s+)?compte",
            r"(?:cancellazione|cancellare|eliminazione)\s+(?:\w+\s+){0,3}(?:dell?')?account",
            r"(?:konto|benutzerkonto)\w*\s+(?:\w+\s+){0,4}lösch|lösch\w*\s+(?:\w+\s+){0,4}(?:konto|daten)",
            r"アカウント.{0,15}(?:削除|消去)|退会",
            r"계정.{0,15}(?:삭제|탈퇴)|회원\s*탈퇴",
        ]

        # 4. Non-deletion scope markers: if no account-level deletion target matched, a request
        #    about only these topics (marketing opt-out, single objects, access, login help) is NOT_APPLICABLE.
        self.non_deletion_scope_patterns = [
            r"\bmarketing\b", r"\bpromotional\b", r"\bnewsletter", r"\bunsubscrib", r"\bmailing\s+list",
            r"\bsaved\s+card", r"\bpayment\s+method", r"\breview\b(?!\s+(?:any|the|all)\s+(?:identifiers|records|account|data))",
            r"\binvoice", r"\breceipt", r"\bpassword\b", r"\blog\s*in\b|\blogin\b", r"\bpause\b", r"\bfreeze\b",
            r"\b(?:download|copy|export)\s+(?:of\s+)?(?:my|the|all)\b", r"\bwhat\s+personal\s+information\s+you\s+hold",
            r"\bmisspell", r"\bout\s+of\s+date\b", r"\bchange\s+the\s+email",
        ]

        # 5. Broad deletion stems (EN/ES/FR/DE/IT/PT/JA/KO) used for indirect follow-up requests such as
        #    "remove that search result", "finish the deletion", "the profile is still there".
        self.deletion_stems = [
            "delet", "eras", "purg", "wipe", "remov", "close", "closing", "cancel",
            "supprim", "suppression", "elimin", "borr", "exclus",
            "lösch", "loesch", "cancell", "dimentic",
            "forget", "forgotten", "still exist", "still appear", "still be found", "is gone",
            "삭제", "탈퇴", "지워", "削除", "消去", "解約", "退会",
        ]

    def _load_prompt(self):
        if os.path.exists(self.prompt_path):
            try:
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    self.prompt_template = f.read()
            except Exception:
                pass

    def classify(self, request_text: str) -> str:
        """Returns 'DELETION' or 'NOT_DELETION' with a deterministic rule trace."""
        return "DELETION" if self.is_deletion_request(request_text) else "NOT_DELETION"

    def is_deletion_request(self, request_text: str) -> bool:
        if not request_text or not request_text.strip():
            return False
        self.token_usage["calls"] += 1
        text = " ".join(request_text.lower().split())

        for pat in self.negation_patterns:
            if re.search(pat, text):
                return False
        for pat in self.targeted_patterns + self.multilingual_patterns:
            if re.search(pat, text):
                return True
        for pat in self.non_deletion_scope_patterns:
            if re.search(pat, text):
                return False
        return any(stem in text for stem in self.deletion_stems)

    def get_token_usage(self) -> Dict[str, int]:
        return self.token_usage
