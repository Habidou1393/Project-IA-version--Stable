import random
import re
from difflib import get_close_matches
from utils.wikipedia_search import recherche_wikipedia
from utils.google_search import recherche_google
from utils.Calcul_Maths import resoudre_maths
from app.config import WIKI_TRIGGER, GOOGLE_TRIGGER, MATH_TRIGGER


# ✅ Tolérance aux fautes
def texte_similaire(msg: str, expressions: list[str], seuil: float = 0.8) -> bool:
    return bool(get_close_matches(msg, expressions, n=1, cutoff=seuil))


# ✅ Extrait la politesse + la question utile
def extraire_politesse_et_question(msg: str) -> tuple[str | None, str]:
    msg = msg.strip().lower()
    politesses = [
        "peux-tu", "peux tu", "pourrais-tu", "pourrais tu", "tu peux", "tu pourrais",
        "tu-peux", "s'il te plaît", "stp", "svp", "sil te plait", "s il te plait",
        "est ce que", "est-ce que", "tu-pourrais", "donne moi", "m'aider","me donner","avoir"
    ]
    polie_trouvée = []
    for p in politesses:
        if p in msg:
            polie_trouvée.append(p)
            msg = msg.replace(p, "")
    propre = msg.strip()
    reponse_polie = None
    if polie_trouvée:
        reponse_polie = random.choice([
            "Bien sûr, je suis là pour ça !",
            "Avec plaisir 😊",
            "Oui bien sûr, je t’aide !",
            "Pas de souci, je te réponds 👇",
            "Aucun problème ! Voilà ce que j’ai trouvé :"
        ])
    return reponse_polie, propre


# ✅ Réponse humaine
def chatbot_reponse(texte: str, math_mode: bool = False) -> str:
    if math_mode:
        return texte
    réactions = [
        "😊", "👍", "Ça me fait plaisir de t'aider !", "Super question !",
        "Tu es brillant(e) !", "Hmm...", "Intéressant...", "Voyons voir...",
        "C'est une bonne question.", "Je réfléchis...",
        "Je ne suis pas une boule de cristal, mais je crois que c'est ça ! 😂",
        "Si j'avais un euro à chaque fois qu'on me pose cette question... 💸",
        "Je suis un bot, mais je commence à comprendre les humains ! 🤖",
        "Je suis pas parfait, mais j'essaie ! 😅"
    ]
    return f"{random.choice(réactions)} {texte}"


# ✅ Salutations
def detection_salutation(message: str) -> str | None:
    msg = message.lower().strip()
    if texte_similaire(msg, ["bonjour", "salut", "coucou", "hello", "hey", "bjr", "slut"]):
        return random.choice([
            "Bonjour ! Comment puis-je t'aider aujourd'hui ?",
            "Salut ! Ravi de te voir.",
            "Coucou ! Que puis-je faire pour toi ?"
        ])
    if texte_similaire(msg, [
        "ça va", "comment ça va", "comment sa va", "comment tu vas",
        "tu vas bien", "comment cava", "cv", "sava", "cava"
    ]):
        return random.choice([
            "Ça va bien, merci ! Et toi ?",
            "Je vais bien, merci ! Et toi, comment ça se passe ?",
            "Tout roule de mon côté, et toi ?"
        ])
    if texte_similaire(msg, ["au revoir", "bye", "à bientôt", "adieu", "aurevoir", "ciao","a plus"]):
        return random.choice([
            "Au revoir ! À la prochaine !",
            "Bye ! Prends soin de toi.",
            "À bientôt ! N'hésite pas à revenir."
        ])
    if texte_similaire(msg, ["merci", "merci beaucoup", "merci bien", "merki", "mercie","mrc"]):
        return random.choice([
            "Avec plaisir ! Si tu as d'autres questions, n'hésite pas.",
            "De rien ! Je suis là pour ça.",
            "Pas de souci, c'est toujours un plaisir de t'aider !"
        ])
    return None


# ✅ Détection maths
def Le_message_mathematique(msg: str) -> bool:
    msg = msg.lower()
    mots_cles = [
        "int(", "∫", "dérive", "dérivée", "intégrale", "primitive", "lim", "limite",
        "résous", "équation", "différentielle", "factorise", "racine", "polynôme",
        "dx", "dy", "sin", "cos", "tan", "ln", "log", "e^", "x^", "x²", "=", "≠", "<", ">"
    ]
    if any(m in msg for m in mots_cles):
        return True
    if re.match(r"^[\s\d\w\^\+\-\*\/\=\(\)]+$", msg) and any(c in msg for c in "=^"):
        return True
    return False

