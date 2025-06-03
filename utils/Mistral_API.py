import requests
from app.config import MISTRAL_API_KEY

def ask_mistral(prompt: str, model: str = "mistral-small") -> str:
    """
    Envoie un prompt à l'API Mistral et retourne la réponse générée.

    :param prompt: Texte ou question à envoyer au modèle
    :param model: Nom du modèle Mistral à utiliser (ex : 'mistral-small')
    :return: Réponse texte générée ou message d'erreur
    """
    if not MISTRAL_API_KEY:
        return "Clé API Mistral manquante. Vérifie ton fichier config.py"

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la requête Mistral : {e}"
    except (KeyError, IndexError):
        return f"Réponse inattendue de l'API Mistral : {response.text}"
