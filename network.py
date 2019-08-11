#!/usr/bin/env python3
import collections
import sympy

import elements as elem

class Edge(collections.namedtuple('Edge', ['u', 'v', 'element'])):
    pass


class Network:
    def __init__(self):
        super().__init__()
        self._edges = set()
        self._nodes = set()
        self._symbols = set()
        self._ground_node = None
        self._incident_edges_of_node = collections.defaultdict(list)

    def add_edge(self, elem: Edge):
        if not isinstance(elem, Edge):
            raise ValueError(
                "Only edges of class Edge can be added to the Network")
        elif elem in self._edges:
            return

        u, v, _ = elem
        if self._ground_node == None:
            self._ground_node = min(u, v)
        else:
            self._ground_node = min(self._ground_node, min(u, v))

        self._nodes.add(u)
        self._nodes.add(v)
        self._incident_edges_of_node[u] += [elem]
        self._incident_edges_of_node[v] += [elem]
        self._edges.add(elem)
        self._symbols.add(elem.element.symbol)

    @property
    def nodes(self):
        return sorted(self._nodes, key=str)

    @property
    def edges(self):
        return self._edges

    @property
    def nonground_nodes(self):
        return filter(lambda u: u != self.ground_node, self.nodes)

    @property
    def ground_node(self):
        if self._ground_node is None:
            raise ValueError("Set is empty, thus there is no ground node")
        return self._ground_node

    def incident_edges(self, node):
        return self._incident_edges_of_node[node]

