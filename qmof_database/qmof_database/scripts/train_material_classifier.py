import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn.functional as F

from torch.nn import Linear
from torch_geometric.loader import DataLoader
from torch_geometric.nn import SAGEConv, global_mean_pool

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


# ---------------- SETTINGS ----------------
GRAPH_PATH = "../processed_graphs/qmof_sparse_classification_graphs.pt"

BATCH_SIZE = 16
HIDDEN_DIM = 64
LEARNING_RATE = 0.001
EPOCHS = 30
NUM_CLASSES = 3

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# ------------------------------------------


CLASS_NAMES = {
    0: "Conductor",
    1: "Semiconductor",
    2: "Insulator",
}


graphs = torch.load(GRAPH_PATH, weights_only=False)

print(f"\nTotal graphs loaded: {len(graphs)}")


train_graphs, test_graphs = train_test_split(
    graphs,
    test_size=0.2,
    random_state=42,
    stratify=[int(g.y.item()) for g in graphs],
)

print(f"Train graphs: {len(train_graphs)}")
print(f"Test graphs: {len(test_graphs)}")


train_loader = DataLoader(
    train_graphs,
    batch_size=BATCH_SIZE,
    shuffle=True,
)

test_loader = DataLoader(
    test_graphs,
    batch_size=BATCH_SIZE,
    shuffle=False,
)


class GraphSAGEClassifier(torch.nn.Module):
    def __init__(self, in_channels, hidden_dim, num_classes):
        super().__init__()

        self.conv1 = SAGEConv(in_channels, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)

        self.lin1 = Linear(hidden_dim, hidden_dim)
        self.lin2 = Linear(hidden_dim, num_classes)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index)
        x = F.relu(x)

        x = self.conv2(x, edge_index)
        x = F.relu(x)

        # Graph-level embedding
        x = global_mean_pool(x, batch)

        x = self.lin1(x)
        x = F.relu(x)

        out = self.lin2(x)

        return out


sample_graph = graphs[0]
in_channels = sample_graph.x.shape[1]

model = GraphSAGEClassifier(
    in_channels=in_channels,
    hidden_dim=HIDDEN_DIM,
    num_classes=NUM_CLASSES,
).to(DEVICE)

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE,
)

criterion = torch.nn.CrossEntropyLoss()

print("\nModel:")
print(model)


train_losses = []
test_losses = []
test_accuracies = []


def train():
    model.train()

    total_loss = 0

    for batch in train_loader:
        batch = batch.to(DEVICE)

        optimizer.zero_grad()

        out = model(
            batch.x,
            batch.edge_index,
            batch.batch,
        )

        loss = criterion(
            out,
            batch.y.view(-1),
        )

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(train_loader)


def evaluate(loader):
    model.eval()

    total_loss = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(DEVICE)

            out = model(
                batch.x,
                batch.edge_index,
                batch.batch,
            )

            loss = criterion(
                out,
                batch.y.view(-1),
            )

            total_loss += loss.item()

            preds = out.argmax(dim=1)

            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(batch.y.view(-1).cpu().numpy())

    avg_loss = total_loss / len(loader)

    acc = accuracy_score(all_targets, all_preds)
    precision = precision_score(all_targets, all_preds, average="weighted", zero_division=0)
    recall = recall_score(all_targets, all_preds, average="weighted", zero_division=0)
    f1 = f1_score(all_targets, all_preds, average="weighted", zero_division=0)

    cm = confusion_matrix(all_targets, all_preds)

    return avg_loss, acc, precision, recall, f1, cm, all_targets, all_preds


print("\nStarting material classification training...\n")

for epoch in range(1, EPOCHS + 1):
    train_loss = train()

    (
        test_loss,
        acc,
        precision,
        recall,
        f1,
        cm,
        targets,
        preds,
    ) = evaluate(test_loader)

    train_losses.append(train_loss)
    test_losses.append(test_loss)
    test_accuracies.append(acc)

    print(
        f"Epoch {epoch:03d} | "
        f"Train Loss: {train_loss:.4f} | "
        f"Test Loss: {test_loss:.4f} | "
        f"Acc: {acc:.4f} | "
        f"Precision: {precision:.4f} | "
        f"Recall: {recall:.4f} | "
        f"F1: {f1:.4f}"
    )


print("\nFinal Confusion Matrix:")
print(cm)

torch.save(model.state_dict(), "../processed_graphs/material_classifier.pt")

torch.save(train_losses, "../processed_graphs/classifier_train_losses.pt")
torch.save(test_losses, "../processed_graphs/classifier_test_losses.pt")
torch.save(test_accuracies, "../processed_graphs/classifier_test_accuracies.pt")
torch.save(targets, "../processed_graphs/classifier_targets.pt")
torch.save(preds, "../processed_graphs/classifier_preds.pt")

print("\nTraining completed.")
print("Model saved to ../processed_graphs/material_classifier.pt")