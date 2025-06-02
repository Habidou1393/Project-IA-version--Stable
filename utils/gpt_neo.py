# gpt_neo.py
from transformers import pipeline, set_seed
from typing import Optional


class GPTNeoGenerator:
    def __init__(self, model_name: str = "EleutherAI/gpt-neo-125M", seed: Optional[int] = None):
        """
        Initialise le pipeline de génération de texte.
        """
        self.model_name = model_name
        self.generator = pipeline("text-generation", model=model_name)

        if seed is not None:
            set_seed(seed)

    def generate(
        self,
        prompt: str,
        max_length: int = 150,
        temperature: float = 0.9,
        top_k: int = 50,
        top_p: float = 0.95,
        repetition_penalty: float = 1.0,
    ) -> str:
        """
        Génère un texte en fonction d’un prompt et de paramètres personnalisés.
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Le prompt doit être une chaîne de caractères non vide.")

        results = self.generator(
            prompt,
            max_length=max_length,
            do_sample=True,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
        )
        return results[0]['generated_text'].strip()
