import math
import numpy as np
from typing import List, Tuple

from pyrr import Vector3

from models.edge import Edge
from models.node import Node, create_nodes


LOG_SOURCE: str = "NETWORK_MODEL"


class NetworkModel:
    def __init__(self, layer: List[int], node_size: float, layer_distance: float, layer_data: List[np.array] = None,
                 importance_prune_threshold: float = 0.5):
        self.layer: List[int] = layer
        self.node_size: float = node_size
        self.layer_distance: float = layer_distance
        self.importance_prune_threshold: float = importance_prune_threshold

        self.max_layer_width: float = 1.0
        for node_count in layer:
            sqrt_node_count = math.ceil(math.sqrt(node_count))
            if self.max_layer_width < sqrt_node_count * node_size:
                self.max_layer_width = sqrt_node_count * node_size

        self.bounding_volume: Tuple[Vector3, Vector3] = (
            Vector3([-self.max_layer_width, -self.max_layer_width, -len(self.layer) * self.layer_distance / 2.0]),
            Vector3([self.max_layer_width, self.max_layer_width, len(self.layer) * self.layer_distance / 2.0]))
        self.bounding_mid: Vector3 = (self.bounding_volume[1] + self.bounding_volume[0]) / 2.0
        self.bounding_range: Vector3 = (self.bounding_volume[1] - self.bounding_volume[0]) / 2.0
        self.bounding_range = Vector3(
            [abs(self.bounding_range.x), abs(self.bounding_range.y), abs(self.bounding_range.z)])

        self.layer_nodes: List[List[Node]] = create_nodes(self.layer, self.bounding_mid,
                                                          (self.bounding_volume[0].x, self.bounding_volume[1].x),
                                                          (self.bounding_volume[0].y, self.bounding_volume[1].y),
                                                          (self.bounding_volume[0].z, self.bounding_volume[1].z),
                                                          None, layer_data)
        self.edge_count: int = 0
        for i in range(len(self.layer) - 1):
            self.edge_count += len(self.layer_nodes[i]) * len(self.layer_nodes[i + 1])
        self.pruned_edges: int = 0
        self.average_edge_distance: float = self.get_average_edge_distance()
        print("[%s] Average edge distance: %f" % (LOG_SOURCE, self.average_edge_distance))

    def get_nodes(self) -> List[Node]:
        node_data: List[Node] = []
        for layer in self.layer_nodes:
            for node in layer:
                node_data.append(node)
        return node_data

    def set_nodes(self, node_data: List[Node]):
        read_node_index: int = 0
        for i, layer in enumerate(self.layer_nodes):
            new_nodes = []
            for _ in layer:
                new_nodes.append(node_data[read_node_index])
                read_node_index += 1
            self.layer_nodes[i] = new_nodes

    def generate_edges(self) -> List[Edge]:
        edges: List[Edge] = []
        for i in range(len(self.layer) - 1):
            for node_one in self.layer_nodes[i]:
                for node_two in self.layer_nodes[i + 1]:
                    new_edge: Edge = Edge(node_one, node_two)
                    if new_edge.data[3] * new_edge.data[6] > self.importance_prune_threshold / new_edge.data[2]:
                        edges.append(Edge(node_one, node_two))
                    else:
                        self.pruned_edges += 1
        return edges

    def generate_edges_special(self) -> List[Edge]:
        edges: List[Edge] = []
        for i in range(len(self.layer) - 1):
            for i_one, node_one in enumerate(self.layer_nodes[i]):
                for i_two, node_two in enumerate(self.layer_nodes[i + 1]):
                    if ((node_one.position + node_two.position) / 2.0).y != (
                            self.bounding_volume[1].y + self.bounding_volume[0].y) / 2.0:
                        edges.append(Edge(node_one, node_two))
        return edges

    def generate_max_distance(self) -> float:
        max_distance: float = 0.0
        for i in range(len(self.layer) - 1):
            for node_one in self.layer_nodes[i]:
                for node_two in self.layer_nodes[i + 1]:
                    distance: float = (node_one.position - node_two.position).length
                    if max_distance < distance:
                        max_distance = distance
        return max_distance

    def get_average_edge_distance(self) -> float:
        distance_sum: float = 0.0
        distance_values: int = 0
        for i in range(len(self.layer) - 1):
            distance_values += len(self.layer_nodes[i]) * len(self.layer_nodes[i])
        for i in range(len(self.layer) - 1):
            layer_distance_sum: float = 0.0
            for node_one in self.layer_nodes[i]:
                for node_two in self.layer_nodes[i]:
                    layer_distance_sum += math.sqrt(
                        (node_one.position.x - node_two.position.x) * (node_one.position.x - node_two.position.x)
                        + (node_one.position.y - node_two.position.y) * (node_one.position.y - node_two.position.y)
                        + (node_one.position.z - node_two.position.z) * (node_one.position.z - node_two.position.z))
            distance_sum += layer_distance_sum / float(distance_values)
        return distance_sum
