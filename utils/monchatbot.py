import random
import torch
from sentence_transformers import util
from utils.wikipedia_search import get_wikipedia_summary
from utils.google_search import recherche_google
from utils.neural_net import model
from app.config import WIKI_TRIGGER, TAILLE_MAX

corpus_embeddings = None

def update_corpus_embeddings():
    from app.memory import memoire_cache, lock
    global corpus_embeddings
    with lock:
        questions = [item["question"] for item in memoire_cache]
        corpus_embeddings = model.encode(questions, convert_to_tensor=True) if questions else None

update_corpus_embeddings()

def ton_humain_reponse(texte: str) -> str:
    réactions = (
        ["😊", "👍", "Ça me fait plaisir de t'aider !", "Super question !", "Tu es brillant(e) !"],
        ["Hmm...", "Intéressant...", "Voyons voir...", "C'est une bonne question.", "Je réfléchis..."],
        [
            "Je ne suis pas une boule de cristal, mais là je crois que c'est ça ! 😂",
            "Si j'avais un euro à chaque fois qu'on me pose cette question... 💸",
            "Je suis un bot, mais je commence à comprendre les humains ! 🤖",
            "Je suis pas parfait, mais j'essaie ! 😅"
        ]
    )
    r = random.random()
    prefix = random.choice(
        réactions[0] if r < 0.15 else réactions[2] if r < 0.2 else réactions[1]
    )
    return f"{prefix} {texte}"

def detect_salutation(message: str) -> str | None:
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
    return None

def ajouter_a_memoire(question: str, reponse: str):
    from app.memory import memoire_cache, lock, save_memory
    with lock:
        memoire_cache.append({"question": question, "response": reponse})
        if len(memoire_cache) > TAILLE_MAX:
            memoire_cache.pop(0)
        save_memory()
        update_corpus_embeddings()

def obtenir_la_response(message: str) -> str:
    from app.memory import memoire_cache, lock

    msg = message.strip()
    if not msg:
        return "Je n'ai pas bien saisi ta question, pourrais-tu reformuler s'il te plaît ?"

    if (resp := detect_salutation(msg)):
        return resp

    # Requête Wikipédia
    if msg.lower().startswith(WIKI_TRIGGER):
        query = msg[len(WIKI_TRIGGER):].strip()
        if not query:
            return "Tu dois me dire ce que tu veux que je cherche sur Wikipédia."
        try:
            if (res := get_wikipedia_summary(query)):
                return ton_humain_reponse(f"Voici ce que j'ai trouvé sur Wikipédia :\n{res}")
            return ton_humain_reponse("Désolé, rien trouvé de pertinent sur Wikipédia.")
        except Exception as e:
            return ton_humain_reponse(f"Erreur lors de la recherche Wikipédia : {e}")

    try:
        embedding = model.encode(msg, convert_to_tensor=True)
    except Exception as e:
        return ton_humain_reponse(f"Erreur lors de l'encodage de la question : {e}")

    global corpus_embeddings
    with lock:
        if not memoire_cache:
            ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")
            return ton_humain_reponse(f"C'est la première fois que tu me poses ça, je retiens : « {msg} »")

        if corpus_embeddings is not None:
            try:
                scores = util.cos_sim(embedding, corpus_embeddings)[0]
                idx = int(scores.argmax())
                max_score = float(scores[idx])

                seuil = 0.55 if len(memoire_cache) < 10 else 0.60 if len(memoire_cache) < 50 else 0.65
                if max_score >= seuil:
                    return ton_humain_reponse(f"Je pense que ceci répond à ta question :\n{memoire_cache[idx]['response']}")
            except Exception as e:
                return ton_humain_reponse(f"Erreur lors de la recherche dans la mémoire : {e}")

    # Recherche Google si mémoire insuffisante
    try:
        if (res := recherche_google(msg)):
            ajouter_a_memoire(msg, res)
            return ton_humain_reponse(f"Voici ce que j'ai trouvé via Google :\n{res}")
    except Exception as e:
        return ton_humain_reponse(f"Erreur lors de la recherche Google : {e}")

    ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")
    return ton_humain_reponse("Je ne connais pas encore la réponse, mais je l'apprendrai pour toi !")
