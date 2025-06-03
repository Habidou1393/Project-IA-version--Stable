const chat = document.getElementById("chatMessages");
const input = document.getElementById("userInput");
const form = document.getElementById("chatForm");

let loadingMsg = null;

// Crée un message et l’ajoute à la zone de chat
function ajouterMessage(nom, texte, classe) {
    const div = document.createElement("div");
    div.className = `message ${classe}`;
    div.innerHTML = `<strong>${nom}</strong> ${texte}`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
    return div;
}

// Affiche un indicateur de chargement animé
function creerSpinner() {
    const span = document.createElement("span");
    span.className = "spinner";
    span.innerText = "est en train d’écrire...";
    return span;
}

// Envoie le message et gère la réponse
async function envoyerMessage() {
    const message = input.value.trim();
    if (!message) return;

    ajouterMessage("Moi :", message, "user");
    input.value = "";
    input.disabled = true;

    loadingMsg = ajouterMessage("Chatbot :", "", "bot");
    loadingMsg.appendChild(creerSpinner());

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });

        if (!response.ok) throw new Error("Erreur serveur");

        const data = await response.json();
        loadingMsg.innerHTML = `<strong>Chatbot :</strong> ${data.response}`;


    } catch (err) {
        console.error("Erreur lors de l’envoi :", err);
        loadingMsg.innerHTML = `<strong>Chatbot :</strong> Erreur réseau. Veuillez réessayer.`;
    } finally {
        input.disabled = false;
        input.focus();
    }
}

// Gestion du formulaire (envoi avec Entrée)
form.addEventListener("submit", function (e) {
    e.preventDefault();
    envoyerMessage();
});

// Support Shift+Enter pour nouvelle ligne
input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && e.shiftKey) {
        e.stopPropagation();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.slice(0, start) + "\n" + this.value.slice(end);
        this.selectionStart = this.selectionEnd = start + 1;
        e.preventDefault();
    }
});
