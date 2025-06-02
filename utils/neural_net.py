import os  # Gestion des fichiers
import torch  # Framework de deep learning
import torch.nn as nn  # Modules pour construire les réseaux
import torch.optim as optim  # Optimisation des poids
from sentence_transformers import SentenceTransformer  # Embeddings de phrases
from app.memory import memoire_cache, lock  # Mémoire partagée et verrou pour synchronisation
import matplotlib.pyplot as plt  # Tracés de courbes

# 🔠 Modèle multilingue d'embedding (512 dimensions)
model = SentenceTransformer('distiluse-base-multilingual-cased-v1')

# ⚙️ Détection de l'appareil : GPU si dispo, sinon CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"✅ Appareil utilisé : {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU uniquement'})")

# 🔁 Bloc résiduel (comme dans ResNet/Transformers)
class ResidualBlock(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.block = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, dim),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(dim, dim),
        )

    def forward(self, x):
        return x + self.block(x)

# 🧠 Réseau de neurones principal avec attention + résidus
class ComplexNN(nn.Module):
    def __init__(self, input_dim=512, hidden_dim=1024, output_dim=512, num_blocks=4):
        super().__init__()
        self.input_layer = nn.Linear(input_dim, hidden_dim)
        self.residual_blocks = nn.Sequential(*[ResidualBlock(hidden_dim) for _ in range(num_blocks)])
        self.attention = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=8, batch_first=True)
        self.output_layer = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.input_layer(x)
        x = x.unsqueeze(1)
        attn_output, _ = self.attention(x, x, x)
        x = self.residual_blocks(attn_output)
        x = x.squeeze(1)
        return self.output_layer(x)

# 🚀 Initialisation du modèle
nn_model = ComplexNN().to(device)

# 🔧 Optimiseur AdamW + scheduler de type CosineAnnealing
optimizer = optim.AdamW(nn_model.parameters(), lr=1e-4, weight_decay=1e-5)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)
loss_fn = nn.MSELoss()

# 🔄 Activation AMP uniquement sur GPU
use_amp = device.type == 'cuda'
scaler = torch.cuda.amp.GradScaler() if use_amp else None

# 📁 Chemin de sauvegarde
MODEL_PATH = "data/nn_model.pt"

# 💾 Sauvegarde modèle + optimiseur
def save_model():
    torch.save({
        'model_state_dict': nn_model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
    }, MODEL_PATH)
    print(f"💾 Modèle sauvegardé dans {MODEL_PATH}")

# 📤 Chargement du modèle
def load_model():
    if os.path.exists(MODEL_PATH):
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        nn_model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print(f"✅ Modèle chargé depuis {MODEL_PATH}")
    else:
        print("🆕 Aucun modèle trouvé, nouveau modèle initialisé.")

# 📈 Entraînement du modèle sur la mémoire (Q/A)
def train_nn_on_memory(epochs=10, show_plot=False):
    with lock:
        if len(memoire_cache) < 2:
            return
        questions = [item["question"] for item in memoire_cache]
        responses = [item["response"] for item in memoire_cache]

    with torch.no_grad():
        q_embed = model.encode(questions, convert_to_tensor=True).to(device)
        r_embed = model.encode(responses, convert_to_tensor=True).to(device)

    nn_model.train()
    losses = []

    for epoch in range(epochs):
        optimizer.zero_grad()

        if use_amp:
            with torch.cuda.amp.autocast():
                pred = nn_model(q_embed)
                loss = loss_fn(pred, r_embed)
            scaler.scale(loss).backward()
            torch.nn.utils.clip_grad_norm_(nn_model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            pred = nn_model(q_embed)
            loss = loss_fn(pred, r_embed)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(nn_model.parameters(), max_norm=1.0)
            optimizer.step()

        scheduler.step()
        loss_value = loss.item()
        losses.append(loss_value)
        print(f"📉 Epoch {epoch+1}/{epochs} - Loss: {loss_value:.4f}")

    save_model()

    if show_plot:
        plt.plot(range(1, epochs+1), losses, marker='o')
        plt.title("Courbe de perte")
        plt.xlabel("Épochs")
        plt.ylabel("Loss")
        plt.grid()
        plt.show()

# ➕ Ajout d'une question/réponse à la mémoire + apprentissage rapide
def ajouter_qa(question, reponse):
    with lock:
        memoire_cache.append({"question": question, "response": reponse})
    if len(memoire_cache) >= 2:
        train_nn_on_memory(epochs=2)
