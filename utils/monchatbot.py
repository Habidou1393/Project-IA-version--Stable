import random  # Pour générer des réponses humaines aléatoires (emojis, expressions)
import torch  # Utilisé pour les tenseurs avec sentence-transformers
from sentence_transformers import util  # Pour le calcul de similarité cosinus entre embeddings

# Import des fonctions de recherche externe
from utils.wikipedia_search import get_wikipedia_summary  # Fonction de recherche dans Wikipédia
from utils.google_search import recherche_google  # Fonction de recherche via l'API Google

# Import du modèle de transformation de texte en vecteur
from utils.neural_net import model  # SentenceTransformer chargé ailleurs (BERT ou autre)

# Import de constantes de configuration
from app.config import WIKI_TRIGGER, TAILLE_MAX  # Déclencheur Wikipedia + taille max de mémoire

# Import du modèle génératif personnalisé (type GPT)
from .neogpt import NeoGPT

# Création d'une instance de NeoGPT avec une personnalité définie
neo_gpt = NeoGPT(personality="assistant")

# Variable globale pour stocker les embeddings des questions précédentes
corpus_embeddings = None

# Fonction qui met à jour les embeddings du corpus mémoire
def update_corpus_embeddings():
    from app.memory import memoire_cache, lock  # Import de la mémoire + verrou de thread
    global corpus_embeddings
    with lock:  # Sécurise l'accès multi-thread
        questions = [item["question"] for item in memoire_cache]  # On récupère toutes les questions mémorisées
        # Encode les questions si elles existent
        corpus_embeddings = model.encode(questions, convert_to_tensor=True) if questions else None

# Mise à jour initiale des embeddings
update_corpus_embeddings()

# Fonction pour humaniser les réponses avec des expressions aléatoires
def ton_humain_reponse(texte: str) -> str:
    réactions = (
        ["😊", "👍", "Ça me fait plaisir de t'aider !", "Super question !", "Tu es brillant(e) !"],  # Amical
        ["Hmm...", "Intéressant...", "Voyons voir...", "C'est une bonne question.", "Je réfléchis..."],  # Neutre
        ["Je ne suis pas une boule de cristal, mais je crois que c'est ça ! 😂",
         "Si j'avais un euro à chaque fois qu'on me pose cette question... 💸",
         "Je suis un bot, mais je commence à comprendre les humains ! 🤖",
         "Je suis pas parfait, mais j'essaie ! 😅"]  # Humour
    )
    r = random.random()
    # Choix du ton basé sur une probabilité
    prefix = random.choice(
        réactions[0] if r < 0.15 else réactions[2] if r < 0.2 else réactions[1]
    )
    return f"{prefix} {texte}"  # Ajoute un préfixe expressif à la réponse

# Détection des salutations ou formules de politesse dans les messages
def detect_salutation(message: str) -> str | None:
    msg = message.lower()
    # Si message contient un mot de salutation
    if any(greet in msg for greet in ["bonjour", "salut", "coucou", "hello", "hey"]):
        return random.choice([
            "Bonjour ! Comment puis-je t'aider aujourd'hui ?",
            "Salut ! Ravi de te voir.",
            "Coucou ! Que puis-je faire pour toi ?"
        ])
    
    # Si message contient une question de type "ça va ?"
    if any(x in msg for x in ["comment vas-tu", "comment ça va", "ça va", "tu vas bien"]):
        return random.choice([
            "Je vais très bien, merci ! Et toi ?",
            "Tout roule ici, prêt à t'aider !",
            "Super bien, merci de demander !"
        ])
    
    if any(x in msg for x in ["merci", "merci beaucoup", "merci bien"]):
        return random.choice([
            "Avec plaisir ! Si tu as d'autres questions, n'hésite pas.",
            "C'est toujours un plaisir de t'aider !",
            "Merci à toi pour ta question !"
        ])
    
    if any(x in msg for x in ["au revoir", "à bientôt", "à la prochaine"]):
        return random.choice([
            "Au revoir ! À bientôt j'espère !",
            "À la prochaine ! Prends soin de toi.",
            "Merci d'avoir discuté avec moi, à bientôt !"
        ])
    
    if any(x in msg for x in ["s'il te plaît", "svp", "stp"]):
        return random.choice([
            "Bien sûr, je suis là pour ça !",
            "Pas de souci, je suis là pour t'aider !",
            "Avec plaisir, que puis-je faire pour toi ?"
        ])
    
    if any(x in msg for x in ["oui", "non", "peut-être", "d'accord"]):
        return random.choice([
            "D'accord, je prends note !",
            "Bien compris, merci pour ta réponse !",
            "Merci pour ta réponse, je suis là si tu as d'autres questions !"
        ])
    
    if any(x in msg for x in ["je ne sais pas", "je ne comprends pas", "je ne suis pas sûr"]):
        return random.choice([
            "Pas de souci, je suis là pour t'aider à comprendre !",
            "C'est normal, on peut en discuter ensemble.",
            "Pas de problème, je peux t'expliquer si tu veux !"
        ])
    
    if any(x in msg for x in ["j'ai besoin d'aide", "aide moi", "peux-tu m'aider"]):
        return random.choice([
            "Bien sûr, je suis là pour ça ! Que puis-je faire pour toi ?",
            "Pas de souci, je suis là pour t'aider !",
            "Dis-moi ce dont tu as besoin, je vais essayer de t'aider."
        ])
    return None  # Pas de salutation détectée

