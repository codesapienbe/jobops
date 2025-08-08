from __future__ import annotations

from typing import Optional, Dict, Any, List
import requests


class LinearService:
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key or ""
        self.url = "https://api.linear.app/graphql"

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def test_connection(self, timeout: float = 3.0) -> bool:
        if not self.api_key:
            return False
        try:
            payload = {"query": "query { viewer { id } }"}
            r = requests.post(self.url, json=payload, headers=self._headers(), timeout=timeout)
            return r.ok
        except Exception:
            return False

    def create_issue(self, *, title: str, description: str, team_id: str, project_id: Optional[str] = None, label_ids: Optional[List[str]] = None, priority: Optional[int] = None, parent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        input_obj: Dict[str, Any] = {
            "title": title,
            "description": description,
            "teamId": team_id,
        }
        if project_id:
            input_obj["projectId"] = project_id
        if label_ids:
            input_obj["labelIds"] = label_ids
        if priority is not None:
            input_obj["priority"] = priority
        if parent_id:
            input_obj["parentId"] = parent_id

        mutation = """
        mutation($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            issue { id title url }
          }
        }
        """
        try:
            r = requests.post(self.url, json={"query": mutation, "variables": {"input": input_obj}}, headers=self._headers(), timeout=8.0)
            data = r.json()
            return (data.get("data") or {}).get("issueCreate", {}).get("issue")
        except Exception:
            return None
