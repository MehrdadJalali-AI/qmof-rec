import os
import torch
import torch.nn.functional as F

from torch_geometric.loader import DataLoader

from app.model import GraphSAGEClassifier
from app.graph_builder import cif_file_to_graph


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "material_classifier.pt")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


CLASS_NAMES = {
    0: "Conductor",
    1: "Semiconductor",
    2: "Insulator",
}


class MaterialPredictor:
    def __init__(self):
        self.model = GraphSAGEClassifier(
            in_channels=5,
            hidden_dim=64,
            num_classes=3,
        ).to(DEVICE)

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found: {MODEL_PATH}. "
                "Copy material_classifier.pt into backend/app/models/"
            )

        self.model.load_state_dict(
            torch.load(MODEL_PATH, map_location=DEVICE)
        )

        self.model.eval()

    def predict_from_cif(self, cif_bytes: bytes, filename: str):
        graph = cif_file_to_graph(cif_bytes, filename)

        loader = DataLoader([graph], batch_size=1, shuffle=False)

        batch = next(iter(loader))
        batch = batch.to(DEVICE)

        with torch.no_grad():
            logits = self.model(
                batch.x,
                batch.edge_index,
                batch.batch,
            )

            probs = F.softmax(logits, dim=1)
            pred_class = int(torch.argmax(probs, dim=1).item())
            confidence = float(probs[0, pred_class].item())

        class_probabilities = {
            CLASS_NAMES[i]: float(probs[0, i].item())
            for i in range(len(CLASS_NAMES))
        }

        return {
            "filename": filename,
            "predicted_class_id": pred_class,
            "predicted_material_type": CLASS_NAMES[pred_class],
            "confidence": confidence,
            "class_probabilities": class_probabilities,
            "graph_statistics": {
                "num_nodes_atoms": int(graph.num_nodes),
                "num_edges_sparse": int(graph.edge_index.shape[1]),
                "node_features": int(graph.x.shape[1]),
                "edge_features": int(graph.edge_attr.shape[1]),
                "sparsification_method": "k-nearest neighbors",
                "k_neighbors": 8,
            },
        }