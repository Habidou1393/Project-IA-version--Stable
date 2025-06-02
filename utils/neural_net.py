import os  # Pour la gestion des fichiers
import torch  # PyTorch, framework ML
import torch.nn as nn  # Modules pour construire des réseaux de neurones
import torch.optim as optim  # Optimiseurs pour entraîner le modèle
from sentence_transformers import SentenceTransformer  # Pour générer des embeddings
from app.memory import memoire_cache, lock  # Mémoire partagée et verrou pour la synchronisation
import matplotlib.pyplot as plt  # Pour afficher les graphiques de loss

# Chargement du modèle d'embeddings multilingue
model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
# Détecte si GPU est disponible sinon CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Définition d'un bloc résiduel simple (inspiration Transformer)
class ResidualBlock(nn.Module):
    def __init__(self, dim):
        super().__init__()
        # Couche de normalisation + deux couches linéaires avec GELU et Dropout
        self.block = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, dim),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(dim, dim),
        )

    def forward(self, x):
        # Ajoute la sortie du bloc au input (connexion résiduelle)
        return x + self.block(x)

# Réseau de neurones complet avec attention multi-têtes et blocs résiduels
class ComplexNN(nn.Module):
    def __init__(self, input_dim=512, hidden_dim=1024, output_dim=512, num_blocks=4):
        super().__init__()
        # Couche linéaire d'entrée
        self.input_layer = nn.Linear(input_dim, hidden_dim)
        # Plusieurs blocs résiduels en séquence
        self.residual_blocks = nn.Sequential(*[ResidualBlock(hidden_dim) for _ in range(num_blocks)])
        # Mécanisme d'attention multi-têtes
        self.attention = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=8, batch_first=True)
        # Couche linéaire de sortie
        self.output_layer = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.input_layer(x)  # Passage de la couche d'entrée
        x = x.unsqueeze(1)  # Ajout d'une dimension batch sequence pour l'attention
        attn_output, _ = self.attention(x, x, x)  # Application de l'attention sur x
        x = self.residual_blocks(attn_output)  # Passage par les blocs résiduels
        x = x.squeeze(1)  # Suppression de la dimension sequence
        return self.output_layer(x)  # Passage par la couche de sortie

# Création du modèle et transfert vers GPU si disponible
nn_model = ComplexNN().to(device)
# Optimiseur AdamW avec taux d'apprentissage et weight decay
optimizer = optim.AdamW(nn_model.parameters(), lr=1e-4, weight_decay=1e-5)
# Scheduler qui ajuste le learning rate de façon cosinusoïdale sur 10 epochs
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)
# Fonction de perte MSE (mean squared error) adaptée à la régression
loss_fn = nn.MSELoss()
# Gestionnaire d'échelle pour mixed precision (accélération GPU)
scaler = torch.cuda.amp.GradScaler(enabled=torch.cuda.is_available())

MODEL_PATH = "data/nn_model.pt"  # Chemin pour sauvegarder le modèle

# 💾 Fonction pour sauvegarder le modèle et l'optimiseur
def save_model():
    torch.save({
        'model_state_dict': nn_model.state_dict(),  # État du modèle
        'optimizer_state_dict': optimizer.state_dict()  # État de l'optimiseur
    }, MODEL_PATH)
    print(f"💾 Modèle sauvegardé dans {MODEL_PATH}")

# 📤 Fonction pour charger le modèle si le fichier existe
def load_model():
    if os.path.exists(MODEL_PATH):
        checkpoint = torch.load(MODEL_PATH, map_location=device)  # Chargement checkpoint
        nn_model.load_state_dict(checkpoint['model_state_dict'])  # Chargement poids modèle
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])  # Chargement optimiseur
        print(f"✅ Modèle chargé depuis {MODEL_PATH}")
    else:
        print("🆕 Aucun modèle trouvé, nouveau modèle initialisé.")

# 📈 Fonction d'entraînement du modèle sur la mémoire
def train_nn_on_memory(epochs=10, show_plot=False):
    with lock:  # Bloc critique pour accéder à la mémoire partagée
        if len(memoire_cache) < 2:  # Pas assez d'exemples pour entraîner
            return
        questions = [item["question"] for item in memoire_cache]  # Extraction questions
        responses = [item["response"] for item in memoire_cache]  # Extraction réponses

    with torch.no_grad():  # Pas de gradient pendant l'encodage embeddings
        # Encodage questions en tenseurs GPU
        q_embed = model.encode(questions, convert_to_tensor=True).to(device)
        # Encodage réponses en tenseurs GPU
        r_embed = model.encode(responses, convert_to_tensor=True).to(device)

    nn_model.train()  # Mode entraînement
    losses = []  # Liste pour stocker les pertes par epoch

    for epoch in range(epochs):
        optimizer.zero_grad()  # Remise à zéro des gradients
        with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):  # Mixed precision pour GPU
            pred = nn_model(q_embed)  # Prédictions du modèle
            loss = loss_fn(pred, r_embed)  # Calcul de la perte MSE

        scaler.scale(loss).backward()  # Rétropropagation avec échelle
        torch.nn.utils.clip_grad_norm_(nn_model.parameters(), max_norm=1.0)  # Clip gradients pour stabilité
        scaler.step(optimizer)  # Optimisation du modèle
        scaler.update()  # Mise à jour du scaler
        scheduler.step()  # Mise à jour du learning rate

        loss_value = loss.item()  # Extraction valeur scalaire de la perte
        losses.append(loss_value)  # Ajout dans l'historique
        print(f"Epoch {epoch+1}/{epochs} - Loss: {loss_value:.4f}")

    save_model()  # Sauvegarde du modèle après entraînement

    if show_plot:  # Option pour afficher la courbe de perte
        plt.plot(range(1, epochs+1), losses, marker='o')
        plt.title("Courbe de perte")
        plt.xlabel("Épochs")
        plt.ylabel("Loss")
        plt.grid()
        plt.show()

# 📥 Ajouter une paire question/réponse et entraîner rapidement
def ajouter_qa(question, reponse):
    with lock:  # Verrou pour modifier la mémoire partagée
        memoire_cache.append({"question": question, "response": reponse})  # Ajout pair QA
    if len(memoire_cache) >= 2:
        train_nn_on_memory(epochs=2)  # Entraînement rapide sur la mémoire mise à jour
