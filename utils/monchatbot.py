import random  # Pour générer des réponses aléatoires (émoticônes ou phrases)
import re  # Pour utiliser des expressions régulières dans la détection mathématique
from utils.wikipedia_search import get_wikipedia_summary  # Fonction de résumé Wikipédia
from utils.google_search import recherche_google  # Fonction de recherche Google
from utils.Calcul_Maths import resoudre_expression_math  # Résolution d'expressions mathématiques
from app.config import WIKI_TRIGGER, GOOGLE_TRIGGER, MATH_TRIGGER  # Mots-clés déclencheurs pour les types de requêtes

# Génère une réponse humaine avec une touche aléatoire sympathique
def ton_humain_reponse(texte: str, math_mode: bool = False) -> str:
    if math_mode:
        return texte  # Ne pas ajouter de réaction dans le mode mathématique
    réactions = [  # Liste d'expressions et émojis pour rendre la réponse plus humaine
        "😊", "👍", "Ça me fait plaisir de t'aider !", "Super question !",
        "Tu es brillant(e) !", "Hmm...", "Intéressant...", "Voyons voir...",
        "C'est une bonne question.", "Je réfléchis...", "Je ne suis pas une boule de cristal, mais je crois que c'est ça ! 😂",
        "Si j'avais un euro à chaque fois qu'on me pose cette question... 💸",
        "Je suis un bot, mais je commence à comprendre les humains ! 🤖",
        "Je suis pas parfait, mais j'essaie ! 😅"
    ]
    return f"{random.choice(réactions)} {texte}"  # Retourne le texte avec une réaction aléatoire

# Détecte si un message est une salutation ou autre interaction basique et retourne une réponse adaptée
def detect_salutation(message: str) -> str | None:
    msg = message.lower().strip()  # Mise en minuscule pour comparaison
    if any(m in msg for m in ("bonjour", "salut", "coucou", "hello", "hey")):
        return random.choice([
            "Bonjour ! Comment puis-je t'aider aujourd'hui ?",
            "Salut ! Ravi de te voir.",
            "Coucou ! Que puis-je faire pour toi ?"
        ])
    if any(m in msg for m in ("ça va", "comment ça va", "comment vas-tu", "ça roule, cv ?")):
        return random.choice([
            "Ça va bien, merci ! Et toi ?",
            "Je vais bien, merci ! Et toi, comment ça se passe ?",
            "Tout roule de mon côté, et toi ?"
        ])
    if any(m in msg for m in ("au revoir", "bye", "à bientôt", "adieu")):
        return random.choice([
            "Au revoir ! À la prochaine !",
            "Bye ! Prends soin de toi.",
            "À bientôt ! N'hésite pas à revenir."
        ])
    if any(m in msg for m in ("merci", "merci beaucoup", "merci bien")):
        return random.choice([
            "Avec plaisir ! Si tu as d'autres questions, n'hésite pas.",
            "De rien ! Je suis là pour ça.",
            "Pas de souci, c'est toujours un plaisir de t'aider !"
        ])
    if any(m in msg for m in ("oui", "ouais", "d'accord", "ok")):
        return random.choice([
            "Super !",
            "D'accord, parfait !",
            "Ok, on continue alors !"
        ])
    if any(m in msg for m in ("non", "pas d'accord", "je ne pense pas")):
        return random.choice([
            "D'accord, je comprends. Si tu veux en discuter, je suis là.",
            "Pas de souci, chacun a son avis !",
            "Ok, pas de problème. Dis-moi si tu changes d'avis."
        ])
    if any(m in msg for m in ("peux-tu", "pourrais-tu", "est-ce que tu peux")):
        return random.choice([
            "Bien sûr, je suis là pour ça ! Que veux-tu que je fasse ?",
            "Oui, dis-moi ce que tu aimerais que je fasse.",
            "Je peux certainement t'aider avec ça. Que souhaites-tu ?"
        ])
    if any(m in msg for m in ("qui es-tu", "qui est tu", "qui es tu")):
        return random.choice([
            "Je suis ton assistant virtuel, prêt à t'aider !",
            "Je suis un chatbot conçu pour répondre à tes questions.",
            "Je suis là pour t'assister, que puis-je faire pour toi ?"
        ])
    return None  # Si aucun cas ne correspond, retourne None

# Détecte si le message contient probablement des maths (formules, mots-clés, symboles)
def est_message_mathematique(msg: str) -> bool:
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

# Fonction principale qui traite un message utilisateur et renvoie une réponse
def obtenir_la_response(message: str) -> str:
    from app.memory import memoire_cache, lock  # Import de la mémoire (cache)
    msg = message.strip()
    if not msg:
        return "Je n'ai pas bien saisi ta question, pourrais-tu reformuler s'il te plaît ?"

    if (resp := detect_salutation(msg)):
        return resp  # Retourne une réponse préprogrammée si salutation

    # 📚 Si la requête commence par le mot-clé pour Wikipedia
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

    # 🌐 Si la requête commence par le mot-clé pour Google
    if msg.lower().startswith(GOOGLE_TRIGGER):
        query = msg[len(GOOGLE_TRIGGER):].strip()
        if not query:
            return "Tu dois me dire ce que tu veux que je cherche sur Google."
        try:
            if (res := recherche_google(query)):
                return ton_humain_reponse(f"Voici ce que j'ai trouvé via Google :\n{res}")
            return ton_humain_reponse("Désolé, rien trouvé de pertinent via Google.")
        except Exception as e:
            return ton_humain_reponse(f"Erreur lors de la recherche Google : {e}")

    # ➕ Si la requête commence par le mot-clé pour les maths
    if msg.lower().startswith(MATH_TRIGGER):
        expression = msg[len(MATH_TRIGGER):].strip()
        if not expression:
            return ton_humain_reponse("Tu dois m’écrire une expression ou un problème mathématique à résoudre.")
        try:
            solution = resoudre_expression_math(expression)
            return ton_humain_reponse(solution, math_mode=True)
        except Exception as e:
            return ton_humain_reponse(f"Erreur lors du calcul mathématique : {e}")

    # 🔍 Si on détecte automatiquement une expression mathématique
    if est_message_mathematique(msg):
        try:
            solution = resoudre_expression_math(msg)
            return ton_humain_reponse(solution, math_mode=True)
        except Exception as e:
            return ton_humain_reponse(f"Erreur lors du calcul mathématique : {e}")

    # Cas par défaut : réponse de repli
    return ton_humain_reponse("Je ne connais pas encore la réponse, mais je vais l'apprendre !")