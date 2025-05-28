from flask import Flask, render_template, request, jsonify
from utils.monchatbot import obtenir_la_response


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"response": "Veuillez écrire quelque chose."})
    response = obtenir_la_response(message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
