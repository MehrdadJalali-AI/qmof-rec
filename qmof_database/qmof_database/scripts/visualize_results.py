import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import matplotlib.pyplot as plt


# ---------------- LOAD DATA ----------------

train_losses = torch.load(
    "../processed_graphs/train_losses.pt",
    weights_only=False
)

test_losses = torch.load(
    "../processed_graphs/test_losses.pt",
    weights_only=False
)

targets = torch.load(
    "../processed_graphs/targets.pt",
    weights_only=False
)

preds = torch.load(
    "../processed_graphs/preds.pt",
    weights_only=False
)


# ---------------- LOSS CURVE ----------------

plt.figure(figsize=(8, 5))

plt.plot(train_losses, label="Train Loss")
plt.plot(test_losses, label="Test Loss")

plt.xlabel("Epoch")
plt.ylabel("Loss")

plt.title("Training and Test Loss")

plt.legend()

plt.grid(True)

plt.show()


# ---------------- PREDICTION SCATTER ----------------

plt.figure(figsize=(6, 6))

plt.scatter(targets, preds)

min_val = min(min(targets), min(preds))
max_val = max(max(targets), max(preds))

plt.plot(
    [min_val, max_val],
    [min_val, max_val],
)

plt.xlabel("True Bandgap")
plt.ylabel("Predicted Bandgap")

plt.title("True vs Predicted Bandgap")

plt.grid(True)

plt.show()