"""Réglages communs aux tests."""
import os
from pathlib import Path

import pytest

# Les chemins de config.py partent de la racine du dépôt :
# on s'y place pour que `pytest` marche depuis n'importe quel dossier.
RACINE = Path(__file__).resolve().parents[1]
os.chdir(RACINE)

from backend import train  # noqa: E402
from backend.config import MODEL_SAVE_PATH  # noqa: E402


@pytest.fixture(scope="session")
def modele_entraine():
    """Entraîne le modèle s'il n'a pas encore été sauvegardé."""
    if not Path(MODEL_SAVE_PATH).exists():
        train.entrainer()
