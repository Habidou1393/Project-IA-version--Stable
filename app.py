from flask import Flask, render_template, request, jsonify
import json, os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import wikipedia

app = Flask(__name__)

DATA_FILE = "chat_memory.json"

# Charger les phrases apprises
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Sauvegarder de nouvelles phrases
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Essayer de répondre à partir de la mémoire
def get_response(message):
    memory = load_data()

    if not memory:
        memory.append({"question": message, "response": "Je vais m'en souvenir."})
        save_data(memory)
        return "Je n’ai encore rien appris, mais je retiens : \"" + message + "\""

    questions = [item["question"] for item in memory] + [message]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(questions)

    similarities = cosine_similarity(vectors[-1], vectors[:-1])
    best_index = similarities.argmax()
    score = similarities[0, best_index]

    if score > 0.6:
        return memory[best_index]["response"]
    else:
        try:
            wikipedia.set_lang("fr")
            wiki_summary = wikipedia.summary(message, sentences=2)
            memory.append({"question": message, "response": wiki_summary})
            save_data(memory)
            return f"(Depuis Wikipédia)\n{wiki_summary}"
        except:
            memory.append({"question": message, "response": "Je vais m'en souvenir."})
            save_data(memory)
            return "Je ne connais pas cette phrase, mais je vais l'apprends."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    message = data.get("message", "")
    response = get_response(message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
