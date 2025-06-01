import os
import json
import tempfile
from threading import Lock
from app.config import DATA_FILE, TAILLE_MAX

lock = Lock()
memoire_cache = []

def load_memory():
    global memoire_cache
    if not os.path.isfile(DATA_FILE):
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and all("question" in d and "response" in d for d in data):
                memoire_cache[:] = data[-TAILLE_MAX:]
            else:
                # print("Format de mémoire invalide, réinitialisation.")
                memoire_cache.clear()
    except (json.JSONDecodeError, OSError) as e:
        # print(f"Erreur lors du chargement de la mémoire : {e}")
        memoire_cache.clear()

def save_memory():
    with lock:
        try:
            # Écriture dans un fichier temporaire pour éviter corruption
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
                json.dump(memoire_cache[-TAILLE_MAX:], tmp, ensure_ascii=False, indent=2)
                temp_name = tmp.name
            os.replace(temp_name, DATA_FILE)
        except OSError as e:
            # print(f"Erreur lors de la sauvegarde de la mémoire : {e}")
            pass

load_memory()
