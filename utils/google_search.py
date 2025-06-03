import logging
from googlesearch import search
from bs4 import BeautifulSoup
import requests
from typing import Optional

logger = logging.getLogger(__name__)

def recherche_google(query: str, logger: Optional[logging.Logger] = None, num_results: int = 3) -> Optional[str]:
    if logger is None:
        logger = logging.getLogger(__name__)

    query = query.strip()
    if not query:
        logger.warning("Requête Google vide.")
        return None

    try:
        logger.info(f"Recherche Google lancée pour : '{query}'")
        urls = list(search(query, num_results=num_results, lang="fr"))

        if not urls:
            logger.warning(f"Aucun résultat Google pour '{query}'")
            return None

        # Parcourt les résultats et tente d’extraire un résumé HTML
        for url in urls:
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # On tente d’extraire le premier paragraphe significatif
                p = soup.find("p")
                if p and p.get_text(strip=True):
                    texte = p.get_text(strip=True)
                    logger.info(f"Résumé trouvé sur : {url}")
                    return f"{texte}\n(Source : {url})"

            except Exception as e:
                logger.warning(f"Erreur en lisant {url} : {e}")

        logger.warning("Aucun contenu exploitable trouvé dans les résultats Google.")
        return None

    except Exception as e:
        logger.error(f"Erreur globale Google pour '{query}' : {e}", exc_info=True)
        return None
