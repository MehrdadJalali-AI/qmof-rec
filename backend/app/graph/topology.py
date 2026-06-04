def graph_statistics(graph):
    return {
        "num_nodes_atoms": int(graph.num_nodes),
        "num_edges_sparse": int(graph.edge_index.shape[1]),
        "node_features": int(graph.x.shape[1]),
        "edge_features": int(graph.edge_attr.shape[1]),
    }