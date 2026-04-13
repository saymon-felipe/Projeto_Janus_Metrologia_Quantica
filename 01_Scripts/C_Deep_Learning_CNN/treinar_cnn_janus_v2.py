import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.model_selection import train_test_split

X = np.load("X_janus_v2.npy") # Shape: (Amostras, 2, 5, 8)
y = np.load("y_janus_v2.npy")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Converter para tensores
X_train, y_train = torch.FloatTensor(X_train), torch.FloatTensor(y_train).view(-1, 1)
X_test, y_test = torch.FloatTensor(X_test), torch.FloatTensor(y_test).view(-1, 1)

class JanusCNN_V2(nn.Module):
    def __init__(self):
        super(JanusCNN_V2, self).__init__()
        self.conv1 = nn.Conv2d(2, 32, kernel_size=2)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=2)
        self.fc1 = nn.Linear(64 * 1 * 2, 32)
        self.dropout = nn.Dropout(0.4)
        self.fc2 = nn.Linear(32, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = torch.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.sigmoid(self.fc2(x))
        return x

model = JanusCNN_V2()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.0005, weight_decay=1e-4)

print("[*] A treinar CNN Janus V2 (Multicanal)...")
for epoch in range(150): 
    model.train()
    optimizer.zero_grad()
    outputs = model(X_train)
    loss = criterion(outputs, y_train)
    loss.backward()
    optimizer.step()
    
    if (epoch+1) % 25 == 0:
        print(f"Epoch [{epoch+1}/150], Loss: {loss.item():.4f}")

model.eval()
with torch.no_grad():
    acc = (model(X_test).round().eq(y_test).sum().float() / y_test.shape[0]).item()
    print(f"\n🏆 PRECISÃO FINAL (MULTICANAL): {acc * 100:.2f}%")