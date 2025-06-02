import os  # Module pour manipuler les chemins, variables d'environnement, etc.
import sys  # Module pour interagir avec l’interpréteur Python et les chemins d’importation
import logging  # Module pour configurer et utiliser la journalisation (logs)
from flask import Flask, request, jsonify, render_template, abort  # Import des composants Flask nécessaires

# Configuration du chemin racine du projet
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  
# __file__ est le chemin du fichier actuel, on remonte d’un niveau (..) et on prend le chemin absolu
# Cela fixe la racine du projet, utile pour accéder aux dossiers templates et static

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)  
# On ajoute ROOT_DIR au début de la liste sys.path pour que Python trouve les modules du projet lors des imports

# Initialisation de Flask avec chemins explicites
app = Flask(
    __name__,  # Nom du module actuel, sert à Flask pour gérer les ressources
    template_folder=os.path.join(ROOT_DIR, 'templates'),  # Chemin absolu vers le dossier des templates HTML
    static_folder=os.path.join(ROOT_DIR, 'static')  # Chemin absolu vers le dossier des fichiers statiques (CSS, JS, images)
)

# Configuration du logging (journalisation)
logging.basicConfig(
    level=logging.INFO,  # Niveau minimal des logs affichés (INFO et plus graves)
    format='%(asctime)s [%(levelname)s] %(message)s'  # Format des messages de log avec timestamp et niveau
)

# Optionnel : CORS basique (cross-origin resource sharing)
# from flask_cors import CORS
# CORS(app, resources={r"/ask": {"origins": "*"}})  
# Ces lignes sont commentées, elles permettraient d’autoriser des requêtes venant d’autres domaines

@app.route("/")  # Route pour la page d’accueil "/"
def index():
    return render_template("index.html")  
    # Renvoie la page HTML index.html qui se trouve dans templates/

@app.route("/ask", methods=["POST"])  # Route pour recevoir les questions en POST à "/ask"
def ask():
    from utils.monchatbot import obtenir_la_response  # Import différé (dans la fonction) pour éviter boucle d’import

    try:
        data = request.get_json(force=True, silent=False)  
        # On tente de récupérer le JSON envoyé dans la requête
    except Exception as e:
        app.logger.warning(f"Requête JSON invalide : {e}")  # Log en warning si JSON invalide
        return jsonify(response="Format JSON invalide."), 400  # Réponse erreur 400 (mauvaise requête)

    message = (data.get("message") or "").strip()  
    # On récupère la valeur "message" dans le JSON, on met chaîne vide si absent, puis on enlève les espaces

    if not message:
        return jsonify(response="Veuillez écrire quelque chose."), 400  # Erreur si message vide

    try:
        response_text = obtenir_la_response(message)  
        # On appelle la fonction qui génère la réponse à la question
    except Exception as e:
        app.logger.error(f"Erreur lors du traitement de la requête: {e}", exc_info=True)  
        # Log erreur avec trace complète si exception
        return jsonify(response="Erreur interne lors du traitement."), 500  # Erreur serveur 500

    app.logger.info(f"Question reçue: {message[:50]}... Réponse fournie.")  
    # Log d’info indiquant que la question a bien été reçue (limité à 50 caractères)

    return jsonify(response=response_text)  # Renvoie la réponse au format JSON

@app.route("/health")  # Route pour vérifier que le serveur fonctionne
def health():
    return jsonify(status="ok")  # Renvoie un simple JSON confirmant que le service est actif

if __name__ == "__main__":  # Si on lance ce fichier directement (pas en import)
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"  
    # Lecture variable d’environnement FLASK_DEBUG pour activer/désactiver le mode debug

    host = os.getenv("FLASK_HOST", "0.0.0.0")  
    # Adresse IP à laquelle Flask écoute (0.0.0.0 = toutes interfaces réseau)

    port = int(os.getenv("FLASK_PORT", "5000"))  
    # Port d’écoute par défaut 5000, converti en entier

    app.run(debug=debug_mode, host=host, port=port)  
    # Démarre le serveur Flask avec la configuration définie (debug, host, port)
