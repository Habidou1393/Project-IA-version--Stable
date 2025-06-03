from utils.Mistral_API import ask_mistral

def resoudre_expression_math(expression: str) -> str:
    expression = expression.strip()
    if not expression:
        return "Tu dois entrer une expression mathématique à résoudre."

    demande_explicite = "explique" in expression.lower()

    if demande_explicite:
        prompt = (
            f"En français : explique étape par étape comment résoudre l'expression mathématique suivante, "
            f"puis donne la réponse finale à la fin :\n{expression}"
        )
    else:
        prompt = (
            f"En français : calcule cette expression mathématique et donne uniquement le résultat final, sans explication :\n{expression}"
        )

    return ask_mistral(prompt)
