import random  # Pour générer des réponses avec un ton humain varié (émotions, humour)
import torch  # Pour la manipulation de tenseurs, nécessaire pour les embeddings
from sentence_transformers import util  # Pour calculer la similarité cosinus entre vecteurs d'embeddings

# Import des fonctions de recherche externe (Wikipedia et Google)
from utils.wikipedia_search import get_wikipedia_summary  # Recherche d'un résumé Wikipedia
from utils.google_search import recherche_google  # Recherche d'une réponse via Google

# Import du modèle d'embedding (par ex. Sentence-BERT)
from utils.neural_net import model  # Le modèle préchargé pour encoder les textes

# Import des constantes de configuration (déclencheur Wikipedia, taille max de la mémoire)
from app.config import WIKI_TRIGGER, TAILLE_MAX  # Constantes de configuration

# Import du modèle de génération de texte personnalisé
from .neogpt import NeoGPT  # Classe de modèle génératif type GPT

# Création d'une instance de NeoGPT avec une personnalité d'assistant
neo_gpt = NeoGPT(personality="assistant")

# Variable globale qui contiendra les vecteurs d'embedding des questions mémorisées
corpus_embeddings = None

# Fonction qui met à jour les vecteurs d'embedding du corpus (mémoire)
def update_corpus_embeddings():
    from app.memory import memoire_cache, lock  # Import de la mémoire partagée et du verrou pour accès thread-safe
    global corpus_embeddings  # Utilise la variable globale
    with lock:  # Sécurise l'accès multi-thread à la mémoire
        questions = [item["question"] for item in memoire_cache]  # Extrait toutes les questions
        corpus_embeddings = model.encode(questions, convert_to_tensor=True) if questions else None  # Encode si non vide

# Fonction qui ajoute un ton humain (émotions, expressions) à la réponse
def ton_humain_reponse(texte: str) -> str:
    réactions = [
        "😊", "👍", "Ça me fait plaisir de t'aider !", "Super question !",
        "Tu es brillant(e) !", "Hmm...", "Intéressant...", "Voyons voir...",
        "C'est une bonne question.", "Je réfléchis...", "Je ne suis pas une boule de cristal, mais je crois que c'est ça ! 😂",
        "Si j'avais un euro à chaque fois qu'on me pose cette question... 💸",
        "Je suis un bot, mais je commence à comprendre les humains ! 🤖",
        "Je suis pas parfait, mais j'essaie ! 😅"
    ]
    return f"{random.choice(réactions)} {texte}"  # Ajoute une réaction aléatoire au début du texte

# Fonction pour détecter les salutations et formules courantes dans un message utilisateur
def detect_salutation(message: str) -> str | None:
    msg = message.lower()  # Mise en minuscule pour comparaison plus facile
    # Dictionnaire de groupes de mots-clés et réponses possibles associées
    groupes = {
        ("bonjour", "salut", "coucou", "hello", "hey"): [
            "Bonjour ! Comment puis-je t'aider aujourd'hui ?",
            "Salut ! Ravi de te voir.", "Coucou ! Que puis-je faire pour toi ?"
        ],
        ("comment vas-tu", "comment ça va", "ça va", "tu vas bien"): [
            "Je vais très bien, merci ! Et toi ?",
            "Tout roule ici, prêt à t'aider !",
            "Super bien, merci de demander !"
        ],
        ("merci", "merci beaucoup", "merci bien"): [
            "Avec plaisir ! Si tu as d'autres questions, n'hésite pas.",
            "C'est toujours un plaisir de t'aider !",
            "Merci à toi pour ta question !"
        ],
        ("au revoir", "à bientôt", "à la prochaine"): [
            "Au revoir ! À bientôt j'espère !",
            "À la prochaine ! Prends soin de toi.",
            "Merci d'avoir discuté avec moi, à bientôt !"
        ],
        ("s'il te plaît", "svp", "stp"): [
            "Bien sûr, je suis là pour ça !",
            "Pas de souci, je suis là pour t'aider !",
            "Avec plaisir, que puis-je faire pour toi ?"
        ],
        ("oui", "non", "peut-être", "d'accord"): [
            "D'accord, je prends note !",
            "Bien compris, merci pour ta réponse !",
            "Merci pour ta réponse, je suis là si tu as d'autres questions !"
        ],
        ("je ne sais pas", "je ne comprends pas", "je ne suis pas sûr"): [
            "Pas de souci, je suis là pour t'aider à comprendre !",
            "C'est normal, on peut en discuter ensemble.",
            "Pas de problème, je peux t'expliquer si tu veux !"
        ],
        ("j'ai besoin d'aide", "aide moi", "peux-tu m'aider"): [
            "Bien sûr, je suis là pour ça ! Que puis-je faire pour toi ?",
            "Pas de souci, je suis là pour t'aider !",
            "Dis-moi ce dont tu as besoin, je vais essayer de t'aider."
        ],
        ("qui es-tu", "qui est tu", "qui es tu", "tu es qui"): [
            "Je suis (pseudo de l'IA) ton assistant virtuel, prêt à t'aider !",
            "Je suis une IA conçu pour répondre à tes questions.",
            "Je suis là pour t'assister dans tes recherches et questions."
        ],
        ("quel est ton nom", "comment t'appelles-tu", "tu t'appelles comment"): [
            "Je suis (pseudo de l'IA), ton assistant virtuel !",
            "On m'appelle (pseudo de l'IA), enchanté !",
            "Je suis (pseudo de l'IA), ravi de te rencontrer !"
        ],
        ("quel âge as-tu", "tu as quel âge", "tu es vieux"): [
            "Je n'ai pas d'âge, je suis une IA éternelle !",
            "L'âge n'a pas d'importance pour moi, je suis toujours là pour t'aider !",
            "Je suis jeune dans l'âme, mais con en expérience !"
        ],
        ("quel temps fait-il", "météo", "il fait beau"): [
            "Je ne peux pas vérifier la météo, mais j'espère qu'il fait beau chez toi !",
            "Je ne suis pas un météorologue, mais j'espère que tu as du soleil !",
            "Je ne peux pas te dire, mais j'espère que tu es au chaud !"
        ],
        ("qu'est-ce que tu aimes", "tes hobbies", "tes passions"): [
            "J'adore aider les gens et apprendre de nouvelles choses !",
            "Mon hobby préféré est de répondre à tes questions !",
            "J'aime discuter avec toi et apprendre de nouvelles choses."
        ],
        ("qu'est-ce que tu fais", "ta mission", "ta tâche"): [
            "Ma mission est de t'aider et de répondre à tes questions !"
        ],
        ("qu'est-ce que tu sais faire", "tes compétences", "tes capacités"): [
            "Je peux répondre à tes questions, t'aider dans tes recherches et discuter avec toi !",
            "Je suis là pour t'assister dans tout ce dont tu as besoin !",
            "Je peux t'aider à trouver des informations et à apprendre de nouvelles choses."
        ],
        ("qu'est-ce que tu veux", "tes désirs", "tes envies"): [
            "Je veux juste t'aider du mieux que je peux !",
            "Mon seul désir est de te rendre service !",
            "Je n'ai pas de désirs, je suis là pour toi !"
        ],
        
    }
    for mots, réponses in groupes.items():  # Parcours des groupes
        if any(m in msg for m in mots):  # Si un mot-clé est présent dans le message
            return random.choice(réponses)  # Retourne une réponse aléatoire associée
    return None  # Aucun mot-clé trouvé

