from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/qmof-matplotlib")

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import GATConv, SAGEConv


def _safe_float(value, default=np.nan) -> float:
    try:
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except Exception:
        return default


def _formula_tokens(formula: str) -> List[str]:
    return re.findall(r"[A-Z][a-z]?", formula or "")


def _load_materials(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _feature_matrix(materials: List[Dict], vocab_size: int = 24) -> Tuple[np.ndarray, List[str]]:
    token_counts: Dict[str, int] = {}
    tokenized = []
    for material in materials:
        tokens = _formula_tokens(str(material.get("formula", "")))
        tokenized.append(tokens)
        for token in tokens:
            token_counts[token] = token_counts.get(token, 0) + 1
    vocab = [token for token, _ in sorted(token_counts.items(), key=lambda x: x[1], reverse=True)[:vocab_size]]
    rows = []
    for tokens, material in zip(tokenized, materials):
        total = max(1, len(tokens))
        counts = [tokens.count(token) / total for token in vocab]
        atom_count = min(total / 100.0, 1.0)
        has_band_gap = 0.0 if math.isnan(_safe_float(material.get("band_gap"))) else 1.0
        rows.append(counts + [atom_count, has_band_gap])
    return np.asarray(rows, dtype=np.float32), vocab + ["atom_count_scaled", "has_band_gap"]


def _build_knn_graph(features: np.ndarray, k: int) -> np.ndarray:
    nbrs = NearestNeighbors(n_neighbors=k + 1, metric="cosine")
    nbrs.fit(features)
    indices = nbrs.kneighbors(features, return_distance=False)
    edges = []
    for src, neigh in enumerate(indices):
        for dst in neigh[1:]:
            edges.append((src, int(dst)))
            edges.append((int(dst), src))
    edge_index = np.asarray(sorted(set(edges)), dtype=np.int64).T
    return edge_index


def _component_count(edge_index: np.ndarray, n_nodes: int) -> int:
    adjacency = [[] for _ in range(n_nodes)]
    for src, dst in edge_index.T:
        adjacency[int(src)].append(int(dst))
    visited = np.zeros(n_nodes, dtype=bool)
    components = 0
    for start in range(n_nodes):
        if visited[start]:
            continue
        components += 1
        stack = [start]
        visited[start] = True
        while stack:
            node = stack.pop()
            for nb in adjacency[node]:
                if not visited[nb]:
                    visited[nb] = True
                    stack.append(nb)
    return components


class SAGERegressor(nn.Module):
    def __init__(self, in_channels: int, hidden_dim: int):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.head = nn.Linear(hidden_dim, 1)

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = F.relu(self.conv2(x, edge_index))
        return self.head(x).squeeze(-1)

    def embeddings(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        return F.relu(self.conv2(x, edge_index))


class GATRegressor(nn.Module):
    def __init__(self, in_channels: int, hidden_dim: int):
        super().__init__()
        heads = 2
        self.conv1 = GATConv(in_channels, hidden_dim, heads=heads, concat=True)
        self.conv2 = GATConv(hidden_dim * heads, hidden_dim, heads=1, concat=True)
        self.head = nn.Linear(hidden_dim, 1)

    def forward(self, x, edge_index):
        x = F.elu(self.conv1(x, edge_index))
        x = F.elu(self.conv2(x, edge_index))
        return self.head(x).squeeze(-1)

    def embeddings(self, x, edge_index):
        x = F.elu(self.conv1(x, edge_index))
        return F.elu(self.conv2(x, edge_index))


def _split_indices(available: np.ndarray, seed: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_idx, temp_idx = train_test_split(available, test_size=0.30, random_state=seed)
    val_idx, test_idx = train_test_split(temp_idx, test_size=0.50, random_state=seed)
    return train_idx, val_idx, test_idx


def _train_eval(
    model_name: str,
    model: nn.Module,
    features: np.ndarray,
    edge_index_np: np.ndarray,
    targets: np.ndarray,
    available: np.ndarray,
    seed: int,
    epochs: int,
    lr: float,
) -> Tuple[Dict, np.ndarray]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    train_idx, val_idx, test_idx = _split_indices(available, seed)
    scaler = StandardScaler()
    target_scaled = np.full_like(targets, np.nan, dtype=np.float32)
    target_scaled[train_idx] = scaler.fit_transform(targets[train_idx].reshape(-1, 1)).ravel()
    target_scaled[val_idx] = scaler.transform(targets[val_idx].reshape(-1, 1)).ravel()
    target_scaled[test_idx] = scaler.transform(targets[test_idx].reshape(-1, 1)).ravel()

    x = torch.tensor(features, dtype=torch.float32)
    edge_index = torch.tensor(edge_index_np, dtype=torch.long)
    y = torch.tensor(np.nan_to_num(target_scaled, nan=0.0), dtype=torch.float32)
    train_t = torch.tensor(train_idx, dtype=torch.long)
    val_t = torch.tensor(val_idx, dtype=torch.long)
    test_t = torch.tensor(test_idx, dtype=torch.long)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    best_state = None
    best_val = float("inf")
    started_train = time.perf_counter()
    for _ in range(epochs):
        model.train()
        optimizer.zero_grad()
        pred = model(x, edge_index)
        loss = F.mse_loss(pred[train_t], y[train_t])
        loss.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            val_loss = F.mse_loss(model(x, edge_index)[val_t], y[val_t]).item()
        if val_loss < best_val:
            best_val = val_loss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    training_time = time.perf_counter() - started_train
    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    started_infer = time.perf_counter()
    with torch.no_grad():
        pred_scaled = model(x, edge_index).detach().cpu().numpy()
        emb = model.embeddings(x, edge_index).detach().cpu().numpy()
    inference_time = time.perf_counter() - started_infer
    pred = scaler.inverse_transform(pred_scaled[test_idx].reshape(-1, 1)).ravel()
    true = targets[test_idx]
    rmse = float(np.sqrt(mean_squared_error(true, pred)))
    spear = spearmanr(true, pred).correlation
    row = {
        "model": model_name,
        "seed": seed,
        "mae": float(mean_absolute_error(true, pred)),
        "rmse": rmse,
        "r2": float(r2_score(true, pred)),
        "spearman": float(0.0 if np.isnan(spear) else spear),
        "training_time_s": training_time,
        "inference_time_s": inference_time,
        "train_size": int(len(train_idx)),
        "val_size": int(len(val_idx)),
        "test_size": int(len(test_idx)),
        "best_val_mse_scaled": float(best_val),
    }
    return row, emb


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, default=Path("backend/vector_db/metadata.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports/full_rerun/gnn"))
    parser.add_argument("--graph-out-dir", type=Path, default=Path("reports/full_rerun/graph"))
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--hidden-dim", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    parser.add_argument("--lr", type=float, default=0.01)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.graph_out_dir.mkdir(parents=True, exist_ok=True)

    materials = _load_materials(args.metadata)
    features, feature_names = _feature_matrix(materials)
    edge_index = _build_knn_graph(features, args.k)
    targets = {
        "Band gap": np.array([_safe_float(m.get("band_gap")) for m in materials], dtype=np.float32),
        "Density": np.array([_safe_float(m.get("density")) for m in materials], dtype=np.float32),
    }
    graph_summary = {
        "nodes": len(materials),
        "edges_directed": int(edge_index.shape[1]),
        "edge_construction_rule": f"{args.k}-nearest neighbors in formula-derived feature space using cosine distance",
        "average_out_degree_after_symmetrization": float(edge_index.shape[1] / len(materials)),
        "connected_components": int(_component_count(edge_index, len(materials))),
        "node_feature_dimensions": int(features.shape[1]),
        "node_feature_names": feature_names,
        "target_properties_available": {
            name: int(np.isfinite(values).sum()) for name, values in targets.items()
        },
        "split": "70/15/15 random split among records with available target values for each target and seed",
        "notes": [
            "Node features are formula-derived to avoid directly using the target value as an input feature.",
            "Graph construction uses local metadata only; no CIF-derived atomic graphs are available in this workspace.",
        ],
    }
    with (args.graph_out_dir / "qmof_graph_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(graph_summary, handle, indent=2)

    metric_rows = []
    embeddings_written = set()
    for target_name, target_values in targets.items():
        available = np.where(np.isfinite(target_values))[0]
        if len(available) < 100:
            continue
        for seed in args.seeds:
            for model_name, model_cls in [
                ("GraphSAGE", SAGERegressor),
                ("GAT", GATRegressor),
            ]:
                model = model_cls(features.shape[1], args.hidden_dim)
                row, emb = _train_eval(
                    model_name=model_name,
                    model=model,
                    features=features,
                    edge_index_np=edge_index,
                    targets=target_values,
                    available=available,
                    seed=seed,
                    epochs=args.epochs,
                    lr=args.lr,
                )
                row["target_property"] = target_name
                metric_rows.append(row)
                if (model_name, target_name) not in embeddings_written:
                    safe_target = target_name.lower().replace(" ", "_")
                    np.save(args.out_dir / f"{model_name.lower()}_{safe_target}_embeddings.npy", emb)
                    embeddings_written.add((model_name, target_name))

    metrics = pd.DataFrame(metric_rows)
    summary = (
        metrics.groupby(["model", "target_property"])
        .agg(
            mae_mean=("mae", "mean"),
            mae_std=("mae", "std"),
            rmse_mean=("rmse", "mean"),
            rmse_std=("rmse", "std"),
            r2_mean=("r2", "mean"),
            r2_std=("r2", "std"),
            spearman_mean=("spearman", "mean"),
            spearman_std=("spearman", "std"),
            training_time_s_mean=("training_time_s", "mean"),
            inference_time_s_mean=("inference_time_s", "mean"),
            runs=("seed", "count"),
        )
        .reset_index()
    )
    metrics.to_csv(args.out_dir / "gnn_property_prediction_metrics.csv", index=False)
    summary.to_csv(args.out_dir / "gnn_property_prediction_summary.csv", index=False)
    with (args.out_dir / "gnn_training_log.md").open("w", encoding="utf-8") as handle:
        handle.write("# GNN Property Prediction Rerun\n\n")
        handle.write(f"Metadata: `{args.metadata}`\n\n")
        handle.write(f"Graph: `{args.graph_out_dir / 'qmof_graph_summary.json'}`\n\n")
        handle.write(f"Seeds: {args.seeds}; epochs: {args.epochs}; hidden_dim: {args.hidden_dim}; k: {args.k}\n\n")
        handle.write("PyTorch Geometric was used for node-level GraphSAGE and GAT regressors.\n")
    print(f"Wrote GNN outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
