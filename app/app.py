import os
import sys
import logging
from flask import Flask, request, jsonify, render_template

# Définir le dossier racine
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 🛠️ S'assurer que le chemin est dans sys.path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Initialisation de Flask avec les bons chemins
app = Flask(
    __name__,
    template_folder=os.path.join(ROOT_DIR, 'templates'),
    static_folder=os.path.join(ROOT_DIR, 'static')
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Route principale
@app.route("/")
def index():
    return render_template("index.html")

# Endpoint pour envoyer une requête
@app.route("/ask", methods=["POST"])
def ask():
    from utils.monchatbot import obtenir_la_response  # Import différé

    try:
        data = request.get_json(force=True, silent=False)
    except Exception as e:
        app.logger.warning(f"Requête JSON invalide : {e}")
        return jsonify(response="Format JSON invalide."), 400

    message = (data.get("message") or "").strip()
    if not message:
        return jsonify(response="Veuillez écrire quelque chose."), 400

    try:
        response_text = obtenir_la_response(message)
    except Exception as e:
        app.logger.error(f"Erreur lors du traitement de la requête: {e}", exc_info=True)
        return jsonify(response="Erreur interne lors du traitement."), 500

    app.logger.info(f"Question reçue: {message[:50]}... Réponse fournie.")
    return jsonify(response=response_text)

# Vérification de l'état de santé du serveur
@app.route("/health")
def health():
    return jsonify(status="ok")

# Lancer le serveur
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(debug=debug_mode, host=host, port=port)