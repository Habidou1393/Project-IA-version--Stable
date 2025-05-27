import json
import os
from threading import Lock
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import wikipedia
from functools import lru_cache

data_file = "MémoireDuChatbot.json"
taille_max_de_la_memoire = 100
WIKI_TRIGGER = "recherche sur wikipedia "

lock = Lock()

if os.path.exists(data_file):
    with open(data_file, "r", encoding="utf-8") as f:
        memoire_cache = json.load(f)
else:
    memoire_cache = []

def save_memory():
    with lock:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(memoire_cache, f, ensure_ascii=False, indent=2)

def clean_memory():
    global memoire_cache
    if len(memoire_cache) > taille_max_de_la_memoire:
        memoire_cache = memoire_cache[-taille_max_de_la_memoire:]

@lru_cache(maxsize=128)
def get_wikipedia_summary(requete):
    try:
        wikipedia.set_lang("fr")
        return wikipedia.summary(requete, sentences=2)
    except Exception:
        return None

def obtenir_la_response(message):
    global memoire_cache
    
    if message.lower().startswith(WIKI_TRIGGER):
        requete = message[len(WIKI_TRIGGER):].strip()
        if not requete:
            return "Tu dois préciser ce que tu veux chercher sur Wikipédia."
        resume_text_wiki = get_wikipedia_summary(requete)
        if resume_text_wiki:
            return f"Voici un résumé de Wikipédia pour ta requête :\n{resume_text_wiki}"
        else:
            return "Je n'ai pas trouvé d'information sur Wikipédia pour cette requête."

    if not memoire_cache:
        memoire_cache.append({"question": message, "response": "Je vais m'en souvenir."})
        save_memory()
        return f"Je n’ai encore rien appris, mais je retiens : \"{message}\""

    questions = [item["question"] for item in memoire_cache] + [message]
    vectorizer = TfidfVectorizer()
    vecteurs = vectorizer.fit_transform(questions)

    similarites = cosine_similarity(vecteurs[-1], vecteurs[:-1])
    best_index = similarites.argmax()
    score = similarites[0, best_index]

    if score > 0.6:
        return memoire_cache[best_index]["response"]
    else:
        response = "Je ne connais pas cette phrase, mais je vais l'apprendre."
        memoire_cache.append({"question": message, "response": response})
        clean_memory()
        save_memory()
        return response
