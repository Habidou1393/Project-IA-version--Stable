import os  # Pour vérifier l'existence de fichiers et manipuler le système de fichiers
import json  # Pour lire et écrire des données au format JSON
import tempfile  # Pour créer des fichiers temporaires de façon sûre
from threading import Lock  # Pour gérer la concurrence lors des accès en écriture

lock = Lock()  # Création d'un verrou pour sécuriser l'accès concurrent à la mémoire
memoire_cache = []  # Liste globale en mémoire qui stocke les données du chatbot

def save_memory(data_file, taille_max):
    with lock:  # Bloc protégé par un verrou pour éviter l'écriture simultanée par plusieurs threads
        try:
            # On écrit dans un fichier temporaire pour éviter la corruption du fichier principal
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
                json.dump(memoire_cache[-taille_max:], tmp, ensure_ascii=False, indent=2)
                temp_name = tmp.name
            os.replace(temp_name, data_file)  # Remplacement du fichier principal
        except OSError:
            pass
