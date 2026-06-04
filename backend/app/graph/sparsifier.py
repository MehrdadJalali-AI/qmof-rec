import torch

from pymatgen.core import Structure

from app.core.config import settings


def build_knn_edges(
    structure: Structure,
    k: int = None,
):

    if k is None:
        k = settings.K_NEIGHBORS

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

                distances.append(
                    (j, dist)
                )

            except Exception:
                continue

        distances = sorted(
            distances,
            key=lambda x: x[1],
        )

        nearest_neighbors = distances[:k]

        for j, dist in nearest_neighbors:

            edge_index.append([i, j])

            edge_attr.append([dist])

    if len(edge_index) == 0:
        raise ValueError(
            "No graph edges were created from CIF structure."
        )

    edge_index = torch.tensor(
        edge_index,
        dtype=torch.long,
    ).t().contiguous()

    edge_attr = torch.tensor(
        edge_attr,
        dtype=torch.float,
    )

    return edge_index, edge_attr