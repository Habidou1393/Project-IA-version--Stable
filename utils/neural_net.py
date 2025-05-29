import torch
import torch.nn as nn
import torch.optim as optim
from app.memory import memoire_cache, lock
from sentence_transformers import SentenceTransformer

# Modèle d'embedding
model = SentenceTransformer('distiluse-base-multilingual-cased-v1')

# Réseau de neurones optimisé
class ImprovedNN(nn.Module):
    def __init__(self, input_dim=512, hidden_dim=256, output_dim=512):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x): return self.layers(x)

# Initialisation
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
nn_model = ImprovedNN().to(device)
optimizer = optim.AdamW(nn_model.parameters(), lr=1e-3, weight_decay=1e-4)
loss_fn = nn.MSELoss()

# Entraînement
def train_nn_on_memory(epochs=10):
    with lock:
        if len(memoire_cache) < 2:
            return
        questions = [item["question"] for item in memoire_cache]
        responses = [item["response"] for item in memoire_cache]

    with torch.no_grad():
        q_embed = model.encode(questions, convert_to_tensor=True).to(device)
        r_embed = model.encode(responses, convert_to_tensor=True).to(device)

    nn_model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        pred = nn_model(q_embed)
        loss = loss_fn(pred, r_embed)
        loss.backward()
        optimizer.step()
        print(f"Epoch {epoch+1}/{epochs} - Loss: {loss.item():.4f}")