# ✅ Contenu inapproprié
def contient_contenu_inapproprié(msg: str) -> bool:
    blacklist = [
        "con", "connard", "pute", "salop", "enculé", "fdp", "ntm",
        "nique", "merde", "ta gueule", "tg", "salope", "batard"
    ]
    msg = msg.lower()
    return any(mot in msg for mot in blacklist)


# ✅ Fonction principale
def obtenir_la_response(message: str) -> str:
    msg = message.strip()
    if not msg:
        return "Je n'ai pas bien saisi ta question, pourrais-tu reformuler s’il te plaît ?"

    if contient_contenu_inapproprié(msg):
        return "Je suis là pour t’aider, mais restons respectueux s’il te plaît 😊"

    if (resp := detection_salutation(msg)):
        return resp

    reponse_polie, question = extraire_politesse_et_question(msg)

        # 🌍 Wikipédia (le mot peut être avant ou après)
    if WIKI_TRIGGER in question.lower():
        cleaned_question = question.lower().replace(WIKI_TRIGGER, "")
        query = re.sub(
            r"\b(peux-tu|peux tu|pourrais-tu|pourrais tu|tu peux|tu pourrais|tu-peux|"
            r"s'il te plaît|stp|svp|sil te plait|s il te plait|est ce que|est-ce que|"
            r"tu-pourrais|donne moi|m'aider|me donner|avoir|sur|dans|avec|la|le|"
            r"définition|recherche|rechercher|de|du|des|je|tu|il|nous|vous|ils|elle|elles|pourrais|le|la)\b",
            "",
            cleaned_question
        )
        query = query.strip(" :!?.,\"'")
        if not query:
            return "Tu dois me dire ce que tu veux que je cherche sur Wikipédia."
        try:
            res = recherche_wikipedia(query)
            if isinstance(res, list):
            # ← Cas d'ambiguïté : on propose des suggestions
                return chatbot_reponse("Ta question est trop vague. Voici plusieurs sujets possibles :\n- " + "\n- ".join(res))
            if res:
                return f"{reponse_polie + ' ' if reponse_polie else ''}" + chatbot_reponse(f"Voici ce que j'ai trouvé sur Wikipédia :\n{res}")
            return chatbot_reponse("Désolé, rien trouvé de pertinent sur Wikipédia.")
        except Exception as e:
            return chatbot_reponse(f"Erreur Wikipédia : {e}")

    # 🌐 Google (le mot peut être avant ou après)
    if GOOGLE_TRIGGER in question.lower():
        cleaned_question = question.lower().replace(GOOGLE_TRIGGER, "")
        query = re.sub(
            r"\b(peux-tu|peux tu|pourrais-tu|pourrais tu|tu peux|tu pourrais|tu-peux|"
            r"s'il te plaît|stp|svp|sil te plait|s il te plait|est ce que|est-ce que|"
            r"tu-pourrais|donne moi|m'aider|me donner|avoir|sur|dans|avec|la|le|"
            r"définition|recherche|rechercher|de|du|des|je|tu|il|nous|vous|ils|elle|elles|pourrais|le|la)\b",
            "",
            cleaned_question
        )
        query = query.strip(" :!?.,\"'")
        if not query:
            return "Tu dois me dire ce que tu veux que je cherche sur Google."
        try:
            print(f"[DEBUG] Requête Google nettoyée : {query}")
            res = recherche_google(query)
            if res:
                return f"{reponse_polie + ' ' if reponse_polie else ''}" + chatbot_reponse(f"Voici ce que j'ai trouvé via Google :\n{res}")
            return chatbot_reponse("Désolé, rien trouvé de pertinent via Google.")
        except Exception as e:
            return chatbot_reponse(f"Erreur Google : {e}")

    # ➕ Maths
    if MATH_TRIGGER in question.lower():
        expression = question.lower().split(MATH_TRIGGER, 1)[-1].strip()
        if not expression:
            return chatbot_reponse("Tu dois m’écrire une expression ou un problème mathématique à résoudre.")
        try:
            solution = resoudre_maths(expression)
            return chatbot_reponse(solution, math_mode=True)
        except Exception as e:
            return chatbot_reponse(f"Erreur mathématique : {e}")

    # 🔁 Par défaut
    suggestions = [
        "Je n’ai pas trouvé de réponse précise, veux-tu que je cherche sur Google ?",
        "Hmm, rien dans mes connaissances… veux-tu que j'essaie une recherche sur internet ?",
        "Je n'ai pas compris, tu peux reformuler ? Ou me dire si c’est une question Wikipédia, Google ou mathématique.",
        "Pas certain de la réponse 😕 Tu veux que j’explore un peu plus ?"
    ]
    return chatbot_reponse(random.choice(suggestions))