import wikipedia
from functools import lru_cache

wikipedia.set_lang("fr")

@lru_cache(maxsize=128)
def get_wikipedia_summary(query):
    try:
        return wikipedia.summary(query, sentences=2)
    except (wikipedia.DisambiguationError, wikipedia.PageError, Exception):
        return None
