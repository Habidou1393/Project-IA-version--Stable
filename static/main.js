const chat = document.getElementById("chatMessages");
const input = document.getElementById("userInput");
const form = document.getElementById("chatForm");

let loadingMsg = null;

// Fonction pour ajouter un message à l'interface
function ajouterMessage(nom, texte, classe) {
    const div = document.createElement("div");
    div.className = "message " + classe;
    div.textContent = `${nom} ${texte}`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
    return div;
}

// Envoi du message utilisateur + récupération de la réponse
async function envoyerMessage() {
    const message = input.value.trim();
    if (!message) return;

    ajouterMessage("Moi :", message, "user");
    input.value = "";
    input.disabled = true;

    // Affiche un message temporaire en attendant la réponse
    loadingMsg = ajouterMessage("Chatbot :", "est en train d’écrire...", "bot");

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        // Remplace le message temporaire par la vraie réponse
        loadingMsg.textContent = `Chatbot : ${data.response}`;

        // Suppression de la lecture vocale pour que le bot ne parle plus
        // if ('speechSynthesis' in window) {
        //     const utterance = new SpeechSynthesisUtterance(data.response);
        //     utterance.lang = 'fr-FR';
        //     speechSynthesis.speak(utterance);
        // }

    } catch (err) {
        console.error("Erreur serveur :", err);
        loadingMsg.textContent = "Chatbot : Erreur réseau. Veuillez réessayer.";
    } finally {
        input.disabled = false;
        input.focus();
    }
}

// Gestion du formulaire (bouton ou touche Entrée)
form.addEventListener("submit", function (e) {
    e.preventDefault();
    envoyerMessage();
});
