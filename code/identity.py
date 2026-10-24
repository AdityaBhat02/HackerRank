"""Identity Resolution Module for Ghost Data Still Exists.
Resolves primary and historical identifiers for users using:
- dataset/user_identities.csv
- dataset/user_audit_log.csv
"""

import csv
import hashlib
from typing import Dict, List, Set, Optional, Any

class UserProfile:
    def __init__(self, user_id: str, name: str, email: str, phone: str, email_hash: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.email_hash = email_hash
        self.historical_emails: Set[str] = set()
        self.historical_phones: Set[str] = set()
        self.historical_names: Set[str] = set()
        self.historical_hashes: Set[str] = set()

    @property
    def all_emails(self) -> Set[str]:
        emails = {self.email.strip().lower()} if self.email else set()
        for e in self.historical_emails:
            if e:
                emails.add(e.strip().lower())
        return emails

    @property
    def all_hashes(self) -> Set[str]:
        hashes = {self.email_hash.strip()} if self.email_hash else set()
        for h in self.historical_hashes:
            if h:
                hashes.add(h.strip())
        return hashes

    @property
    def all_phones(self) -> Set[str]:
        phones = {self.phone.strip()} if self.phone else set()
        for p in self.historical_phones:
            if p:
                phones.add(p.strip())
        return phones

    @property
    def all_names(self) -> Set[str]:
        names = {self.name.strip().lower()} if self.name else set()
        for n in self.historical_names:
            if n:
                names.add(n.strip().lower())
        return names


class IdentityResolver:
    def __init__(self, identities_csv_path: str, audit_log_csv_path: str):
        self.identities_csv_path = identities_csv_path
        self.audit_log_csv_path = audit_log_csv_path
        self.profiles_by_user_id: Dict[str, UserProfile] = {}
        self.user_id_by_email: Dict[str, str] = {}
        self.user_id_by_hash: Dict[str, str] = {}
        self._load()

    def _load(self):
        # 1. Load current identities
        with open(self.identities_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row['user_id'].strip()
                name = row['name'].strip()
                email = row['email'].strip()
                phone = row['phone'].strip()
                ehash = row['email_hash'].strip()
                prof = UserProfile(uid, name, email, phone, ehash)
                self.profiles_by_user_id[uid] = prof
                if email:
                    self.user_id_by_email[email.lower()] = uid
                if ehash:
                    self.user_id_by_hash[ehash] = uid

        # 2. Load historical identity changes from audit log
        with open(self.audit_log_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row['user_id'].strip()
                field = row['field_name'].strip()
                old_val = row['old_value'].strip()
                new_val = row['new_value'].strip()

                if uid not in self.profiles_by_user_id:
                    self.profiles_by_user_id[uid] = UserProfile(uid, "", "", "", "")

                prof = self.profiles_by_user_id[uid]
                if field == 'email':
                    if old_val:
                        prof.historical_emails.add(old_val.lower())
                        self.user_id_by_email[old_val.lower()] = uid
                    if new_val:
                        prof.historical_emails.add(new_val.lower())
                        self.user_id_by_email[new_val.lower()] = uid
                elif field in ('email_hash', 'hash'):
                    if old_val:
                        prof.historical_hashes.add(old_val)
                        self.user_id_by_hash[old_val] = uid
                    if new_val:
                        prof.historical_hashes.add(new_val)
                        self.user_id_by_hash[new_val] = uid
                elif field == 'phone':
                    if old_val:
                        prof.historical_phones.add(old_val)
                    if new_val:
                        prof.historical_phones.add(new_val)
                elif field in ('name', 'full_name'):
                    if old_val:
                        prof.historical_names.add(old_val.lower())
                    if new_val:
                        prof.historical_names.add(new_val.lower())

        # Ensure all current and historical emails have corresponding SHA256 hashes mapped
        for uid, prof in self.profiles_by_user_id.items():
            for em in prof.all_emails:
                if em:
                    h = hashlib.sha256(em.encode('utf-8')).hexdigest()
                    prof.historical_hashes.add(h)
                    if h not in self.user_id_by_hash:
                        self.user_id_by_hash[h] = uid

    def resolve_user_by_email(self, email: str) -> Optional[UserProfile]:
        clean_email = email.strip().lower()
        uid = self.user_id_by_email.get(clean_email)
        if uid:
            return self.profiles_by_user_id.get(uid)
        return None

    def resolve_user_by_hash(self, hash_val: str) -> Optional[UserProfile]:
        clean_hash = hash_val.strip()
        uid = self.user_id_by_hash.get(clean_hash)
        if uid:
            return self.profiles_by_user_id.get(uid)
        return None

    def resolve_user(self, key: str) -> Optional[UserProfile]:
        if not key:
            return None
        key = key.strip()
        if '@' in key:
            return self.resolve_user_by_email(key)
        if key in self.profiles_by_user_id:
            return self.profiles_by_user_id[key]
        if key in self.user_id_by_hash:
            return self.profiles_by_user_id[self.user_id_by_hash[key]]
        return None

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        return self.profiles_by_user_id.get(user_id)
