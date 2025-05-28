import sys
import os
from flask import Flask, render_template, request, jsonify

# Chemin racine du projet (le dossier qui contient app/, static/, templates/, etc)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ajoute ce chemin au PYTHONPATH pour les imports relatifs
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

app = Flask(
    __name__,
    template_folder=os.path.join(ROOT_DIR, 'templates'),
    static_folder=os.path.join(ROOT_DIR, 'static')  # Ajout du dossier static explicitement
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    # Import ici pour éviter les imports circulaires
    from utils.monchatbot import obtenir_la_response

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"response": "Requête invalide."}), 400
    
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"response": "Veuillez écrire quelque chose."}), 400
    
    response = obtenir_la_response(message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=False)
