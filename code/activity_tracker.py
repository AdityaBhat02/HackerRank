"""Activity Tracker for Ghost Data Still Exists.
Tracks and filters operational activity stream from dataset/system_activity.csv.
All activity checks strictly obey the case's audit_at cutoff.
"""

import csv
from typing import Dict, List, Any, Optional, Set

class ActivityTracker:
    def __init__(self, activity_csv_path: str):
        self.activity_csv_path = activity_csv_path
        self.activities: List[Dict[str, str]] = []
        self.by_resource_id: Dict[str, List[Dict[str, str]]] = {}
        self._load()

    def _load(self):
        with open(self.activity_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.activities.append(row)
                res = row['resource_id'].strip()
                if res:
                    self.by_resource_id.setdefault(res, []).append(row)

    def get_activities_for_resource(self, resource_id: str, max_time: Optional[str] = None) -> List[Dict[str, str]]:
        acts = self.by_resource_id.get(resource_id, [])
        if max_time:
            return [a for a in acts if a['event_time'] <= max_time]
        return acts

    def find_resources_for_user(self, user_id: str, emails: Set[str], max_time: Optional[str] = None) -> Set[str]:
        """Finds any resource IDs mentioned in system activity associated with the user up to max_time."""
        matched_resources = set()
        user_tokens = {user_id.lower()}
        for e in emails:
            if e:
                user_tokens.add(e.lower())

        for act in self.activities:
            if max_time and act['event_time'] > max_time:
                continue

            details_lower = act['details'].lower()
            res_id = act['resource_id'].strip()
            
            # Check if any user token appears in details
            for tok in user_tokens:
                if tok and tok in details_lower:
                    if res_id:
                        matched_resources.add(res_id)
                    break

        return matched_resources