# Ajoute une nouvelle question/réponse à la mémoire et met à jour les embeddings
def ajouter_a_memoire(question: str, reponse: str):
    from app.memory import memoire_cache, lock, save_memory
    with lock:
        memoire_cache.append({"question": question, "response": reponse})  # Ajout
        if len(memoire_cache) > TAILLE_MAX:  # On respecte la taille max
            memoire_cache.pop(0)
        save_memory()  # Sauvegarde sur disque
        update_corpus_embeddings()  # Met à jour les vecteurs

# Fonction principale qui gère une requête utilisateur
def obtenir_la_response(message: str) -> str:
    from app.memory import memoire_cache, lock

    msg = message.strip()  # Nettoyage
    if not msg:
        return "Je n'ai pas bien saisi ta question, pourrais-tu reformuler s'il te plaît ?"

    # Si message est une salutation, on répond directement
    if (resp := detect_salutation(msg)):
        return resp

    # Si l'utilisateur veut une recherche Wikipédia
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

    # Encodage de la requête utilisateur
    try:
        embedding = model.encode(msg, convert_to_tensor=True)
    except Exception as e:
        return ton_humain_reponse(f"Erreur lors de l'encodage de la question : {e}")

    global corpus_embeddings
    with lock:
        # Si mémoire vide, on enregistre simplement
        if not memoire_cache:
            ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")
            return ton_humain_reponse(f"C'est la première fois que tu me poses ça, je retiens : « {msg} »")

        # Si des embeddings sont présents, on cherche une réponse similaire
        if corpus_embeddings is not None:
            try:
                scores = util.cos_sim(embedding, corpus_embeddings)[0]  # Similarité cosinus
                idx = int(scores.argmax())  # Meilleur score
                max_score = float(scores[idx])

                # Seuil dynamique basé sur la taille de la mémoire
                seuil = 0.55 if len(memoire_cache) < 10 else 0.60 if len(memoire_cache) < 50 else 0.65
                if max_score >= seuil:
                    return ton_humain_reponse(f"Je pense que ceci répond à ta question :\n{memoire_cache[idx]['response']}")
            except Exception as e:
                return ton_humain_reponse(f"Erreur lors de la recherche dans la mémoire : {e}")

    # Si pas de match en mémoire, on essaie une génération via NeoGPT
    try:
        res = neo_gpt.chat(msg, max_length=100)
        ajouter_a_memoire(msg, res)
        return ton_humain_reponse(res)
    except Exception as e:
        # Si NeoGPT échoue, on tente Google en fallback
        try:
            if (res := recherche_google(msg)):
                ajouter_a_memoire(msg, res)
                return ton_humain_reponse(f"Voici ce que j'ai trouvé via Google :\n{res}")
        except Exception as e2:
            return ton_humain_reponse(f"Erreur lors de la recherche Google : {e2}")
        return ton_humain_reponse(f"Erreur interne lors de la génération de réponse : {e}")

    # Fallback ultime : on garde la question et on promet d'y revenir
    ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")
    return ton_humain_reponse("Je ne connais pas encore la réponse, mais je l'apprendrai pour toi !")
