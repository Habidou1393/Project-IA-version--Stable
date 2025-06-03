from utils.Mistral_API import Mistral  # Importe la fonction pour interagir avec l'API Mistral
                                            
def resoudre_maths(expression: str) -> str:
    # Fonction qui traite une expression mathématique (avec ou sans explication),
    # et retourne la réponse générée par l'API Mistral.

    expression = expression.strip()  # Supprime les espaces inutiles en début et fin d'expression

    if not expression:
        # Vérifie si l'utilisateur a bien saisi quelque chose
        return "Tu dois entrer une expression mathématique à résoudre."

    demande_explicite = "explique" in expression.lower()
    # Détecte si l'utilisateur demande une explication (recherche du mot "explique", insensible à la casse)

    if demande_explicite:
        # Si une explication est demandée, on construit un prompt instructif et détaillé
        prompt = (
            f"En français : explique étape par étape comment résoudre l'expression mathématique suivante, "
            f"puis donne la réponse finale à la fin :\n{expression}"
        )
    else:
        # Sinon, on demande un calcul direct et concis sans explication
        prompt = (
            f"En français : calcule cette expression mathématique et donne uniquement le résultat final, sans explication :\n{expression}"
        )

    return Mistral(prompt)  # Envoie le prompt à l'API Mistral et retourne la réponse