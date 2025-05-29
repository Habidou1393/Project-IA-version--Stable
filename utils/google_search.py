import requests
import re
from collections import Counter
from app.config import GOOGLE_API_KEY, GOOGLE_CX

def recherche_google(query):
    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": query, "hl": "fr"},
            timeout=5
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        texte = " ".join(item.get("snippet", "") for item in items if "snippet" in item).strip()
        if not texte:
            return None

        phrases = [p for p in re.split(r'(?<=[.!?])\s+', texte) if len(p) > 40]
        if not phrases:
            return texte

        freq = Counter(re.findall(r'\w+', texte.lower()))
        communs = set(dict(freq.most_common(20)))

        def score(phrase): return sum(w in communs for w in phrase.lower().split())

        return " ".join(sorted(phrases, key=score, reverse=True)[:3]) or texte

    except Exception as e:
        print(f"[Google Search Error] {e}")
        return None
