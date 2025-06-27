import os  # Pour vérifier l'existence de fichiers et manipuler le système de fichiers
import json  # Pour lire et écrire des données au format JSON
import tempfile  # Pour créer des fichiers temporaires de façon sûre
from threading import Lock  # Pour gérer la concurrence lors des accès en écriture
from app.config import DATA_FILE, TAILLE_MAX  # Import des constantes de configuration

lock = Lock()  # Création d'un verrou pour sécuriser l'accès concurrent à la mémoire
memoire_cache = []  # Liste globale en mémoire qui stocke les données du chatbot

def load_memory():
    global memoire_cache  # On indique que l'on va modifier la variable globale
    if not os.path.isfile(DATA_FILE):  # Si le fichier de mémoire n'existe pas
        return  # On quitte la fonction sans rien faire

    try:
        # Ouverture en lecture du fichier JSON contenant la mémoire du chatbot
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)  # Chargement des données JSON dans 'data'
            # Vérifie que data est une liste et que chaque élément a bien les clés "question" et "response"
            if isinstance(data, list) and all("question" in d and "response" in d for d in data):
                # On conserve uniquement les derniers éléments jusqu'à TAILLE_MAX
                memoire_cache[:] = data[-TAILLE_MAX:]
            else:
                # Si le format n'est pas valide, on vide la mémoire
                # print("Format de mémoire invalide, réinitialisation.")
                memoire_cache.clear()
    except (json.JSONDecodeError, OSError) as e:
        # En cas d'erreur lors du chargement JSON ou d'erreur système, on vide la mémoire
        # print(f"Erreur lors du chargement de la mémoire : {e}")
        memoire_cache.clear()

def save_memory():
    with lock:  # Bloc protégé par un verrou pour éviter l'écriture simultanée par plusieurs threads
        try:
            # On écrit dans un fichier temporaire pour éviter la corruption du fichier principal
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
                # On écrit la mémoire (limitée à TAILLE_MAX derniers éléments) dans ce fichier temporaire
                json.dump(memoire_cache[-TAILLE_MAX:], tmp, ensure_ascii=False, indent=2)
                temp_name = tmp.name  # On récupère le nom du fichier temporaire
            os.replace(temp_name, DATA_FILE)  # On remplace le fichier principal par le fichier temporaire
        except OSError as e:
            # En cas d'erreur lors de l'écriture, on peut ignorer ou logguer (ici pass)
            # print(f"Erreur lors de la sauvegarde de la mémoire : {e}")
            pass

load_memory()  # Chargement automatique de la mémoire au démarrage du module
