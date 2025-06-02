import logging
from wikipedia import summary, set_lang, DisambiguationError, PageError
from functools import lru_cache
from typing import Optional, Union, List

logger = logging.getLogger(__name__)

# Définit la langue par défaut de Wikipédia (ici français)
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
        query (str): La requête à rechercher sur Wikipédia.
        lang (str): Code langue Wikipédia (ex: 'fr' pour français).
        sentences (int): Nombre maximum de phrases à retourner dans le résumé.
        auto_suggest (bool): Active la correction automatique si la requête est mal orthographiée.
        redirect (bool): Suivre automatiquement les redirections Wikipédia.
        return_disambiguation (bool): Si True, en cas de page ambigüe, retourne la liste des options possibles.
        logger (logging.Logger): Logger optionnel pour gérer les messages d'erreur ou warning.

    Returns:
        str, List[str] ou None: Résumé Wikipédia sous forme de texte,
                               ou liste d'options en cas de désambiguïsation si demandé,
                               ou None en cas d'erreur ou requête vide.
    """

    # Utilise un logger passé en paramètre ou crée un logger par défaut
    if logger is None:
        logger = logging.getLogger(__name__)

    # Nettoie la requête en enlevant espaces superflus
    query = query.strip()
    if not query:
        logger.warning("Requête Wikipédia vide.")  # Warn si la requête est vide
        return None  # On ne continue pas

    try:
        # Change la langue Wikipédia active pour la requête
        set_lang(lang)

        # Récupère un résumé selon la requête et paramètres
        texte = summary(query, sentences=sentences, auto_suggest=auto_suggest, redirect=redirect)

        # Si résumé non vide, on retourne le texte nettoyé
        if texte:
            return texte.strip()
        else:
            # Si résumé vide, on log un warning et retourne None
            logger.warning(f"Wikipedia: Résumé vide pour '{query}'.")
            return None

    # Gestion spécifique des erreurs liées à Wikipédia :

    # Si la page est ambiguë (plusieurs résultats possibles)
    except DisambiguationError as e:
        logger.warning(f"Wikipedia: Désambiguïsation pour '{query}', options : {e.options}")
        if return_disambiguation:
            # Si demandé, retourne la liste des options disponibles
            return e.options
        else:
            # Sinon on retourne None
            return None

    # Si la page n'existe pas (page introuvable)
    except PageError:
        logger.warning(f"Wikipedia: Page introuvable pour '{query}'.")
        return None

    # Gestion d'autres erreurs inattendues
    except Exception as e:
        # Log l'erreur complète avec traceback pour débogage
        logger.error(f"Wikipedia: Erreur inattendue pour '{query}': {e}", exc_info=True)
        return None
