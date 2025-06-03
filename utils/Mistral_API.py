import requests
from app.config import MISTRAL_API_KEY

def ask_mistral(prompt, model="mistral-small"):
    if not MISTRAL_API_KEY:
        return "Clé API Mistral manquante. Vérifie ton fichier config.py ou .env."

    url = "https://api.mistral.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    # ✅ Ajout d'un message système pour forcer le français
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu es un assistant utile et précis qui répond uniquement en français."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Erreur de requête : {e}"
    except KeyError:
        return f"Réponse inattendue de l'API : {response.text}"
