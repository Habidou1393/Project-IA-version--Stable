from flask import Flask, render_template, request, jsonify
import json
import os
from threading import Lock
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import wikipedia
from functools import lru_cache

app = Flask(__name__)

DATA_FILE = "MémoireDuChatbot.json"
MAX_MEMORY_SIZE = 100
WIKI_TRIGGER = "cherche sur wikipedia "

lock = Lock()

# Charge la mémoire en RAM au démarrage (et la garde en cache)
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        memory_cache = json.load(f)
else:
    memory_cache = []

def save_memory():
    with lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(memory_cache, f, ensure_ascii=False, indent=2)

def clean_memory():
    global memory_cache
    if len(memory_cache) > MAX_MEMORY_SIZE:
        memory_cache = memory_cache[-MAX_MEMORY_SIZE:]

@lru_cache(maxsize=128)
def get_wikipedia_summary(query):
    try:
        wikipedia.set_lang("fr")
        return wikipedia.summary(query, sentences=2)
    except Exception:
        return None

def get_response(message):
    global memory_cache

    # Si la requête commence par le trigger Wikipedia, on cherche sur Wikipédia uniquement
    if message.lower().startswith(WIKI_TRIGGER):
        query = message[len(WIKI_TRIGGER):].strip()
        if not query:
            return "Tu dois préciser ce que tu veux chercher sur Wikipédia."
        wiki_summary = get_wikipedia_summary(query)
        if wiki_summary:
            return f"(Depuis Wikipédia)\n{wiki_summary}"
        else:
            return "Je n'ai pas trouvé d'information sur Wikipédia pour cette requête."

    # Sinon, réponse normale basée sur la mémoire
    if not memory_cache:
        memory_cache.append({"question": message, "response": "Je vais m'en souvenir."})
        save_memory()
        return f"Je n’ai encore rien appris, mais je retiens : \"{message}\""

    questions = [item["question"] for item in memory_cache] + [message]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(questions)

    similarities = cosine_similarity(vectors[-1], vectors[:-1])
    best_index = similarities.argmax()
    score = similarities[0, best_index]

    if score > 0.6:
        return memory_cache[best_index]["response"]
    else:
        response = "Je ne connais pas cette phrase, mais je vais l'apprendre."
        memory_cache.append({"question": message, "response": response})
        clean_memory()
        save_memory()
        return response

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"response": "Veuillez écrire quelque chose."})
    response = get_response(message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
