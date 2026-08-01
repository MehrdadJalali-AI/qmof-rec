import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn.functional as F

from torch.nn import Linear
from torch_geometric.loader import DataLoader
from torch_geometric.nn import SAGEConv, global_mean_pool

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# ---------------- SETTINGS ----------------
GRAPH_PATH = "../processed_graphs/qmof_graphs.pt"

BATCH_SIZE = 8
HIDDEN_DIM = 64
LEARNING_RATE = 0.001
EPOCHS = 20

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)
# ------------------------------------------


# ---------------- LOAD DATASET ----------------
graphs = torch.load(
    GRAPH_PATH,
    weights_only=False,
)

print(f"\nTotal graphs loaded: {len(graphs)}")


# ---------------- TRAIN / TEST SPLIT ----------------
train_graphs, test_graphs = train_test_split(
    graphs,
    test_size=0.2,
    random_state=42,
)

print(f"Train graphs: {len(train_graphs)}")
print(f"Test graphs: {len(test_graphs)}")


# ---------------- DATALOADERS ----------------
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


# ---------------- GRAPH SAGE MODEL ----------------
class GraphSAGE(torch.nn.Module):

    def __init__(self, in_channels, hidden_dim):
        super().__init__()

        # GraphSAGE layers
        self.conv1 = SAGEConv(
            in_channels,
            hidden_dim,
        )

        self.conv2 = SAGEConv(
            hidden_dim,
            hidden_dim,
        )

        # Final regression layer
        self.lin = Linear(
            hidden_dim,
            1,
        )

    def forward(
        self,
        x,
        edge_index,
        batch,
    ):

        # First GraphSAGE layer
        x = self.conv1(
            x,
            edge_index,
        )

        x = F.relu(x)

        # Second GraphSAGE layer
        x = self.conv2(
            x,
            edge_index,
        )

        x = F.relu(x)

        # Pool node embeddings -> graph embedding
        x = global_mean_pool(
            x,
            batch,
        )

        # Final prediction
        x = self.lin(x)

        return x


# ---------------- MODEL ----------------
sample_graph = graphs[0]

in_channels = sample_graph.x.shape[1]

model = GraphSAGE(
    in_channels=in_channels,
    hidden_dim=HIDDEN_DIM,
).to(DEVICE)

print("\nModel:")
print(model)


# ---------------- OPTIMIZER ----------------
optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE,
)

criterion = torch.nn.MSELoss()


# ---------------- STORE LOSSES ----------------
train_losses = []
test_losses = []


# ---------------- TRAIN FUNCTION ----------------
def train():

    model.train()

    total_loss = 0

    for batch in train_loader:

        batch = batch.to(DEVICE)

        optimizer.zero_grad()

        pred = model(
            batch.x,
            batch.edge_index,
            batch.batch,
        )

        loss = criterion(
            pred.squeeze(),
            batch.y.squeeze(),
        )

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(train_loader)


# ---------------- EVALUATION FUNCTION ----------------
def evaluate(loader):

    model.eval()

    total_loss = 0

    all_preds = []
    all_targets = []

    with torch.no_grad():

        for batch in loader:

            batch = batch.to(DEVICE)

            pred = model(
                batch.x,
                batch.edge_index,
                batch.batch,
            )

            loss = criterion(
                pred.squeeze(),
                batch.y.squeeze(),
            )

            total_loss += loss.item()

            # Save predictions
            all_preds.extend(
                pred.squeeze().cpu().numpy().flatten()
            )

            # Save targets
            all_targets.extend(
                batch.y.squeeze().cpu().numpy().flatten()
            )

    avg_loss = total_loss / len(loader)

    # Metrics
    mae = mean_absolute_error(
        all_targets,
        all_preds,
    )

    rmse = mean_squared_error(
        all_targets,
        all_preds,
    ) ** 0.5

    r2 = r2_score(
        all_targets,
        all_preds,
    )

    return (
        avg_loss,
        mae,
        rmse,
        r2,
        all_targets,
        all_preds,
    )


# ---------------- TRAINING LOOP ----------------
print("\nStarting training...\n")

for epoch in range(1, EPOCHS + 1):

    train_loss = train()

    (
        test_loss,
        mae,
        rmse,
        r2,
        targets,
        preds,
    ) = evaluate(test_loader)

    # Save losses
    train_losses.append(train_loss)
    test_losses.append(test_loss)

    print(
        f"Epoch {epoch:03d} | "
        f"Train Loss: {train_loss:.4f} | "
        f"Test Loss: {test_loss:.4f} | "
        f"MAE: {mae:.4f} | "
        f"RMSE: {rmse:.4f} | "
        f"R2: {r2:.4f}"
    )


# ---------------- SAVE MODEL ----------------
torch.save(
    model.state_dict(),
    "../processed_graphs/graphsage_model.pt",
)

# ---------------- SAVE VISUALIZATION DATA ----------------
torch.save(
    train_losses,
    "../processed_graphs/train_losses.pt",
)

torch.save(
    test_losses,
    "../processed_graphs/test_losses.pt",
)

torch.save(
    targets,
    "../processed_graphs/targets.pt",
)

torch.save(
    preds,
    "../processed_graphs/preds.pt",
)

print("\nTraining completed.")

print("\nModel saved to:")
print("../processed_graphs/graphsage_model.pt")

print("\nVisualization files saved:")
print("../processed_graphs/train_losses.pt")
print("../processed_graphs/test_losses.pt")
print("../processed_graphs/targets.pt")
print("../processed_graphs/preds.pt")