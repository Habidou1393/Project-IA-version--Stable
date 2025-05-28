import os, json
from threading import Lock
from app.config import DATA_FILE, TAILLE_MAX

lock = Lock()
memoire_cache = []

def load_memory():
    global memoire_cache
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                memoire_cache = json.load(f)
        except json.JSONDecodeError:
            memoire_cache = []
    else:
        memoire_cache = []

def save_memory():
    with lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(memoire_cache[-TAILLE_MAX:], f, ensure_ascii=False, indent=2)

load_memory()
