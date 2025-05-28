import random
from utils.wikipedia_search import get_wikipedia_summary
from utils.google_search import recherche_google
from utils.neural_net import model, train_nn_on_memory, nn_model
from sentence_transformers import util
from app.config import WIKI_TRIGGER, TAILLE_MAX

corpus_embeddings = None

def update_corpus_embeddings():
    from app.memory import memoire_cache, lock
    global corpus_embeddings
    with lock:
        questions = [item["question"] for item in memoire_cache]
    if questions:
        corpus_embeddings = model.encode(questions, convert_to_tensor=True)
    else:
        corpus_embeddings = None

update_corpus_embeddings()

def ton_humain_reponse(base_reponse):
    positives = ["😊", "👍", "Ça me fait plaisir de t'aider !", "Super question !", "Tu es brillant(e) !"]
    neutres = ["Hmm...", "Intéressant...", "Voyons voir...", "C'est une bonne question.", "Je réfléchis..."]
    humoristiques = [
        "Je ne suis pas une boule de cristal, mais là je crois que c'est ça ! 😂",
        "Si j'avais un euro à chaque fois qu'on me pose cette question... 💸",
        "Je suis un bot, mais je commence à comprendre les humains ! 🤖",
        "Je suis pas parfait, mais j'essaie ! 😅"
    ]

    r = random.random()
    if r < 0.15:
        prefix = random.choice(positives)
    elif r < 0.2:
        prefix = random.choice(humoristiques)
    else:
        prefix = random.choice(neutres)
    return f"{prefix} {base_reponse}"

def detect_simple_greetings(message):
    msg = message.lower()
    if any(greet in msg for greet in ["bonjour", "salut", "coucou", "hello", "hey"]):
        return random.choice([
            "Bonjour ! Comment puis-je t'aider aujourd'hui ?",
            "Salut ! Ravi de te voir.",
            "Coucou ! Que puis-je faire pour toi ?"
        ])
    if any(q in msg for q in ["comment vas-tu", "comment ça va", "ça va", "tu vas bien"]):
        return random.choice([
            "Je vais très bien, merci ! Et toi ?",
            "Tout roule ici, prêt à t'aider !",
            "Super bien, merci de demander !"
        ])
    return None

def obtenir_la_response(message):
    from app.memory import memoire_cache, lock, save_memory

    message = message.strip()
    if not message:
        return "Je n'ai pas bien saisi ta question, pourrais-tu reformuler s'il te plaît ?"

    simple_resp = detect_simple_greetings(message)
    if simple_resp:
        return simple_resp

    if message.lower().startswith(WIKI_TRIGGER):
        query = message[len(WIKI_TRIGGER):].strip()
        if not query:
            return "Hmm, tu dois me dire ce que tu veux que je cherche sur Wikipédia."
        try:
            resume = get_wikipedia_summary(query)
            if resume:
                return ton_humain_reponse(f"Voilà ce que j'ai trouvé sur Wikipédia pour ta recherche :\n{resume}")
            return ton_humain_reponse("Désolé, je n'ai rien trouvé de pertinent sur Wikipédia.")
        except Exception as e:
            return ton_humain_reponse(f"Une erreur est survenue lors de la recherche sur Wikipédia : {str(e)}")

    with lock:
        if not memoire_cache:
            memoire_cache.append({"question": message, "response": "Je vais m'en souvenir pour la prochaine fois."})
            save_memory()
            update_corpus_embeddings()
            return ton_humain_reponse(f"C'est la première fois que tu me poses ça, je retiens : « {message} »")

    try:
        query_embedding = model.encode(message, convert_to_tensor=True)
    except Exception as e:
        return ton_humain_reponse(f"Une erreur est survenue lors de l'encodage de ta question : {str(e)}")

    global corpus_embeddings
    if corpus_embeddings is not None:
        try:
            similarities = util.cos_sim(query_embedding, corpus_embeddings)[0]
            best_score, best_index = float(similarities.max()), int(similarities.argmax())
            if best_score > 0.6:
                with lock:
                    reponse = memoire_cache[best_index]["response"]
                return ton_humain_reponse(f"Je pense que ceci répond à ta question :\n{reponse}")
        except Exception as e:
            return ton_humain_reponse(f"Une erreur est survenue lors de la recherche de similarités : {str(e)}")

    google_result = recherche_google(message)
    if google_result:
        with lock:
            memoire_cache.append({"question": message, "response": google_result})
            if len(memoire_cache) > TAILLE_MAX:
                memoire_cache.pop(0)
            save_memory()
            update_corpus_embeddings()
        return ton_humain_reponse(f"Voici ce que j'ai trouvé via Google :\n{google_result}")

    with lock:
        memoire_cache.append({"question": message, "response": "Je vais m'en souvenir pour la prochaine fois."})
        if len(memoire_cache) > TAILLE_MAX:
            memoire_cache.pop(0)
        save_memory()
        update_corpus_embeddings()
    return ton_humain_reponse("Je ne connais pas encore la réponse, mais je l'apprendrai pour toi !")
