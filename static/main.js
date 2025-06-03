// Récupère les éléments HTML nécessaires : la zone de messages, le champ d’entrée et le formulaire
const chat = document.getElementById("chatMessages");
const input = document.getElementById("userInput");
const form = document.getElementById("chatForm");
const darkModeToggle = document.getElementById("darkModeToggle"); // Bouton de thème

darkModeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark"); // Active ou désactive le mode sombre
});

let loadingMsg = null; // Variable pour stocker le message "en cours de chargement"

// Fonction pour créer un nouveau message et l’ajouter à la zone de chat
function ajouterMessage(nom, texte, classe) {
    const div = document.createElement("div"); // Crée un nouvel élément <div>
    div.className = `message ${classe}`; // Attribue une classe CSS dynamique
    div.innerHTML = `<strong>${nom}</strong> ${texte}`; // Définit le contenu HTML du message
    chat.appendChild(div); // Ajoute le message à la zone de chat
    chat.scrollTop = chat.scrollHeight; // Fait défiler vers le bas pour voir le dernier message
    return div; // Retourne l’élément div (utile pour y ajouter un spinner par ex.)
}

// Fonction pour créer un indicateur de chargement ("Chatbot est en train d’écrire...")
function afficherChargement() {
    const span = document.createElement("span"); // Crée un élément <span>
    span.className = "spinner"; // Lui attribue la classe CSS "spinner"
    span.innerText = "est en train d’écrire..."; // Définit le texte affiché pendant le chargement
    return span; // Retourne l’élément <span>
}

// Fonction principale pour envoyer un message et traiter la réponse du serveur
async function envoyerMessage() {
    const message = input.value.trim(); // Récupère et nettoie le message saisi par l’utilisateur
    if (!message) return; // Ne fait rien si le champ est vide

    ajouterMessage("Moi :", message, "user"); // Affiche le message utilisateur dans le chat
    input.value = ""; // Vide le champ de saisie
    input.disabled = true; // Désactive temporairement la saisie pendant la requête

    loadingMsg = ajouterMessage("Chatbot :", "", "bot"); // Crée un message vide pour la réponse du bot
    loadingMsg.appendChild(afficherChargement()); // Ajoute un indicateur de chargement

    try {
        // Envoie la requête POST au backend Flask
        const response = await fetch("/ask", {
            method: "POST", // Méthode HTTP POST
            headers: { "Content-Type": "application/json" }, // Spécifie le format des données envoyées
            body: JSON.stringify({ message }), // Corps de la requête avec le message utilisateur
        });

        if (!response.ok) throw new Error("Erreur serveur"); // Lève une erreur si le serveur ne répond pas correctement

        const data = await response.json(); // Parse la réponse JSON
        loadingMsg.innerHTML = `<strong>Chatbot :</strong> ${data.response}`; // Affiche la réponse du bot

        // ✅ Détection de contenu LaTeX pour appliquer un style spécial
        if (data.response.includes("\\(") || data.response.includes("$$")) {
            loadingMsg.classList.add("math"); // Ajoute une classe spéciale si du LaTeX est détecté
        }

        // ✅ Rendu MathJax (si chargé dans la page)
        if (window.MathJax) MathJax.typeset(); // Lance le rendu MathJax pour le contenu mathématique
    } catch (err) {
        console.error("Erreur lors de l’envoi :", err); // Affiche une erreur dans la console (utile pour le debug)
        loadingMsg.innerHTML = `<strong>Chatbot :</strong> Erreur réseau. Veuillez réessayer.`; // Message d’erreur à l’utilisateur
    } finally {
        input.disabled = false; // Réactive le champ de saisie
        input.focus(); // Replace le curseur dans le champ de saisie
    }
}

// Intercepte la soumission du formulaire (clic ou touche "Entrée")
form.addEventListener("submit", function (e) {
    e.preventDefault(); // Empêche le rechargement de la page
    envoyerMessage(); // Appelle la fonction d’envoi du message
});

// Gestion de Shift+Enter pour insérer une nouvelle ligne dans le champ de saisie
input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && e.shiftKey) {
        // Si l’utilisateur appuie sur Shift + Entrée
        e.stopPropagation(); // Empêche l’événement de se propager
        const start = this.selectionStart; // Position de départ du curseur
        const end = this.selectionEnd; // Position de fin de sélection
        this.value = this.value.slice(0, start) + "\n" + this.value.slice(end); // Ajoute un saut de ligne
        this.selectionStart = this.selectionEnd = start + 1; // Replace le curseur après la nouvelle ligne
        e.preventDefault(); // Empêche le comportement par défaut (soumettre le formulaire)
    }
});