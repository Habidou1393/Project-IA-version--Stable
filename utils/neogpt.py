from utils.gpt_neo import GPTNeoGenerator  # Import du générateur GPT-Neo personnalisé


class NeoGPT:
    def __init__(self, personality: str = "assistant", **kwargs):
        """
        Initialise l’IA avec un type de personnalité (style de réponse).
        - personality : définit le ton / style des réponses (assistant, humor, pro)
        - kwargs : paramètres supplémentaires pour GPTNeoGenerator (ex: modèle, seed...)
        """
        self.generator = GPTNeoGenerator(**kwargs)  # Instancie le générateur GPT-Neo
        self.personality = personality  # Stocke la personnalité choisie

    def format_prompt(self, user_input: str) -> str:
        """
        Formate le prompt en fonction de la personnalité définie.
        - Prend la saisie utilisateur et la modifie pour guider le style de la réponse.
        """
        if self.personality == "humor":  # Si personnalité humoristique
            return f"Réponds de façon drôle : {user_input}"  # Invite à répondre de façon drôle
        elif self.personality == "pro":  # Si personnalité professionnelle
            return f"Réponds comme un expert professionnel : {user_input}"  # Invite à répondre de façon experte
        else:  # Par défaut, style assistant utile
            return f"Tu es un assistant utile. {user_input}"  # Invite à répondre de manière utile

    def chat(self, user_input: str, **gen_params) -> str:
        """
        Génère une réponse en formatant le prompt selon la personnalité.
        - user_input : texte saisi par l’utilisateur
        - gen_params : paramètres optionnels de génération (max_length, temperature, etc)
        """
        prompt = self.format_prompt(user_input)  # Formate le prompt avec le style désiré
        return self.generator.generate(prompt, **gen_params)  # Génère et renvoie la réponse texte
