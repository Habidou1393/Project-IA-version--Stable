from wikipedia import summary, set_lang, DisambiguationError, PageError
from functools import lru_cache

set_lang("fr")

@lru_cache(maxsize=128)
def get_wikipedia_summary(query: str) -> str | None:
    if not query.strip():
        return None
    try:
        return summary(query.strip(), sentences=2, auto_suggest=False, redirect=True)
    except (DisambiguationError, PageError, Exception):
        return None
