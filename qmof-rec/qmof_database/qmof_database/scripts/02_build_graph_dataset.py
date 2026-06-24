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
OUTPUT_FILE = "qmof_graphs.pt"

TARGET_COLUMN = "outputs.hse06.bandgap"

GLOBAL_FEATURE_COLUMNS = [
    "info.natoms",
    "info.pld",
    "info.lcd",
    "info.density",
    "info.volume",
    "info.symmetry.spacegroup_number",
    "info.synthesized",
]

DISTANCE_CUTOFF = 4.5
MAX_GRAPHS = 500
# ------------------------------------------


def safe_float(value, default=0.0):
    if pd.isna(value):
        return default

    if isinstance(value, bool):
        return float(value)

    try:
        return float(value)
    except Exception:
        return default


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


def build_edges_from_distance(structure, cutoff=4.5):
    edge_index = []
    edge_attr = []

    num_atoms = len(structure)

    for i in range(num_atoms):
        for j in range(i + 1, num_atoms):
            try:
                distance = structure.get_distance(i, j)
            except Exception:
                continue

            if distance <= cutoff:
                edge_index.append([i, j])
                edge_index.append([j, i])

                edge_attr.append([distance])
                edge_attr.append([distance])

    if len(edge_index) == 0:
        return None, None

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_attr, dtype=torch.float)

    return edge_index, edge_attr


def build_graph_from_row(row, cif_folder_path):
    qmof_id = row["qmof_id"]
    cif_path = os.path.join(cif_folder_path, f"{qmof_id}.cif")

    if not os.path.exists(cif_path):
        print(f"[Missing CIF] {cif_path}")
        return None

    try:
        structure = Structure.from_file(cif_path)
    except Exception as e:
        print(f"[CIF Read Error] {qmof_id}: {e}")
        return None

    # Node features
    x_list = []
    for site in structure:
        try:
            x_list.append(atom_features(site))
        except Exception:
            continue

    if len(x_list) == 0:
        print(f"[No Nodes] {qmof_id}")
        return None

    x = torch.tensor(x_list, dtype=torch.float)

    # Edges
    edge_index, edge_attr = build_edges_from_distance(
        structure=structure,
        cutoff=DISTANCE_CUTOFF,
    )

    if edge_index is None:
        print(f"[No Edges] {qmof_id}")
        return None

    # Target
    y_value = safe_float(row[TARGET_COLUMN])
    y = torch.tensor([y_value], dtype=torch.float)

    # Global graph-level features
    global_features = []
    for col in GLOBAL_FEATURE_COLUMNS:
        if col in row.index:
            global_features.append(safe_float(row[col]))
        else:
            global_features.append(0.0)

    global_features = torch.tensor(global_features, dtype=torch.float).view(1, -1)

    # PyTorch Geometric graph object
    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=y,
    )

    data.qmof_id = qmof_id
    data.global_features = global_features

    return data


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Load CSV
    df = pd.read_csv(CSV_PATH, low_memory=False)

    print(f"Original CSV rows: {len(df)}")

    # Keep only rows with target
    df = df.dropna(subset=[TARGET_COLUMN])

    print(f"Rows after removing missing target: {len(df)}")

    # Match only rows whose CIF files exist
    available_cifs = {
        filename.replace(".cif", "")
        for filename in os.listdir(CIF_FOLDER_PATH)
        if filename.endswith(".cif")
    }

    print(f"Available CIF files: {len(available_cifs)}")

    df = df[df["qmof_id"].isin(available_cifs)]

    print(f"Rows with matching CIF files: {len(df)}")

    if MAX_GRAPHS is not None:
        df = df.head(MAX_GRAPHS)

    graph_list = []
    failed = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        qmof_id = row["qmof_id"]

        graph = build_graph_from_row(row, CIF_FOLDER_PATH)

        if graph is None:
            failed.append(qmof_id)
        else:
            graph_list.append(graph)

    output_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)
    torch.save(graph_list, output_path)

    print("\nGraph dataset creation completed.")
    print(f"Saved graphs: {len(graph_list)}")
    print(f"Failed graphs: {len(failed)}")
    print(f"Output file: {output_path}")

    if len(failed) > 0:
        print("\nFailed QMOF IDs:")
        print(failed[:20])

    if len(graph_list) > 0:
        sample = graph_list[0]

        print("\nSample graph:")
        print(sample)
        print("QMOF ID:", sample.qmof_id)
        print("Node feature shape:", sample.x.shape)
        print("Edge index shape:", sample.edge_index.shape)
        print("Edge feature shape:", sample.edge_attr.shape)
        print("Global features shape:", sample.global_features.shape)
        print("Target y:", sample.y)


if __name__ == "__main__":
    main()