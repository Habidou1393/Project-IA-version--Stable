import requests
import re
from collections import Counter
from app.config import GOOGLE_API_KEY, GOOGLE_CX

def recherche_google(query):
    try:
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": query, "hl": "fr"},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        if not items:
            return None
        texte = " ".join(i.get("snippet", "") for i in items if "snippet" in i).strip()
        if not texte:
            return None

        phrases = [p.strip() for p in re.split(r'(?<=[.!?]) +', texte) if len(p.strip()) > 40]
        mots = re.findall(r'\w+', texte.lower())
        freq = Counter(mots)
        communs = set(mot for mot, _ in freq.most_common(20))

        def pertinence(phrase):
            return sum(mot in communs for mot in phrase.lower().split())

        phrases_importantes = sorted(phrases, key=pertinence, reverse=True)[:3]
        resume = " ".join(phrases_importantes)
        return resume or texte
    except (requests.RequestException, ValueError) as e:
        print(f"Une erreur est survenue lors de la recherche Google : {str(e)}")
        return None
