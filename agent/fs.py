import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_name(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = SAFE_NAME_RE.sub("", name)
    return name or "untitled"


def iso_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass


def read_json_if_exists(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@dataclass
class Paths:
    root: str

    def mesh_dir(self, mesh: str) -> str:
        return os.path.join(self.root, sanitize_name(mesh))

    def correct_path(self, mesh: str) -> str:
        return os.path.join(self.mesh_dir(mesh), "correct.json")

    def forest_path(self) -> str:
        return os.path.join(self.root, "forest.json")

    def branch_dir(self, mesh: str, branch: str) -> str:
        return os.path.join(self.mesh_dir(mesh), sanitize_name(branch))

    def commit_dir(self, mesh: str, branch: str, commit_id: str) -> str:
        return os.path.join(self.branch_dir(mesh, branch), sanitize_name(commit_id))


def ensure_branch(paths: Paths, mesh: str, branch: str) -> None:
    os.makedirs(paths.branch_dir(mesh, branch), exist_ok=True)


def remove_branch(paths: Paths, mesh: str, branch: str) -> None:
    import shutil
    d = paths.branch_dir(mesh, branch)
    if os.path.isdir(d):
        shutil.rmtree(d)


def list_meshes(paths: Paths) -> List[str]:
    if not os.path.isdir(paths.root):
        return []
    items = []
    for name in os.listdir(paths.root):
        if name == "forest.json":
            continue
        full = os.path.join(paths.root, name)
        if os.path.isdir(full):
            items.append(name)
    return sorted(items)


def list_branches(paths: Paths, mesh: str) -> List[str]:
    d = paths.mesh_dir(mesh)
    if not os.path.isdir(d):
        return []
    out: List[str] = []
    for name in os.listdir(d):
        full = os.path.join(d, name)
        if os.path.isdir(full):
            out.append(name)
    return sorted(out)


def list_commits(paths: Paths, mesh: str, branch: str) -> List[str]:
    d = paths.branch_dir(mesh, branch)
    if not os.path.isdir(d):
        return []
    out: List[str] = []
    for name in os.listdir(d):
        full = os.path.join(d, name)
        if os.path.isdir(full):
            out.append(name)
    return sorted(out, reverse=True)


def read_correct(paths: Paths, mesh: str) -> Optional[str]:
    data = read_json_if_exists(paths.correct_path(mesh))
    if not data:
        return None
    return data.get("current_branch") or data.get("correct_branch")


def write_correct(paths: Paths, mesh: str, branch: str) -> None:
    payload = {
        "schema_version": "1.0",
        "current_branch": sanitize_name(branch),
        "updated_at": iso_now(),
    }
    atomic_write_json(paths.correct_path(mesh), payload)


def build_forest(paths: Paths) -> Dict[str, Any]:
    meshes_index: Dict[str, Any] = {}
    for mesh in list_meshes(paths):
        branches_obj: Dict[str, Any] = {}
        for br in list_branches(paths, mesh):
            commits_meta = [
                {"id": c, "datetime": None, "message": None, "tag": None}
                for c in list_commits(paths, mesh, br)
            ]
            branches_obj[br] = {"commits": commits_meta}
        meshes_index[mesh] = {
            "correct_branch": read_correct(paths, mesh),
            "branches": branches_obj,
        }
    return {
        "schema_version": "1.0",
        "updated_at": iso_now(),
        "meshes": meshes_index,
    }


def read_forest(paths: Paths) -> Dict[str, Any]:
    data = read_json_if_exists(paths.forest_path())
    if data is None:
        return {"schema_version": "1.0", "updated_at": iso_now(), "meshes": {}}
    return data


def write_forest(paths: Paths, forest: Dict[str, Any]) -> None:
    forest["updated_at"] = iso_now()
    atomic_write_json(paths.forest_path(), forest)


def ensure_commit_structure(paths: Paths, mesh: str, branch: str, commit_id: str) -> None:
    d = paths.commit_dir(mesh, branch, commit_id)
    os.makedirs(d, exist_ok=True)
    # Create placeholder commit.json if not exists
    commit_json = os.path.join(d, "commit.json")
    if not os.path.exists(commit_json):
        atomic_write_json(
            commit_json,
            {
                "data_version": "1.0",
                "datetime": iso_now(),
                "branch": sanitize_name(branch),
                "mesh_name": sanitize_name(mesh),
            },
        )


