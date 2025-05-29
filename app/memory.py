import os
import json
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
            memoire_cache[:] = json.load(f)
    except (json.JSONDecodeError, OSError):
        memoire_cache.clear()

def save_memory():
    with lock:
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(memoire_cache[-TAILLE_MAX:], f, ensure_ascii=False, indent=2)
        except OSError:
            pass  # Optionnel : logguer l’erreur si nécessaire

load_memory()
