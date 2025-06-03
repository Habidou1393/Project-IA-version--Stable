import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Mot-clé déclencheur pour lancer une recherche sur Wikipédia dans les requêtes utilisateur
WIKI_TRIGGER = "recherche sur wikipedia"

# Mot-clé déclencheur pour lancer une recherche sur Google dans les requêtes utilisateur
GOOGLE_TRIGGER = "recherche sur google"

# Mot-clé déclencheur pour résoudre des expressions mathématiques dans les requêtes utilisateur
MATH_TRIGGER = "maths : "