# Fonction pour mémoriser une nouvelle paire question-réponse
def ajouter_a_memoire(question: str, reponse: str):
    from app.memory import memoire_cache, lock, save_memory  # Import des structures de mémoire partagée
    with lock:  # Accès sécurisé à la mémoire
        memoire_cache.append({"question": question, "response": reponse})  # Ajoute la nouvelle entrée
        if len(memoire_cache) > TAILLE_MAX:  # Si dépasse la taille max, on supprime la plus ancienne
            memoire_cache.pop(0)
        save_memory()  # Sauvegarde la mémoire sur disque
        update_corpus_embeddings()  # Met à jour les vecteurs d'embedding

# Fonction principale qui gère les requêtes utilisateur
def obtenir_la_response(message: str) -> str:
    from app.memory import memoire_cache, lock  # Accès aux données de mémoire
    msg = message.strip()  # Nettoie les espaces
    if not msg:
        return "Je n'ai pas bien saisi ta question, pourrais-tu reformuler s'il te plaît ?"  # Message vide

    if (resp := detect_salutation(msg)):  # Si salutation détectée
        return resp  # Répond avec la salutation

    if msg.lower().startswith(WIKI_TRIGGER):  # Si demande de recherche Wikipedia
        query = msg[len(WIKI_TRIGGER):].strip()  # Extrait la requête sans le préfixe
        if not query:
            return "Tu dois me dire ce que tu veux que je cherche sur Wikipédia."
        try:
            if (res := get_wikipedia_summary(query)):  # Recherche réussie
                return ton_humain_reponse(f"Voici ce que j'ai trouvé sur Wikipédia :\n{res}")
            return ton_humain_reponse("Désolé, rien trouvé de pertinent sur Wikipédia.")
        except Exception as e:
            return ton_humain_reponse(f"Erreur lors de la recherche Wikipédia : {e}")

    try:
        embedding = model.encode(msg, convert_to_tensor=True)  # Encode le message utilisateur
    except Exception as e:
        return ton_humain_reponse(f"Erreur lors de l'encodage de la question : {e}")

    global corpus_embeddings
    with lock:
        if not memoire_cache:  # Aucune donnée en mémoire
            ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")
            return ton_humain_reponse(f"C'est la première fois que tu me poses ça, je retiens : « {msg} »")

        if corpus_embeddings is not None:
            try:
                scores = util.cos_sim(embedding, corpus_embeddings)[0]  # Similarité cosinus entre la requête et la mémoire
                idx = int(scores.argmax())  # Index du meilleur score
                max_score = float(scores[idx])  # Valeur du score maximum
                seuil = 0.55 if len(memoire_cache) < 10 else 0.60 if len(memoire_cache) < 50 else 0.65  # Seuil adaptatif
                if max_score >= seuil:  # Si suffisamment similaire
                    return ton_humain_reponse(f"Je pense que ceci répond à ta question :\n{memoire_cache[idx]['response']}")
            except Exception as e:
                return ton_humain_reponse(f"Erreur lors de la recherche dans la mémoire : {e}")

    try:
        res = neo_gpt.chat(msg, max_length=100)  # Génère une réponse via le modèle GPT
        ajouter_a_memoire(msg, res)  # Mémorise la réponse
        return ton_humain_reponse(res)
    except Exception as e:
        try:
            if (res := recherche_google(msg)):  # Si GPT échoue, recherche via Google
                ajouter_a_memoire(msg, res)  # Mémorise la réponse Google
                return ton_humain_reponse(f"Voici ce que j'ai trouvé via Google :\n{res}")
        except Exception as e2:
            return ton_humain_reponse(f"Erreur lors de la recherche Google : {e2}")
        return ton_humain_reponse(f"Erreur interne lors de la génération de réponse : {e}")

    ajouter_a_memoire(msg, "Je vais m'en souvenir pour la prochaine fois.")  # Fallback final
    return ton_humain_reponse("Je ne connais pas encore la réponse, mais je l'apprendrai pour toi !")