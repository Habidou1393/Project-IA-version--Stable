import torch
import torch.nn as nn
import torch.optim as optim
from app.memory import memoire_cache, lock
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('distiluse-base-multilingual-cased-v1')

class SimpleNN(nn.Module):
    def __init__(self, input_size=512, hidden_size=128, output_size=512):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        return self.fc2(self.relu(self.fc1(x)))

nn_model = SimpleNN()
optimizer = optim.Adam(nn_model.parameters(), lr=0.001)
loss_fn = nn.MSELoss()

def train_nn_on_memory(epochs=10):
    with lock:
        if len(memoire_cache) < 2:
            return
        questions = [item["question"] for item in memoire_cache]
        responses = [item["response"] for item in memoire_cache]

    q_embeddings = model.encode(questions, convert_to_tensor=True)
    r_embeddings = model.encode(responses, convert_to_tensor=True)

    nn_model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        pred = nn_model(q_embeddings)
        loss = loss_fn(pred, r_embeddings)
        loss.backward()
        optimizer.step()
