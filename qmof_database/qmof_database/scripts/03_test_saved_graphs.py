import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch


GRAPH_PATH = "../processed_graphs/qmof_graphs.pt"


# IMPORTANT FIX
graphs = torch.load(GRAPH_PATH, weights_only=False)

print(f"\nTotal graphs loaded: {len(graphs)}")

g = graphs[0]

print("\n========== SAMPLE GRAPH ==========")

print(g)

print("\nQMOF ID:")
print(g.qmof_id)

print("\nNode feature matrix shape:")
print(g.x.shape)

print("\nEdge index shape:")
print(g.edge_index.shape)

print("\nEdge feature shape:")
print(g.edge_attr.shape)

print("\nGlobal feature shape:")
print(g.global_features.shape)

print("\nTarget y:")
print(g.y)

print("\n========== GRAPH DETAILS ==========")

print(f"Number of nodes: {g.num_nodes}")
print(f"Number of edges: {g.num_edges}")

print("\nFirst 5 node features:")
print(g.x[:5])

print("\nFirst 10 edges:")
print(g.edge_index[:, :10])

print("\nFirst 10 edge distances:")
print(g.edge_attr[:10])

print("\nGlobal graph features:")
print(g.global_features)