import requests
import re
import logging
from collections import Counter
from app.config import GOOGLE_API_KEY, GOOGLE_CX

logger = logging.getLogger(__name__)

def recherche_google(query, timeout=5):
    """
    Effectue une recherche Google via l'API Custom Search et retourne un résumé
    optimisé à partir des extraits des résultats.

    Args:
        query (str): La requête de recherche.
        timeout (int): Timeout en secondes pour la requête HTTP.

    Returns:
        str | None: Résumé textuel des résultats, ou None si aucune donnée.
    """
    try:
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": query,
            "hl": "fr",
            "fields": "items(snippet)"  # Ne récupérer que les snippets pour optimiser
        }
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=timeout
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return None

        # Concatène les snippets en nettoyant les espaces inutiles
        snippets = [item.get("snippet", "").strip() for item in items if "snippet" in item]
        texte = " ".join(snippets).replace("\n", " ").strip()
        if not texte:
            return None

        # Découpe en phrases (au moins 40 caractères pour éviter trop courtes)
        phrases = [p for p in re.split(r'(?<=[.!?])\s+', texte) if len(p) > 40]
        if not phrases:
            return texte

        # Compte la fréquence des mots (en minuscules)
        mots = re.findall(r'\w+', texte.lower())
        freq = Counter(mots)
        communs = dict(freq.most_common(20))

        # Score basé sur la somme des fréquences des mots communs présents dans la phrase
        def score(phrase):
            return sum(communs.get(w, 0) for w in re.findall(r'\w+', phrase.lower()))

        # Trie par score décroissant et prend les 3 meilleures phrases
        top_phrases = sorted(phrases, key=score, reverse=True)[:3]

        return " ".join(top_phrases) if top_phrases else texte

    except requests.RequestException as e:
        logger.warning(f"[Google Search] Problème requête HTTP: {e}")
    except ValueError as e:
        logger.warning(f"[Google Search] Erreur décodage JSON: {e}")
    except Exception as e:
        logger.error(f"[Google Search] Erreur inattendue: {e}", exc_info=True)
    return None
