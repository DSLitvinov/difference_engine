from typing import Dict, Any


def validate_forest(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("forest.json must be an object")
    if "meshes" not in data or not isinstance(data["meshes"], dict):
        raise ValueError("forest.json missing 'meshes' object")


def validate_correct(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("correct.json must be an object")
    if "current_branch" not in data or not isinstance(data["current_branch"], str):
        raise ValueError("correct.json missing 'current_branch' string")


