import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import pandas as pd
import torch
from tqdm import tqdm

from pymatgen.core import Structure
from torch_geometric.data import Data


# ---------------- SETTINGS ----------------
CSV_PATH = "../qmof.csv"
CIF_FOLDER_PATH = "../relaxed_structures"
OUTPUT_FOLDER = "../processed_graphs"
OUTPUT_FILE = "qmof_sparse_classification_graphs.pt"

TARGET_COLUMN = "outputs.hse06.bandgap"

MAX_GRAPHS = 500

# Sparse graph setting
K_NEIGHBORS = 8
# ------------------------------------------


def bandgap_to_class(bandgap):
    """
    Converts bandgap value into material type class.

    0 = conductor
    1 = semiconductor
    2 = insulator
    """
    if bandgap < 0.5:
        return 0
    elif bandgap < 2.0:
        return 1
    else:
        return 2


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


def build_knn_edges(structure, k=8):
    """
    Sparse topology-aware edge construction.

    For each atom:
    - compute distance to all other atoms
    - keep only k nearest neighbors
    """

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

        # Sort neighbors by distance
        distances = sorted(distances, key=lambda x: x[1])

        # Keep only k nearest neighbors
        nearest_neighbors = distances[:k]

        for j, dist in nearest_neighbors:
            edge_index.append([i, j])
            edge_attr.append([dist])

    if len(edge_index) == 0:
        return None, None

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_attr, dtype=torch.float)

    return edge_index, edge_attr


def build_graph_from_row(row):
    qmof_id = row["qmof_id"]
    cif_path = os.path.join(CIF_FOLDER_PATH, f"{qmof_id}.cif")

    if not os.path.exists(cif_path):
        return None

    try:
        structure = Structure.from_file(cif_path)
    except Exception:
        return None

    # Node features
    x_list = []

    for site in structure:
        try:
            x_list.append(atom_features(site))
        except Exception:
            continue

    if len(x_list) == 0:
        return None

    x = torch.tensor(x_list, dtype=torch.float)

    # Sparse edges
    edge_index, edge_attr = build_knn_edges(
        structure=structure,
        k=K_NEIGHBORS,
    )

    if edge_index is None:
        return None

    # Classification label
    bandgap = float(row[TARGET_COLUMN])
    label = bandgap_to_class(bandgap)

    y = torch.tensor([label], dtype=torch.long)

    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=y,
    )

    data.qmof_id = qmof_id
    data.bandgap = torch.tensor([bandgap], dtype=torch.float)
    data.num_original_atoms = len(structure)

    return data


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    df = pd.read_csv(CSV_PATH, low_memory=False)

    print(f"Original rows: {len(df)}")

    df = df.dropna(subset=[TARGET_COLUMN])

    print(f"Rows with target bandgap: {len(df)}")

    available_cifs = {
        f.replace(".cif", "")
        for f in os.listdir(CIF_FOLDER_PATH)
        if f.endswith(".cif")
    }

    df = df[df["qmof_id"].isin(available_cifs)]

    print(f"Rows with matching CIF files: {len(df)}")

    if MAX_GRAPHS is not None:
        df = df.head(MAX_GRAPHS)

    graphs = []
    failed = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        g = build_graph_from_row(row)

        if g is None:
            failed.append(row["qmof_id"])
        else:
            graphs.append(g)

    output_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)
    torch.save(graphs, output_path)

    print("\nSparse classification dataset created.")
    print(f"Saved graphs: {len(graphs)}")
    print(f"Failed graphs: {len(failed)}")
    print(f"Output: {output_path}")

    if len(graphs) > 0:
        sample = graphs[0]
        print("\nSample graph:")
        print(sample)
        print("QMOF ID:", sample.qmof_id)
        print("Bandgap:", sample.bandgap)
        print("Class label:", sample.y)
        print("Nodes:", sample.num_nodes)
        print("Edges:", sample.num_edges)


if __name__ == "__main__":
    main()