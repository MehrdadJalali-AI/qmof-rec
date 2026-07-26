import torch
import torch.nn.functional as F

from torch.nn import Linear
from torch_geometric.nn import SAGEConv, global_mean_pool


class GraphSAGEClassifier(torch.nn.Module):
    def __init__(self, in_channels=5, hidden_dim=64, num_classes=3):
        super().__init__()

        self.conv1 = SAGEConv(in_channels, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)

        self.lin1 = Linear(hidden_dim, hidden_dim)
        self.lin2 = Linear(hidden_dim, num_classes)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index)
        x = F.relu(x)

        x = self.conv2(x, edge_index)
        x = F.relu(x)

        graph_embedding = global_mean_pool(x, batch)

        x = self.lin1(graph_embedding)
        x = F.relu(x)

        logits = self.lin2(x)

        return logits

    def get_embedding(self, x, edge_index, batch):
        x = self.conv1(x, edge_index)
        x = F.relu(x)

        x = self.conv2(x, edge_index)
        x = F.relu(x)

        graph_embedding = global_mean_pool(x, batch)

        return graph_embedding
