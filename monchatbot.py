import json
import os
from threading import Lock
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import wikipedia
from functools import lru_cache
import requests

# 📁 Configuration
data_file = "MémoireDuChatbot.json"
taille_max_de_la_memoire = 100
WIKI_TRIGGER = "recherche sur wikipedia "

# 🔐 Verrou pour accès fichiers
lock = Lock()

# 📂 Chargement initial de la mémoire
if os.path.exists(data_file):
    with open(data_file, "r", encoding="utf-8") as f:
        memoire_cache = json.load(f)
else:
    memoire_cache = []

# 🔍 Recherche Google avec API CSE
def rechercher_sur_google(question):
    api_key = "AIzaSyCq-UUQBkDw1BpdEtlA0RHYtAZQ9mXq2O0"
    cx = "6098340421bc7410b"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": question,
        "hl": "fr"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print("Erreur Google API:", response.status_code, response.text)
            return None

        resultats = response.json()

        if "error" in resultats:
            print("Erreur de l’API Google :", resultats["error"])
            return None

        reponses = []
        if "items" in resultats:
            for resultat in resultats["items"][:5]:
                titre = resultat.get("title", "")
                lien = resultat.get("link", "")
                snippet = resultat.get("snippet", "")
                reponses.append(f"{titre}\n{snippet}\n{lien}\n")

        return "\n---\n".join(reponses) if reponses else None

    except Exception as e:
        print("Exception lors de la recherche Google:", str(e))
        return None

# 💾 Sauvegarde de la mémoire
def save_memory():
    with lock:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(memoire_cache, f, ensure_ascii=False, indent=2)

# ♻️ Nettoyage si trop de données
def clean_memory():
    global memoire_cache
    if len(memoire_cache) > taille_max_de_la_memoire:
        memoire_cache = memoire_cache[-taille_max_de_la_memoire:]

# 📝 Résumé Wikipédia avec cache
@lru_cache(maxsize=128)
def get_wikipedia_summary(requete):
    try:
        wikipedia.set_lang("fr")
        return wikipedia.summary(requete, sentences=2)
    except Exception:
        return None

# 🤖 Fonction principale
def obtenir_la_response(message):
    global memoire_cache

    # Commande spéciale Wikipédia
    if message.lower().startswith(WIKI_TRIGGER):
        requete = message[len(WIKI_TRIGGER):].strip()
        if not requete:
            return "Tu dois préciser ce que tu veux chercher sur Wikipédia."
        resume_text_wiki = get_wikipedia_summary(requete)
        if resume_text_wiki:
            return f"Voici un résumé de Wikipédia pour ta requête :\n{resume_text_wiki}"
        else:
            return "Je n'ai pas trouvé d'information sur Wikipédia pour cette requête."

    # Si aucune mémoire enregistrée
    if not memoire_cache:
        memoire_cache.append({"question": message, "response": "Je vais m'en souvenir."})
        save_memory()
        return f"Je n’ai encore rien appris, mais je retiens : \"{message}\""

    # Vérification par similarité
    questions = [item["question"] for item in memoire_cache] + [message]
    vectorizer = TfidfVectorizer()
    vecteurs = vectorizer.fit_transform(questions)

    similarites = cosine_similarity(vecteurs[-1], vecteurs[:-1])
    best_index = similarites.argmax()
    score = similarites[0, best_index]

    if score > 0.6:
        return memoire_cache[best_index]["response"]
    else:
        # 🔍 Étape 1 : Recherche Google
        google_result = rechercher_sur_google(message)
        if google_result:
            memoire_cache.append({"question": message, "response": google_result})
            clean_memory()
            save_memory()
            return f"(Depuis Google)\n{google_result}"

        # 📚 Étape 2 : Recherche Wikipédia
        resume_text_wiki = get_wikipedia_summary(message)
        if resume_text_wiki:
            memoire_cache.append({"question": message, "response": resume_text_wiki})
            clean_memory()
            save_memory()
            return f"(Depuis Wikipédia)\n{resume_text_wiki}"

        # 🧠 Étape 3 : Apprentissage
        response = "Je ne connais pas cette phrase, mais je vais l'apprendre."
        memoire_cache.append({"question": message, "response": response})
        clean_memory()
        save_memory()
        return response