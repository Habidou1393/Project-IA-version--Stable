import requests  # Pour faire les requêtes HTTP
import re  # Pour gérer les expressions régulières (découpage phrases, mots)
import logging  # Pour logger les erreurs et avertissements
from collections import Counter  # Pour compter la fréquence des mots
from app.config import GOOGLE_API_KEY, GOOGLE_CX  # Import des clés API et moteur custom

logger = logging.getLogger(__name__)  # Création d'un logger pour ce module

def recherche_google(query, timeout=5):
    
    if not query or not query.strip():
        return None  # Si la requête est vide ou None, on renvoie None directement

    try:
        # Paramètres pour l'appel à l'API Google Custom Search
        params = {
            "key": GOOGLE_API_KEY,  # Clé API Google
            "cx": GOOGLE_CX,        # Identifiant du moteur de recherche personnalisé
            "q": query,             # Texte de la requête utilisateur
            "hl": "fr",             # Langue des résultats (français)
            "fields": "items/snippet"  # On demande seulement les extraits des résultats
        }
    
        # Envoi de la requête GET à l'API Google Custom Search avec délai d'attente
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=timeout
        )
        resp.raise_for_status()  # Lève une erreur si code HTTP >= 400

        data = resp.json()  # Conversion de la réponse en dictionnaire Python
        items = data.get("items", [])  # Extraction des résultats (items)

        if not items:
            return None  # Si pas de résultats, on retourne None

        # Récupération et nettoyage des snippets de chaque résultat (suppression des retours à la ligne)
        snippets = [item.get("snippet", "").replace("\n", " ").strip() for item in items]

        texte = " ".join(snippets)  # Concaténation de tous les extraits en un seul texte

        if not texte:
            return None  # Si le texte est vide, on retourne None

        # Découpage du texte en phrases via regex, on garde celles avec au moins 40 caractères
        phrases = [p for p in re.split(r'(?<=[.!?])\s+', texte) if len(p) > 40]

        if not phrases:
            return texte  # Si pas de phrases longues, on retourne le texte brut

        # Extraction de tous les mots en minuscules pour calculer leur fréquence
        mots = re.findall(r'\w+', texte.lower())

        # Comptage des mots et récupération des 20 mots les plus fréquents
        freq = Counter(mots)
        communs = dict(freq.most_common(20))

        # Fonction de score d'une phrase basée sur la somme des fréquences des mots communs qu'elle contient
        def score(phrase):
            return sum(communs.get(w, 0) for w in re.findall(r'\w+', phrase.lower()))

        # Tri des phrases par score décroissant et sélection des 3 meilleures
        top_phrases = sorted(phrases, key=score, reverse=True)[:3]

        # Retourne la concaténation des meilleures phrases ou le texte complet en fallback
        return " ".join(top_phrases) if top_phrases else texte

    except requests.RequestException as e:
        logger.warning(f"[Google Search] Problème requête HTTP: {e}")  # Avertit en cas de problème réseau ou HTTP
    except ValueError as e:
        logger.warning(f"[Google Search] Erreur décodage JSON: {e}")  # Avertit en cas de JSON mal formé
    except Exception as e:
        logger.error(f"[Google Search] Erreur inattendue: {e}", exc_info=True)  # Logue toute autre erreur imprévue

    return None  # En cas d'erreur, on retourne None
