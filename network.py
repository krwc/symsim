#!/usr/bin/env python3
import collections
import sympy

import elements as elem

class Edge(collections.namedtuple('Edge', ['u', 'v', 'element'])):
    def __new__(cls, u, v, element: elem.Element):
        assert isinstance(element, elem.Element)
        self = super().__new__(cls, str(u), str(v), element)
        return self


class Network:
    def __init__(self):
        super().__init__()
        self._edges = set()
        self._nodes = set()
        self._symbols = set()
        self._incident_edges_of_node = collections.defaultdict(list)

    def add_edge(self, elem: Edge):
        if not isinstance(elem, Edge):
            raise ValueError(
                "Only edges of class Edge can be added to the Network")
        elif elem in self._edges:
            return

        u, v, _ = elem

        self._nodes.add(u)
        self._nodes.add(v)
        self._incident_edges_of_node[u] += [elem]
        self._incident_edges_of_node[v] += [elem]
        self._edges.add(elem)
        self._symbols.add(elem.element.symbol)

    def find_edge_by_elem_symbol(self, symbol: sympy.Symbol) -> Edge:
        for edge in self.edges:
            if edge.element.symbol == symbol:
                return edge
        return None

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
        GROUND_NODE = '0'
        if GROUND_NODE in self._nodes:
            return GROUND_NODE

        raise ValueError("Set is empty, thus there is no ground node")

    def incident_edges(self, node):
        return self._incident_edges_of_node[node]

