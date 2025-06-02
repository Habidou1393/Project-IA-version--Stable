import random  # Pour les réactions aléatoires
import torch  # Torch, probablement utilisé dans le modèle (importé mais pas utilisé directement ici)
from sentence_transformers import util  # Pour calculer la similarité cosinus entre vecteurs
from utils.wikipedia_search import get_wikipedia_summary  # Recherche et résumé Wikipedia
from utils.google_search import recherche_google  # Recherche Google via API
from utils.neural_net import model  # Modèle d'encodage de phrases
from app.config import WIKI_TRIGGER, TAILLE_MAX  # Constantes de configuration
from .neogpt import NeoGPT  # Classe NeoGPT pour génération de texte

# Initialisation d'une instance NeoGPT avec personnalité "assistant"
neo_gpt = NeoGPT(personality="assistant")

# Variable globale pour stocker les embeddings des questions en mémoire
corpus_embeddings = None

def update_corpus_embeddings():
    from app.memory import memoire_cache, lock  # Import local pour éviter import circulaire
    global corpus_embeddings
    with lock:  # Sécurise l'accès concurrent aux données partagées
        questions = [item["question"] for item in memoire_cache]  # Extraction des questions en mémoire
        # Encode les questions en vecteurs si la mémoire n'est pas vide, sinon None
        corpus_embeddings = model.encode(questions, convert_to_tensor=True) if questions else None

# Mise à jour initiale des embeddings à partir de la mémoire existante
update_corpus_embeddings()

def ton_humain_reponse(texte: str) -> str:
    # Prépare une réponse avec un préfixe humain sympathique aléatoire
    réactions = (
        ["😊", "👍", "Ça me fait plaisir de t'aider !", "Super question !", "Tu es brillant(e) !"],
        ["Hmm...", "Intéressant...", "Voyons voir...", "C'est une bonne question.", "Je réfléchis..."],
        ["Je ne suis pas une boule de cristal, mais je crois que c'est ça ! 😂",
         "Si j'avais un euro à chaque fois qu'on me pose cette question... 💸",
         "Je suis un bot, mais je commence à comprendre les humains ! 🤖",
         "Je suis pas parfait, mais j'essaie ! 😅"]
    )
    r = random.random()  # Tirage aléatoire
    # Choisit le groupe de réactions selon la probabilité
    prefix = random.choice(
        réactions[0] if r < 0.15 else réactions[2] if r < 0.2 else réactions[1]
    )
    return f"{prefix} {texte}"  # Concatène le préfixe avec la réponse donnée

def detect_salutation(message: str) -> str | None:
    # Détecte si le message est une salutation ou une question sur l'état et répond
    msg = message.lower()
    if any(greet in msg for greet in ["bonjour", "salut", "coucou", "hello", "hey"]):
        return random.choice([
            "Bonjour ! Comment puis-je t'aider aujourd'hui ?",
            "Salut ! Ravi de te voir.",
            "Coucou ! Que puis-je faire pour toi ?"
        ])
    if any(x in msg for x in ["comment vas-tu", "comment ça va", "ça va", "tu vas bien"]):
        return random.choice([
            "Je vais très bien, merci ! Et toi ?",
            "Tout roule ici, prêt à t'aider !",
            "Super bien, merci de demander !"
        ])
    return None  # Pas de salutation détectée

def ajouter_a_memoire(question: str, reponse: str):
    from app.memory import memoire_cache, lock, save_memory  # Import local pour éviter import circulaire
    with lock:  # Protection accès mémoire partagée
        memoire_cache.append({"question": question, "response": reponse})  # Ajout à la mémoire
        if len(memoire_cache) > TAILLE_MAX:  # Si dépasse taille max, supprime la plus ancienne
            memoire_cache.pop(0)
        save_memory()  # Sauvegarde persistante de la mémoire
        update_corpus_embeddings()  # Met à jour les embeddings pour la recherche rapide

def obtenir_la_response(message: str) -> str:
    from app.memory import memoire_cache, lock  # Import local mémoire et verrou

    msg = message.strip()  # Nettoyage du message
    if not msg:
        return "Je n'ai pas bien saisi ta question, pourrais-tu reformuler s'il te plaît ?"

    if (resp := detect_salutation(msg)):  # Vérifie si c'est une salutation
        return resp

    if msg.lower().startswith(WIKI_TRIGGER):  # Détecte la commande de recherche Wikipedia
        query = msg[len(WIKI_TRIGGER):].strip()
        if not query:
            return "Tu dois me dire ce que tu veux que je cherche sur Wikipédia."
        try:
            if (res := get_wikipedia_summary(query)):  # Recherche résumé Wikipedia
                return ton_humain_reponse(f"Voici ce que j'ai trouvé sur Wikipédia :\n{res}")
            return ton_humain_reponse("Désolé, rien trouvé de pertinent sur Wikipédia.")
        except Exception as e:
            return ton_humain_reponse(f"Erreur lors de la recherche Wikipédia : {e}")

    try:
        embedding = model.encode(msg, convert_to_tensor=True)  # Encode la question en vecteur
    except Exception as e:
        return ton_humain_reponse(f"Erreur lors de l'encodage de la question : {e}")

    global corpus_embeddings
    with lock:
        if not memoire_cache:  # Si la mémoire est vide, on ajoute et répond
            ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")
            return ton_humain_reponse(f"C'est la première fois que tu me poses ça, je retiens : « {msg} »")

        if corpus_embeddings is not None:
            try:
                scores = util.cos_sim(embedding, corpus_embeddings)[0]  # Calcul similarité cosinus
                idx = int(scores.argmax())  # Index de la meilleure correspondance
                max_score = float(scores[idx])

                # Seuil variable selon taille de mémoire pour accepter correspondance
                seuil = 0.55 if len(memoire_cache) < 10 else 0.60 if len(memoire_cache) < 50 else 0.65
                if max_score >= seuil:
                    # Retourne la réponse associée à la question la plus proche
                    return ton_humain_reponse(f"Je pense que ceci répond à ta question :\n{memoire_cache[idx]['response']}")
            except Exception as e:
                return ton_humain_reponse(f"Erreur lors de la recherche dans la mémoire : {e}")

    try:
        res = neo_gpt.chat(msg, max_length=100)  # Génère une réponse via NeoGPT
        ajouter_a_memoire(msg, res)  # Ajoute la nouvelle question/réponse en mémoire
        return ton_humain_reponse(res)
    except Exception as e:
        try:
            if (res := recherche_google(msg)):  # En cas d'échec, tente recherche Google
                ajouter_a_memoire(msg, res)
                return ton_humain_reponse(f"Voici ce que j'ai trouvé via Google :\n{res}")
        except Exception as e2:
            return ton_humain_reponse(f"Erreur lors de la recherche Google : {e2}")
        # En dernier recours, renvoie une erreur interne
        return ton_humain_reponse(f"Erreur interne lors de la génération de réponse : {e}")

    # Si tout échoue, répond avec un message générique et ajoute en mémoire
    ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")
    return ton_humain_reponse("Je ne connais pas encore la réponse, mais je l'apprendrai pour toi !")
