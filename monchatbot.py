import os
import json
import requests
import wikipedia
from threading import Lock
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 🔧 Configuration
DATA_FILE = "MémoireDuChatbot.json"
TAILLE_MAX = 100
WIKI_TRIGGER = "recherche sur wikipedia "
GOOGLE_API_KEY = "AIzaSyCq-UUQBkDw1BpdEtlA0RHYtAZQ9mXq2O0"
GOOGLE_CX = "6098340421bc7410b"

# 🔐 Sécurité des accès concurrents
lock = Lock()

# 📂 Chargement initial
with lock:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            memoire_cache = json.load(f)
    else:
        memoire_cache = []

# 💾 Sauvegarde mémoire
def save_memory():
    with lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(memoire_cache[-TAILLE_MAX:], f, ensure_ascii=False, indent=2)

# 🌐 Résumé Wikipédia (avec cache)
@lru_cache(maxsize=128)
def get_wikipedia_summary(query):
    wikipedia.set_lang("fr")
    try:
        return wikipedia.summary(query, sentences=2)
    except:
        return None

# 🔎 Recherche Google via API
def recherche_google(query):
    try:
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params={
            "key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": query, "hl": "fr"
        })
        data = resp.json()
        items = data.get("items", [])
        return "\n---\n".join(f"{i.get('title')}\n{i.get('snippet')}\n{i.get('link')}" for i in items[:5]) if items else None
    except:
        return None

# 🤖 Traitement du message
def obtenir_la_response(message):
    message = message.strip()

    if message.lower().startswith(WIKI_TRIGGER):
        query = message[len(WIKI_TRIGGER):].strip()
        if not query:
            return "Tu dois préciser ce que tu veux chercher sur Wikipédia."
        resume = get_wikipedia_summary(query)
        return f"Voici un résumé de Wikipédia pour ta requête :\n{resume}" if resume else "Aucune info trouvée sur Wikipédia."

    if not memoire_cache:
        memoire_cache.append({"question": message, "response": "Je vais m'en souvenir."})
        save_memory()
        return f"Je n’ai encore rien appris, mais je retiens : \"{message}\""

    # Calcul de similarité
    corpus = [item["question"] for item in memoire_cache] + [message]
    vecteurs = TfidfVectorizer().fit_transform(corpus)
    score = cosine_similarity(vecteurs[-1], vecteurs[:-1])[0]
    best_match_index = score.argmax()
    best_score = score[best_match_index]

    if best_score > 0.6:
        return memoire_cache[best_match_index]["response"]

    # Recherche Google
    resultat_google = recherche_google(message)
    if resultat_google:
        memoire_cache.append({"question": message, "response": resultat_google})
        save_memory()
        return f"(Depuis Google)\n{resultat_google}"

    # Résumé Wikipédia
    resume = get_wikipedia_summary(message)
    if resume:
        memoire_cache.append({"question": message, "response": resume})
        save_memory()
        return f"(Depuis Wikipédia)\n{resume}"

    # Apprentissage brut
    reponse = "Je ne connais pas cette phrase, mais je vais l'apprendre."
    memoire_cache.append({"question": message, "response": reponse})
    save_memory()
    return reponse
