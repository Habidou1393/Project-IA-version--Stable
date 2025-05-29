import random
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
        corpus_embeddings = model.encode(
            [item["question"] for item in memoire_cache], convert_to_tensor=True
        ) if memoire_cache else None

update_corpus_embeddings()

def ton_humain_reponse(texte):
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
    prefix = random.choice(réactions[0] if r < 0.15 else réactions[2] if r < 0.2 else réactions[1])
    return f"{prefix} {texte}"

def detect_salutation(message):
    msg = message.lower()
    if any(x in msg for x in ["bonjour", "salut", "coucou", "hello", "hey"]):
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

def ajouter_a_memoire(question, reponse):
    from app.memory import memoire_cache, lock, save_memory
    with lock:
        memoire_cache.append({"question": question, "response": reponse})
        if len(memoire_cache) > TAILLE_MAX:
            memoire_cache.pop(0)
        save_memory()
        update_corpus_embeddings()

def obtenir_la_response(message):
    from app.memory import memoire_cache, lock
    msg = message.strip()
    if not msg:
        return "Je n'ai pas bien saisi ta question, pourrais-tu reformuler s'il te plaît ?"

    if (resp := detect_salutation(msg)):
        return resp

    if msg.lower().startswith(WIKI_TRIGGER):
        query = msg[len(WIKI_TRIGGER):].strip()
        if not query:
            return "Hmm, tu dois me dire ce que tu veux que je cherche sur Wikipédia."
        try:
            if (res := get_wikipedia_summary(query)):
                return ton_humain_reponse(f"Voilà ce que j'ai trouvé sur Wikipédia pour ta recherche :\n{res}")
            return ton_humain_reponse("Désolé, je n'ai rien trouvé de pertinent sur Wikipédia.")
        except Exception as e:
            return ton_humain_reponse(f"Une erreur est survenue lors de la recherche sur Wikipédia : {e}")

    with lock:
        if not memoire_cache:
            ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")
            return ton_humain_reponse(f"C'est la première fois que tu me poses ça, je retiens : « {msg} »")

    try:
        embedding = model.encode(msg, convert_to_tensor=True)
    except Exception as e:
        return ton_humain_reponse(f"Une erreur est survenue lors de l'encodage de ta question : {e}")

    global corpus_embeddings
    if corpus_embeddings is not None:
        try:
            scores = util.cos_sim(embedding, corpus_embeddings)[0]
            idx = int(scores.argmax())
            if float(scores[idx]) > 0.6:
                with lock:
                    return ton_humain_reponse(f"Je pense que ceci répond à ta question :\n{memoire_cache[idx]['response']}")
        except Exception as e:
            return ton_humain_reponse(f"Erreur de recherche de similarités : {e}")

    if (res := recherche_google(msg)):
        ajouter_a_memoire(msg, res)
        return ton_humain_reponse(f"Voici ce que j'ai trouvé via Google :\n{res}")

    ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")
    return ton_humain_reponse("Je ne connais pas encore la réponse, mais je l'apprendrai pour toi !")
