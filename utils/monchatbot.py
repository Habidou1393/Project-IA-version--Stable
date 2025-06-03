import random
from sentence_transformers import util

from utils.wikipedia_search import get_wikipedia_summary
from utils.google_search import recherche_google
from app.config import WIKI_TRIGGER, TAILLE_MAX



def ton_humain_reponse(texte: str) -> str:
    réactions = [
        "😊", "👍", "Ça me fait plaisir de t'aider !", "Super question !",
        "Tu es brillant(e) !", "Hmm...", "Intéressant...", "Voyons voir...",
        "C'est une bonne question.", "Je réfléchis...", "Je ne suis pas une boule de cristal, mais je crois que c'est ça ! 😂",
        "Si j'avais un euro à chaque fois qu'on me pose cette question... 💸",
        "Je suis un bot, mais je commence à comprendre les humains ! 🤖",
        "Je suis pas parfait, mais j'essaie ! 😅"
    ]
    return f"{random.choice(réactions)} {texte}"

def detect_salutation(message: str) -> str | None:
    msg = message.lower().strip()
    # (mêmes blocs if qu'avant, inchangés)
    if any(m in msg for m in ("bonjour", "salut", "coucou", "hello", "hey")):
        return random.choice([
            "Bonjour ! Comment puis-je t'aider aujourd'hui ?",
            "Salut ! Ravi de te voir.",
            "Coucou ! Que puis-je faire pour toi ?"
        ])
    # … (les autres réponses préprogrammées ici identiques à ta version)
    return None

def obtenir_la_response(message: str) -> str:
    from app.memory import memoire_cache, lock
    msg = message.strip()
    if not msg:
        return "Je n'ai pas bien saisi ta question, pourrais-tu reformuler s'il te plaît ?"

    if (resp := detect_salutation(msg)):
        return resp

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
