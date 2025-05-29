import os
import sys
from flask import Flask, request, jsonify, render_template

# Configuration du chemin racine du projet
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Initialisation de Flask avec chemins explicites
app = Flask(
    __name__,
    template_folder=os.path.join(ROOT_DIR, 'templates'),
    static_folder=os.path.join(ROOT_DIR, 'static')
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    from utils.monchatbot import obtenir_la_response  # Import différé pour éviter les boucles
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify(response="Veuillez écrire quelque chose."), 400

    return jsonify(response=obtenir_la_response(message))

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
