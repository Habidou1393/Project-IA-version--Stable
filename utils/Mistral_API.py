import requests  # Pour effectuer des requêtes HTTP
from app.config import MISTRAL_API_KEY  # Importe la clé API depuis la configuration du projet

def ask_mistral(prompt, model="mistral-small"):
    # Fonction qui envoie un prompt à l’API Mistral et retourne la réponse du modèle

    if not MISTRAL_API_KEY:
        # Vérifie que la clé API est définie
        return "Clé API Mistral manquante. Vérifie ton fichier config.py ou .env."

    url = "https://api.mistral.ai/v1/chat/completions"  # URL de l'API Mistral pour générer une réponse

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",  # Authentification avec la clé API
        "Content-Type": "application/json"  # Spécifie que les données envoyées sont au format JSON
    }

    # ✅ Préparation des données à envoyer à l'API (prompt + rôle)
    data = {
        "model": model,  # Nom du modèle à utiliser (ex : mistral-small)
        "messages": [
            {"role": "system", "content": "Tu es un assistant utile et précis qui répond uniquement en français."},  # Message système pour fixer le contexte
            {"role": "user", "content": prompt}  # Message de l'utilisateur avec le prompt fourni
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)  # Envoie la requête POST à l’API Mistral
        response.raise_for_status()  # Déclenche une exception si la réponse contient une erreur HTTP
        return response.json()["choices"][0]["message"]["content"]  # Retourne le texte de réponse généré
    except requests.exceptions.RequestException as e:
        return f"Erreur de requête : {e}"  # En cas d'erreur réseau ou HTTP, retourne un message d'erreur
    except KeyError:
        return f"Réponse inattendue de l'API : {response.text}"  # Si la structure JSON est incorrecte, affiche le texte brut
