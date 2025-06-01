import os
import torch
import torch.nn as nn
import torch.optim as optim
from sentence_transformers import SentenceTransformer
from app.memory import memoire_cache, lock
import matplotlib.pyplot as plt

# Embedding model
model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Bloc résiduel
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

# MLP avec attention simplifiée et résidus
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

# Initialisation
nn_model = ComplexNN().to(device)
optimizer = optim.AdamW(nn_model.parameters(), lr=1e-4, weight_decay=1e-5)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)
loss_fn = nn.MSELoss()
scaler = torch.cuda.amp.GradScaler(enabled=torch.cuda.is_available())

MODEL_PATH = "data/nn_model.pt"

# 💾 Sauvegarder le modèle
def save_model():
    torch.save({
        'model_state_dict': nn_model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
    }, MODEL_PATH)
    print(f"💾 Modèle sauvegardé dans {MODEL_PATH}")

# 📤 Charger le modèle s'il existe
def load_model():
    if os.path.exists(MODEL_PATH):
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        nn_model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print(f"✅ Modèle chargé depuis {MODEL_PATH}")
    else:
        print("🆕 Aucun modèle trouvé, nouveau modèle initialisé.")

# 📈 Entraînement principal
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
        with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
            pred = nn_model(q_embed)
            loss = loss_fn(pred, r_embed)

        scaler.scale(loss).backward()
        torch.nn.utils.clip_grad_norm_(nn_model.parameters(), max_norm=1.0)
        scaler.step(optimizer)
        scaler.update()
        scheduler.step()

        loss_value = loss.item()
        losses.append(loss_value)
        print(f"Epoch {epoch+1}/{epochs} - Loss: {loss_value:.4f}")

    save_model()

    if show_plot:
        plt.plot(range(1, epochs+1), losses, marker='o')
        plt.title("Courbe de perte")
        plt.xlabel("Épochs")
        plt.ylabel("Loss")
        plt.grid()
        plt.show()

# 📥 Ajouter une QA et entraîner automatiquement
def ajouter_qa(question, reponse):
    with lock:
        memoire_cache.append({"question": question, "response": reponse})
    if len(memoire_cache) >= 2:
        train_nn_on_memory(epochs=2)  # entraînement rapide
