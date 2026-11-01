"""Tests sur la séparation backend / frontend imposée par le cahier des charges."""
import ast
from pathlib import Path


def _modules_importes(fichier):
    arbre = ast.parse(Path(fichier).read_text(encoding="utf-8"))
    modules = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            modules.update(alias.name for alias in noeud.names)
        elif isinstance(noeud, ast.ImportFrom) and noeud.module:
            modules.add(noeud.module)
    return modules


def test_le_backend_n_importe_pas_streamlit():
    for fichier in Path("backend").rglob("*.py"):
        modules = _modules_importes(fichier)
        assert not any(m.split(".")[0] == "streamlit" for m in modules), fichier


def test_le_frontend_n_appelle_que_le_service():
    modules = _modules_importes("frontend/app.py")
    backend = {m for m in modules if m.split(".")[0] == "backend"}
    assert backend == {"backend.service"}
