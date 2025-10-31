import json
import os
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, Optional


DEFAULT_AGENT_URL = os.environ.get("DFM_AGENT_URL", "http://127.0.0.1:8765")


class AgentError(Exception):
    pass


class AgentClient:
    def __init__(self, base_url: str = DEFAULT_AGENT_URL, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Content-Type": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = resp.read()
                if not payload:
                    return {}
                return json.loads(payload.decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8")
            except Exception:
                detail = str(e)
            raise AgentError(f"HTTP {e.code} for {method} {path}: {detail}")
        except Exception as e:
            raise AgentError(f"Request failed for {method} {path}: {e}")

    # Service methods
    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def rescan(self, mesh: Optional[str] = None) -> Dict[str, Any]:
        path = "/rescan"
        if mesh:
            # Send as query param for simplicity
            path = f"{path}?mesh={urllib.parse.quote(mesh)}"
        return self._request("POST", path)

    def get_forest(self) -> Dict[str, Any]:
        return self._request("GET", "/forest")

    def get_mesh(self, mesh: str) -> Dict[str, Any]:
        return self._request("GET", f"/mesh/{urllib.parse.quote(mesh)}")

    def get_mesh_state(self, mesh: str) -> Dict[str, Any]:
        return self._request("GET", f"/mesh/{urllib.parse.quote(mesh)}/state")

    def get_branches(self, mesh: str) -> Dict[str, Any]:
        return self._request("GET", f"/mesh/{urllib.parse.quote(mesh)}/branches")

    def get_commits(self, mesh: str, branch: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/mesh/{urllib.parse.quote(mesh)}/branch/{urllib.parse.quote(branch)}/commits",
        )

    def set_correct_branch(self, mesh: str, branch: str) -> Dict[str, Any]:
        return self._request("POST", f"/mesh/{urllib.parse.quote(mesh)}/correct", {"branch": branch})

    def create_branch(self, mesh: str, branch: str) -> Dict[str, Any]:
        return self._request("POST", f"/mesh/{urllib.parse.quote(mesh)}/branch", {"branch": branch})

    def delete_branch(self, mesh: str, branch: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/mesh/{urllib.parse.quote(mesh)}/branch/{urllib.parse.quote(branch)}")

    def create_commit(self, mesh: str, branch: str, message: str, tag: Optional[str] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"branch": branch, "message": message}
        if tag is not None:
            body["tag"] = tag
        return self._request("POST", f"/mesh/{urllib.parse.quote(mesh)}/commit", body)

    def delete_commit(self, mesh: str, branch: str, commit_id: str) -> Dict[str, Any]:
        return self._request(
            "DELETE",
            f"/mesh/{urllib.parse.quote(mesh)}/branch/{urllib.parse.quote(branch)}/commit/{urllib.parse.quote(commit_id)}",
        )


