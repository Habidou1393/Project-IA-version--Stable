from transformers import pipeline, set_seed  # Import des outils Hugging Face pour génération de texte et pour fixer la graine aléatoire
from typing import Optional  # Import pour annotation de type optionnel

class GPTNeoGenerator:
    def __init__(self, model_name: str = "EleutherAI/gpt-neo-125M", seed: Optional[int] = None):
        # Constructeur de la classe avec nom du modèle et optionnellement une graine pour reproductibilité

        self.model_name = model_name  # Stocke le nom du modèle choisi
        self.generator = pipeline("text-generation", model=model_name)  
        # Initialise le pipeline de génération de texte avec le modèle spécifié

        if seed is not None:
            set_seed(seed)  # Fixe la graine aléatoire pour que les résultats soient reproductibles si demandé

    def generate(
        self,
        prompt: str,
        max_length: int = 150,
        temperature: float = 0.9,
        top_k: int = 50,
        top_p: float = 0.95,
        repetition_penalty: float = 1.0,
    ) -> str:
        # Méthode pour générer du texte à partir d'un prompt donné avec plusieurs paramètres pour contrôler la génération

        if not prompt or not isinstance(prompt, str):
            raise ValueError("Le prompt doit être une chaîne de caractères non vide.")  
            # Vérifie que le prompt est une chaîne non vide, sinon lève une erreur

        results = self.generator(
            prompt,
            max_length=max_length,  # Longueur maximale du texte généré
            do_sample=True,  # Active l'échantillonnage aléatoire pour la diversité des réponses
            temperature=temperature,  # Paramètre qui contrôle la créativité (plus bas = plus conservateur)
            top_k=top_k,  # Restreint la sélection aux top_k mots les plus probables
            top_p=top_p,  # Nucleus sampling : probabilité cumulative minimale pour considérer un mot
            repetition_penalty=repetition_penalty,  # Pénalité pour éviter répétitions excessives
        )

        return results[0]['generated_text'].strip()  
        # Renvoie le texte généré (premier résultat) après suppression des espaces superflus
