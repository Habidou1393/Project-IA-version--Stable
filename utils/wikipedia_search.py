import logging
from wikipedia import summary, set_lang, DisambiguationError, PageError
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Définit la langue Wikipédia par défaut
set_lang("fr")

@lru_cache(maxsize=128)
def get_wikipedia_summary(query: str, lang: str = "fr", sentences: int = 2, auto_suggest: bool = True) -> Optional[str]:

    query = query.strip()
    if not query:
        return None

    try:
        set_lang(lang)
        texte = summary(query, sentences=sentences, auto_suggest=auto_suggest, redirect=True)
        return texte.strip() if texte else None
    except DisambiguationError as e:
        logger.warning(f"Wikipedia: Disambiguation pour '{query}': {e.options}")
    except PageError:
        logger.warning(f"Wikipedia: Page introuvable pour '{query}'.")
    except Exception as e:
        logger.error(f"Wikipedia: Erreur inattendue pour '{query}': {e}", exc_info=True)

    return None
