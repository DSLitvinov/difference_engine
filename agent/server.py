import os
import threading
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .fs import Paths, sanitize_name, ensure_branch, remove_branch, list_branches, list_commits, read_correct, write_correct, build_forest, read_forest, write_forest, ensure_commit_structure
from .schemas import validate_forest

def _iso_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


class SetCorrectBranchBody(BaseModel):
    branch: str


class CreateBranchBody(BaseModel):
    branch: str


class CreateCommitBody(BaseModel):
    branch: str
    message: str
    tag: Optional[str] = None


class AgentConfig(BaseModel):
    data_root: str


class AgentState:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._locks: Dict[str, threading.Lock] = {}

    def get_mesh_lock(self, mesh: str) -> threading.Lock:
        if mesh not in self._locks:
            self._locks[mesh] = threading.Lock()
        return self._locks[mesh]


def create_app(data_root: Optional[str] = None) -> FastAPI:
    root = data_root or os.path.abspath(os.path.join(os.getcwd(), "difference_engine"))
    os.makedirs(root, exist_ok=True)
    app = FastAPI(title="Difference Engine Agent", version="1.0.0")
    state = AgentState(AgentConfig(data_root=root))
    paths = Paths(root)

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {"status": "ok", "version": app.version, "data_root": state.config.data_root}

    @app.post("/rescan")
    def rescan(mesh: Optional[str] = None) -> Dict[str, Any]:
        # Rebuild index from disk (optionally for a single mesh)
        forest = build_forest(paths)
        try:
            validate_forest(forest)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Forest validation failed: {e}")
        write_forest(paths, forest)
        if mesh:
            return {"status": "ok", "mesh": mesh}
        return {"status": "ok"}

    @app.get("/forest")
    def forest() -> Dict[str, Any]:
        return read_forest(paths)

    @app.get("/mesh/{mesh}")
    def get_mesh(mesh: str) -> Dict[str, Any]:
        mesh_s = sanitize_name(mesh)
        branches_obj: Dict[str, Any] = {}
        for br in list_branches(paths, mesh_s):
            commits_meta = [
                {"id": c, "datetime": None, "message": None, "tag": None}
                for c in list_commits(paths, mesh_s, br)
            ]
            branches_obj[br] = {"commits": commits_meta}
        return {
            "mesh": mesh_s,
            "correct_branch": read_correct(paths, mesh_s),
            "branches": branches_obj,
        }

    @app.get("/mesh/{mesh}/branches")
    def get_mesh_branches(mesh: str) -> Dict[str, Any]:
        mesh_s = sanitize_name(mesh)
        return {"mesh": mesh_s, "branches": list_branches(paths, mesh_s)}

    @app.get("/mesh/{mesh}/branch/{branch}/commits")
    def get_commits(mesh: str, branch: str) -> Dict[str, Any]:
        mesh_s = sanitize_name(mesh)
        br_s = sanitize_name(branch)
        return {"mesh": mesh_s, "branch": br_s, "commits": list_commits(paths, mesh_s, br_s)}

    @app.get("/mesh/{mesh}/state")
    def get_mesh_state(mesh: str) -> Dict[str, Any]:
        return get_mesh(mesh)

    @app.post("/mesh/{mesh}/correct")
    def set_correct(mesh: str, body: SetCorrectBranchBody) -> Dict[str, Any]:
        mesh_s = sanitize_name(mesh)
        br_s = sanitize_name(body.branch)
        lock = state.get_mesh_lock(mesh_s)
        with lock:
            branches = list_branches(paths, mesh_s)
            if br_s not in branches:
                raise HTTPException(status_code=404, detail="Branch not found")
            write_correct(paths, mesh_s, br_s)
        return {"mesh": mesh_s, "correct_branch": br_s, "updated_at": _iso_now()}

    @app.post("/mesh/{mesh}/branch")
    def create_branch(mesh: str, body: CreateBranchBody) -> Dict[str, Any]:
        mesh_s = sanitize_name(mesh)
        br_s = sanitize_name(body.branch)
        lock = state.get_mesh_lock(mesh_s)
        with lock:
            ensure_branch(paths, mesh_s, br_s)
            # Update forest index lazily by rebuild
            write_forest(paths, build_forest(paths))
        return {"mesh": mesh_s, "branch": br_s, "status": "created"}

    @app.delete("/mesh/{mesh}/branch/{branch}")
    def delete_branch(mesh: str, branch: str) -> Dict[str, Any]:
        mesh_s = sanitize_name(mesh)
        br_s = sanitize_name(branch)
        lock = state.get_mesh_lock(mesh_s)
        with lock:
            # prevent deleting correct branch
            current = read_correct(paths, mesh_s)
            if current == br_s:
                raise HTTPException(status_code=409, detail="Cannot delete current/correct branch")
            remove_branch(paths, mesh_s, br_s)
            write_forest(paths, build_forest(paths))
        return {"mesh": mesh_s, "branch": br_s, "status": "deleted"}

    @app.post("/mesh/{mesh}/commit")
    def create_commit(mesh: str, body: CreateCommitBody) -> Dict[str, Any]:
        mesh_s = sanitize_name(mesh)
        br_s = sanitize_name(body.branch)
        lock = state.get_mesh_lock(mesh_s)
        with lock:
            # commit id like YYYY-MM-DD_HH-MM-SS
            commit_id = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            ensure_commit_structure(paths, mesh_s, br_s, commit_id)
            write_forest(paths, build_forest(paths))
        return {
            "mesh": mesh_s,
            "branch": br_s,
            "commit": {
                "id": commit_id,
                "datetime": _iso_now(),
                "message": body.message,
                "tag": body.tag,
            },
            "status": "created",
        }

    @app.delete("/mesh/{mesh}/branch/{branch}/commit/{commit_id}")
    def delete_commit(mesh: str, branch: str, commit_id: str) -> Dict[str, Any]:
        mesh_s = sanitize_name(mesh)
        br_s = sanitize_name(branch)
        commit_s = sanitize_name(commit_id)
        lock = state.get_mesh_lock(mesh_s)
        with lock:
            import shutil
            d = paths.commit_dir(mesh_s, br_s, commit_s)
            if os.path.isdir(d):
                shutil.rmtree(d)
            write_forest(paths, build_forest(paths))
        return {"mesh": mesh_s, "branch": br_s, "commit_id": commit_s, "status": "deleted"}

    return app


# Uvicorn entrypoint convenience
def run(host: str = "127.0.0.1", port: int = 8765, data_root: Optional[str] = None) -> None:
    import uvicorn

    app = create_app(data_root)
    uvicorn.run(app, host=host, port=port)


