const chat = document.getElementById("chatMessages");
const input = document.getElementById("userInput");
const form = document.getElementById("chatForm");

function ajouterMessage(texte, classe) {
    const div = document.createElement("div");
    div.textContent = texte;
    div.className = "message " + classe;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

async function envoyerMessage() {
    const message = input.value.trim();
    if (!message) return;

    ajouterMessage("Toi : " + message, "user");
    input.value = "";

    const response = await fetch("/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: message})
    });
    const data = await response.json();
    ajouterMessage("Bot : " + data.response, "bot");
}

form.addEventListener("submit", function(e) {
    e.preventDefault();
    envoyerMessage();
});
