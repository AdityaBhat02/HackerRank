"""Configuration module for Ghost Data Still Exists AI Deletion Audit Agent."""

import os
from dataclasses import dataclass

def _resolve_dataset_dir(base_dir: str, repo_root: str) -> str:
    if os.environ.get("DATASET_DIR") and os.path.isdir(os.environ.get("DATASET_DIR")):
        return os.path.abspath(os.environ.get("DATASET_DIR"))
    candidates = [
        os.path.join(repo_root, "dataset"),
        os.path.join(base_dir, "..", "dataset"),
        os.path.join(base_dir, "dataset"),
        os.path.join(os.getcwd(), "dataset"),
        os.path.abspath("dataset"),
    ]
    for c in candidates:
        if os.path.isdir(c) and os.path.exists(os.path.join(c, "deletion_requests.csv")):
            return os.path.abspath(c)
    return os.path.abspath(os.path.join(repo_root, "dataset"))

def _resolve_output_path(base_dir: str, repo_root: str, dataset_dir: str) -> str:
    if os.environ.get("OUTPUT_CSV_PATH"):
        return os.path.abspath(os.environ.get("OUTPUT_CSV_PATH"))
    if os.path.isdir(os.path.join(repo_root, "dataset")):
        return os.path.abspath(os.path.join(repo_root, "output.csv"))
    return os.path.abspath("output.csv")

@dataclass
class Config:
    # Directory paths
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    REPO_ROOT: str = os.path.abspath(os.path.join(BASE_DIR, ".."))
    PROMPTS_DIR: str = os.path.join(BASE_DIR, "prompts")
    CACHE_DIR: str = os.path.join(BASE_DIR, "cache")
    EVALUATION_DIR: str = os.path.join(BASE_DIR, "evaluation")
    
    DATASET_DIR: str = ""
    OUTPUT_CSV_PATH: str = ""
    
    DELETION_REQUESTS_PATH: str = ""
    SAMPLE_REQUESTS_PATH: str = ""
    SAMPLE_OUTPUT_PATH: str = ""
    USER_IDENTITIES_PATH: str = ""
    USER_AUDIT_LOG_PATH: str = ""
    SYSTEM_ACTIVITY_PATH: str = ""
    DELETION_RULES_PATH: str = ""
    EVIDENCE_FILES_PATH: str = ""

    # Model configuration
    MODEL_PROVIDER: str = "Google DeepMind"
    MODEL_NAME: str = "gemini-3.8-flash"
    INTENT_MODEL: str = "gemini-3.8-flash"
    VISION_MODEL: str = "gemini-3.8-flash"
    
    # Performance & caching
    USE_MULTIMODAL_CACHE: bool = True
    ENABLE_ACTIVITY_CLUSTERING: bool = True
    MAX_WORKER_TIME_WINDOW_HOURS: int = 4
    
    # Output specification
    TOTAL_EVALUATION_CASES: int = 518
    TOTAL_SAMPLE_CASES: int = 32

    def __post_init__(self):
        self.DATASET_DIR = _resolve_dataset_dir(self.BASE_DIR, self.REPO_ROOT)
        self.OUTPUT_CSV_PATH = _resolve_output_path(self.BASE_DIR, self.REPO_ROOT, self.DATASET_DIR)
        
        self.DELETION_REQUESTS_PATH = os.path.join(self.DATASET_DIR, "deletion_requests.csv")
        self.SAMPLE_REQUESTS_PATH = os.path.join(self.DATASET_DIR, "sample_deletion_requests.csv")
        self.SAMPLE_OUTPUT_PATH = os.path.join(self.DATASET_DIR, "sample_output.csv")
        self.USER_IDENTITIES_PATH = os.path.join(self.DATASET_DIR, "user_identities.csv")
        self.USER_AUDIT_LOG_PATH = os.path.join(self.DATASET_DIR, "user_audit_log.csv")
        self.SYSTEM_ACTIVITY_PATH = os.path.join(self.DATASET_DIR, "system_activity.csv")
        self.DELETION_RULES_PATH = os.path.join(self.DATASET_DIR, "deletion_rules.csv")
        self.EVIDENCE_FILES_PATH = os.path.join(self.DATASET_DIR, "evidence_files.csv")

config = Config()
