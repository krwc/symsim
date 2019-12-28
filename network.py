#!/usr/bin/env python3
import collections
import sympy
import enum

from internal import elements as elem
from internal.edge import Edge

class Network:
    def __init__(self):
        super().__init__()
        self._edges = set()
        self._nodes = set()
        self._symbols = set()
        self._unique_node_id = 0
        self._incident_edges_of_node = collections.defaultdict(list)

    def _add_edge(self, n1, n2, element: elem.Element):
        edge = Edge(n1, n2, element)

        if edge in self._edges:
            return

        self._nodes.add(n1)
        self._nodes.add(n2)
        self._incident_edges_of_node[n1] += [edge]
        self._incident_edges_of_node[n2] += [edge]
        self._edges.add(edge)
        self._symbols.add(edge.element.symbol)

    def _gen_unique_node(self):
        while True:
            node = 'n_%05d' % self._unique_node_id
            self._unique_node_id += 1
            if node not in self._nodes:
                return node

    def add_resistor(self, n1, n2, name):
        self._add_edge(n1, n2, elem.Resistor(name))

    def add_capacitor(self, n1, n2, name):
        self._add_edge(n1, n2, elem.Capacitor(name))

    def add_inductor(self, n1, n2, name):
        self._add_edge(n1, n2, elem.Inductor(name))

    def add_voltage_source(self, n1, n2, name):
        self._add_edge(n1, n2, elem.VoltageSource(name))

    def add_current_source(self, n1, n2, name):
        self._add_edge(n1, n2, elem.CurrentSource(name))

    class Quantity(enum.Enum):
        CURRENT = enum.auto()
        VOLTAGE = enum.auto()

    def add_dependent_current_source(self, n1, n2, name,
                                     controlling_quantity: Quantity,
                                     controlling_element: str,
                                     scaling_factor: float = 1.0):
        ctor = None
        if controlling_quantity == Network.Quantity.CURRENT:
            ctor = elem.CurrentControlledCurrentSource
        elif controlling_quantity == Network.Quantity.VOLTAGE:
            ctor = elem.VoltageControlledCurrentSource
        else:
            raise ValueError('Expected either Quantity.CURRENT or Quantity.VOLTAGE')

        self._add_edge(n1, n2, ctor(name, controlling_element, scaling_factor))

    def add_bjt(self, nb, ne, nc, name, ro=True):
        # We use a g_m * v_pi dependent current source.
        #
        # B                                     C
        # o-----.            .-------------.----o
        #     + |            |             |
        #       \           / \            \
        #  v_pi / r_pi      \ / gm*v_pi    / ro
        #       \            |             \
        #     - |            |             |
        #       `-----.------`-------------`
        #             |
        #             o E
        gm_id = 'Gm_%s' % name
        ro_id = 'Ro_%s' % name
        rpi_id = 'Rp_%s' % name
        ic_id = 'Ic_%s' % name

        self.add_resistor(nb, ne, rpi_id)
        if ro:
            self.add_resistor(nc, ne, ro_id)

        self.add_dependent_current_source(nc, ne, ic_id, Network.Quantity.VOLTAGE, rpi_id, gm_id)

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

