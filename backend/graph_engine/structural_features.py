from __future__ import annotations

from collections import deque


STRUCTURAL_FEATURE_NAMES = [
    "in_degree_log",
    "out_degree_log",
    "total_degree_log",
    "is_root",
    "is_leaf",
    "depth_log",
]


def build_structural_features(
    edge_index,
    num_nodes: int,
):
    import torch

    if num_nodes <= 0:
        return torch.empty(
            (0, len(STRUCTURAL_FEATURE_NAMES)),
            dtype=torch.float32,
        )

    if edge_index.numel():
        source = edge_index[0]
        target = edge_index[1]

        out_degree = torch.bincount(
            source,
            minlength=num_nodes,
        ).float()

        in_degree = torch.bincount(
            target,
            minlength=num_nodes,
        ).float()

    else:
        in_degree = torch.zeros(
            num_nodes,
            dtype=torch.float32,
        )

        out_degree = torch.zeros(
            num_nodes,
            dtype=torch.float32,
        )

    total_degree = (
        in_degree
        + out_degree
    )

    in_degree_log = torch.log1p(
        in_degree
    )

    out_degree_log = torch.log1p(
        out_degree
    )

    total_degree_log = torch.log1p(
        total_degree
    )

    is_root = (
        in_degree == 0
    ).float()

    is_leaf = (
        out_degree == 0
    ).float()

    adjacency = [
        []
        for _ in range(num_nodes)
    ]

    if edge_index.numel():
        for source_node, target_node in (
            edge_index.t().tolist()
        ):
            adjacency[source_node].append(
                target_node
            )

    roots = [
        index
        for index in range(num_nodes)
        if in_degree[index].item() == 0
    ]

    if not roots:
        roots = [0]

    depths = [-1] * num_nodes
    queue = deque()

    for root in roots:
        if depths[root] == -1:
            depths[root] = 0
            queue.append(root)

    while queue:
        node = queue.popleft()

        for neighbour in adjacency[node]:
            if depths[neighbour] != -1:
                continue

            depths[neighbour] = (
                depths[node] + 1
            )

            queue.append(neighbour)

    depths = [
        max(depth, 0)
        for depth in depths
    ]

    depth_log = torch.log1p(
        torch.tensor(
            depths,
            dtype=torch.float32,
        )
    )

    return torch.stack(
        [
            in_degree_log,
            out_degree_log,
            total_degree_log,
            is_root,
            is_leaf,
            depth_log,
        ],
        dim=1,
    )


class StructuralFeaturesTransform:
    def __call__(self, data):
        from torch_geometric.utils import (
            to_undirected,
        )

        directed_edge_index = (
            data.edge_index.clone()
        )

        data.x = (
            build_structural_features(
                edge_index=directed_edge_index,
                num_nodes=data.num_nodes,
            )
        )

        data.edge_index = to_undirected(
            directed_edge_index,
            num_nodes=data.num_nodes,
        )

        return data
