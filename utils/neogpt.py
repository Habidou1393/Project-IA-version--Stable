# neogpt.py
from utils.gpt_neo import GPTNeoGenerator


class NeoGPT:
    def __init__(self, personality: str = "assistant", **kwargs):
        """
        Initialise l’IA avec un type de personnalité (style de réponse).
        """
        self.generator = GPTNeoGenerator(**kwargs)
        self.personality = personality

    def format_prompt(self, user_input: str) -> str:
        """
        Formate le prompt en fonction de la personnalité définie.
        """
        if self.personality == "humor":
            return f"Réponds de façon drôle : {user_input}"
        elif self.personality == "pro":
            return f"Réponds comme un expert professionnel : {user_input}"
        else:
            return f"Tu es un assistant utile. {user_input}"

    def chat(self, user_input: str, **gen_params) -> str:
        """
        Génère une réponse en formatant le prompt selon la personnalité.
        """
        prompt = self.format_prompt(user_input)
        return self.generator.generate(prompt, **gen_params)
