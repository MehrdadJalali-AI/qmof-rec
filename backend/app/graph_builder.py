import os
import tempfile
import torch

from pymatgen.core import Structure
from torch_geometric.data import Data


K_NEIGHBORS = 8


def atom_features(site):
    element = site.specie

    atomic_number = float(element.Z)
    atomic_mass = float(element.atomic_mass)
    row = float(element.row)

    group = element.group
    group = float(group) if group is not None else 0.0

    electronegativity = element.X
    electronegativity = float(electronegativity) if electronegativity is not None else 0.0

    return [
        atomic_number,
        atomic_mass,
        row,
        group,
        electronegativity,
    ]


def build_knn_edges(structure: Structure, k: int = K_NEIGHBORS):
    edge_index = []
    edge_attr = []

    num_atoms = len(structure)

    for i in range(num_atoms):
        distances = []

        for j in range(num_atoms):
            if i == j:
                continue

            try:
                dist = structure.get_distance(i, j)
                distances.append((j, dist))
            except Exception:
                continue

        distances = sorted(distances, key=lambda x: x[1])
        nearest_neighbors = distances[:k]

        for j, dist in nearest_neighbors:
            edge_index.append([i, j])
            edge_attr.append([dist])

    if len(edge_index) == 0:
        raise ValueError("No graph edges were created from CIF structure.")

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_attr, dtype=torch.float)

    return edge_index, edge_attr


def cif_file_to_graph(cif_bytes: bytes, filename: str = "uploaded.cif"):
    with tempfile.TemporaryDirectory() as tmpdir:
        cif_path = os.path.join(tmpdir, filename)

        with open(cif_path, "wb") as f:
            f.write(cif_bytes)

        structure = Structure.from_file(cif_path)

    x_list = []

    for site in structure:
        x_list.append(atom_features(site))

    x = torch.tensor(x_list, dtype=torch.float)

    edge_index, edge_attr = build_knn_edges(structure, k=K_NEIGHBORS)

    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
    )

    data.num_atoms = len(structure)
    data.num_edges_created = edge_index.shape[1]

    return data