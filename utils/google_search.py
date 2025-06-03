import logging  # Pour gérer les logs d'informations, d'erreurs, etc.
from googlesearch import search  # Pour effectuer une recherche Google à partir d'une requête
from bs4 import BeautifulSoup  # Pour analyser et extraire du texte HTML
import requests  # Pour faire des requêtes HTTP
from typing import Optional  # Pour indiquer qu'un argument peut être de type ou None

from utils.Mistral_API import ask_mistral  # Importe la fonction pour interroger l'API Mistral

logger = logging.getLogger(__name__)  # Initialise un logger spécifique au module courant

def recherche_google(query: str, logger: Optional[logging.Logger] = None, num_results: int = 3) -> Optional[str]:
    # Fonction qui cherche un mot via Google, extrait du texte utile d’un site, et demande à Mistral de résumer

    if logger is None:
        logger = logging.getLogger(__name__)  # Si aucun logger n'est fourni, on en crée un localement

    query = query.strip()  # Supprime les espaces superflus autour de la requête
    if not query:
        logger.warning("Requête Google vide.")  # Avertit si la requête est vide
        return None  # Arrête la fonction si aucune requête n’a été saisie

    try:
        logger.info(f"Recherche Google lancée pour : '{query}'")  # Log d'information sur le début de la recherche
        urls = list(search(query, num_results=num_results, lang="fr"))  # Effectue la recherche Google et récupère les URL

        if not urls:
            logger.warning(f"Aucun résultat Google pour '{query}'")  # Avertit s’il n’y a aucun résultat
            return None  # Retourne None si aucun lien n’a été trouvé

        for url in urls:  # Parcourt chaque URL trouvée
            try:
                response = requests.get(url, timeout=5)  # Tente de charger le contenu de la page (5s max)
                response.raise_for_status()  # Provoque une erreur si le code HTTP n’est pas 200

                soup = BeautifulSoup(response.text, "html.parser")  # Analyse le HTML de la page

                # 🔍 Récupère plusieurs paragraphes utiles
                paragraphes = soup.find_all("p")  # Trouve tous les paragraphes de la page
                contenu = " ".join(  # Concatène les textes de paragraphes sélectionnés
                    p.get_text(strip=True)  # Extrait le texte sans espace superflu
                    for p in paragraphes[:4]  # Prend les 4 premiers paragraphes
                    if len(p.get_text(strip=True)) > 60  # Ignore les paragraphes trop courts
                )

                if contenu:  # Si on a trouvé du contenu exploitable
                    titre = soup.title.string.strip() if soup.title and soup.title.string else url  # Récupère le titre de la page, ou l'URL si vide
                    logger.info(f"Contenu trouvé sur : {url}")  # Log indiquant qu’un contenu a été trouvé

                    # 🧠 Prompt orienté "définir le mot"
                    prompt = (  # Crée un prompt à envoyer à Mistral pour demander une explication
                        f"Voici un extrait de texte qui parle du mot « {query} » :\n\n"
                        f"{contenu}\n\n"
                        f"Explique simplement ce que signifie le mot « {query} » en français, en 2 phrases maximum."
                    )
                    resume = ask_mistral(prompt)  # Envoie le prompt à Mistral et récupère la réponse

                    # Retourne le résumé avec un lien cliquable vers la source
                    return f"{resume}<br><a href='{url}' target='_blank' rel='noopener noreferrer'>{titre}</a>"

            except Exception as e:
                logger.warning(f"Erreur en lisant {url} : {e}")  # Log d’erreur si une page n’a pas pu être lue

        logger.warning("Aucun contenu exploitable trouvé dans les résultats Google.")  # Avertit si aucun contenu valable n’a été trouvé
        return None  # Retourne None car aucun résultat n’a fonctionné

    except Exception as e:
        logger.error(f"Erreur globale Google pour '{query}' : {e}", exc_info=True)  # Log d’erreur globale inattendue
        return None  # Retourne None en cas d’erreur majeure
