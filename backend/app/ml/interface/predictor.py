import os
import logging

import torch
import torch.nn.functional as F

from torch_geometric.loader import DataLoader

from app.core.config import settings
from app.graph.graph_builder import cif_file_to_graph
from app.graph.topology import graph_statistics
from app.ml.models.graphsage import GraphSAGEClassifier

logger = logging.getLogger("qmof.ml")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class MaterialPredictor:
    """
    Wraps the GraphSAGE material classifier.

    The model weights are loaded lazily on first use, rather than at import
    time, so that importing this module (or starting the app) does not fail
    if MODEL_PATH is missing - only requests that actually need prediction
    will fail, with a clear error.
    """

    def __init__(self):
        self._model = None

    def _load_model(self):
        if not os.path.exists(settings.MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at '{settings.MODEL_PATH}'. "
                "Set MODEL_PATH to a valid material_classifier.pt file."
            )

        model = GraphSAGEClassifier(
            in_channels=5,
            hidden_dim=64,
            num_classes=3,
        ).to(DEVICE)

        model.load_state_dict(torch.load(settings.MODEL_PATH, map_location=DEVICE))
        model.eval()

        logger.info("Loaded material classifier from %s", settings.MODEL_PATH)
        return model

    @property
    def model(self):
        if self._model is None:
            self._model = self._load_model()
        return self._model

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
