import logging
from wikipedia import summary, set_lang, DisambiguationError, PageError
from functools import lru_cache
from typing import Optional, Union, List

logger = logging.getLogger(__name__)

# Définit la langue Wikipédia par défaut
set_lang("fr")

@lru_cache(maxsize=128)
def get_wikipedia_summary(
    query: str,
    lang: str = "fr",
    sentences: int = 2,
    auto_suggest: bool = True,
    redirect: bool = True,
    return_disambiguation: bool = False,
    logger: Optional[logging.Logger] = None 
) -> Optional[Union[str, List[str]]]:
    """
    Recherche un résumé Wikipédia pour une requête donnée.

    Args:
        query (str): Requête de recherche.
        lang (str): Langue de Wikipédia (ex: 'fr', 'en').
        sentences (int): Nombre de phrases dans le résumé.
        auto_suggest (bool): Permet la correction automatique de la requête.
        redirect (bool): Suivre automatiquement les redirections.
        return_disambiguation (bool): Si True, retourne la liste des options en cas de désambiguïsation.
        logger (logging.Logger): Logger pour les messages, sinon utilise le logger par défaut.

    Returns:
        str ou list ou None: Résumé Wikipédia, liste d'options en cas de désambiguïsation si `return_disambiguation` est True,
                            ou None en cas d'erreur ou requête vide.
    """

    if logger is None:
        logger = logging.getLogger(__name__)

    query = query.strip()
    if not query:
        logger.warning("Requête Wikipédia vide.")
        return None

    try:
        set_lang(lang)
        texte = summary(query, sentences=sentences, auto_suggest=auto_suggest, redirect=redirect)

        if texte:
            return texte.strip()
        else:
            logger.warning(f"Wikipedia: Résumé vide pour '{query}'.")
            return None

    except DisambiguationError as e:
        logger.warning(f"Wikipedia: Désambiguïsation pour '{query}', options : {e.options}")
        if return_disambiguation:
            # Retourner la liste des options pour que l'utilisateur puisse choisir
            return e.options
        else:
            return None

    except PageError:
        logger.warning(f"Wikipedia: Page introuvable pour '{query}'.")
        return None

    except Exception as e:
        logger.error(f"Wikipedia: Erreur inattendue pour '{query}': {e}", exc_info=True)
        return None
