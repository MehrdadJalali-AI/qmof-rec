import os
import torch
import torch.nn.functional as F

from torch_geometric.loader import DataLoader

from app.core.config import settings
from app.graph.graph_builder import cif_file_to_graph
from app.graph.topology import graph_statistics
from app.ml.models.graphsage import GraphSAGEClassifier


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class MaterialPredictor:
    def __init__(self):
        self.model = GraphSAGEClassifier(
            in_channels=5,
            hidden_dim=64,
            num_classes=3,
        ).to(DEVICE)

        if not os.path.exists(settings.MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {settings.MODEL_PATH}. "
                "Copy material_classifier.pt into backend/models/"
            )

        self.model.load_state_dict(
            torch.load(settings.MODEL_PATH, map_location=DEVICE)
        )

        self.model.eval()

    def predict_from_cif(self, cif_bytes: bytes, filename: str):
        graph = cif_file_to_graph(cif_bytes, filename)

        loader = DataLoader([graph], batch_size=1, shuffle=False)
        batch = next(iter(loader)).to(DEVICE)

        with torch.no_grad():
            logits = self.model(batch.x, batch.edge_index, batch.batch)
            probs = F.softmax(logits, dim=1)

            pred_class = int(torch.argmax(probs, dim=1).item())
            confidence = float(probs[0, pred_class].item())

        class_probabilities = {
            settings.CLASS_NAMES[i]: float(probs[0, i].item())
            for i in settings.CLASS_NAMES
        }

        stats = graph_statistics(graph)
        stats["sparsification_method"] = "k-nearest neighbors"
        stats["k_neighbors"] = settings.K_NEIGHBORS

        return {
            "filename": filename,
            "predicted_class_id": pred_class,
            "predicted_material_type": settings.CLASS_NAMES[pred_class],
            "confidence": confidence,
            "class_probabilities": class_probabilities,
            "graph_statistics": stats,
        }