import torch

from torch_geometric.data import Data

from app.graph.cif_parser import parse_cif_bytes
from app.graph.graph_features import atom_features
from app.graph.sparsifier import build_knn_edges

from app.core.config import settings


def cif_file_to_graph(cif_bytes: bytes, filename: str = "uploaded.cif"):
    structure = parse_cif_bytes(cif_bytes, filename)

    x_list = [atom_features(site) for site in structure]
    x = torch.tensor(x_list, dtype=torch.float)

    edge_index, edge_attr = build_knn_edges(
        structure=structure,
        K_NEIGHBORS=settings.K_NEIGHBORS,
    )

    graph = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
    )

    graph.num_atoms = len(structure)
    graph.num_edges_created = edge_index.shape[1]

    return graph
