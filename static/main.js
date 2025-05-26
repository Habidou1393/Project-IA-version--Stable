const chat = document.getElementById("chat");
const input = document.getElementById("inputMessage");

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

input.addEventListener("keydown", function(e) {
    if (e.key === "Enter") envoyerMessage();
});
