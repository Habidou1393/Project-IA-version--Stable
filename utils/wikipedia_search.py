import logging  # Importe le module standard pour la journalisation (logging)
from wikipedia import summary, set_lang, DisambiguationError, PageError  # Importe les fonctions et exceptions nécessaires du module wikipedia
from functools import lru_cache  # Pour appliquer un cache mémoire à la fonction (mémoïsation)
from typing import Optional, Union, List  # Pour la gestion des types d'arguments et de retour

logger = logging.getLogger(__name__)  # Crée un logger pour le module courant (utile pour les messages de debug/info/warning/error)

# Définit la langue par défaut de Wikipédia (ici français)
set_lang("fr")

@lru_cache(maxsize=128)  # Décorateur qui active le cache pour cette fonction (évite les appels redondants avec les mêmes paramètres)
def recherche_wikipedia(
    query: str,  # La requête à rechercher sur Wikipédia (obligatoire)
    lang: str = "fr",  # Langue de la recherche (par défaut français)
    sentences: int = 2,  # Nombre de phrases à extraire dans le résumé (par défaut 2)
    auto_suggest: bool = True,  # Permet à Wikipédia de corriger automatiquement les fautes ou approximations
    redirect: bool = True,  # Suivre automatiquement les redirections de pages
    return_disambiguation: bool = False,  # Si la requête est ambiguë, retourne la liste des options au lieu de None
    logger: Optional[logging.Logger] = None  # Logger optionnel pour personnaliser la journalisation
) -> Optional[Union[str, List[str]]]:  # La fonction retourne soit un résumé (str), soit une liste (désambiguïsation), soit None

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
