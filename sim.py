#!/usr/bin/env python3

import sympy
import sys
import collections
import io

SUPPORTED_COMPONENTS = {
    # Resistor
    'R',
    # Inductor
    'L',
    # Capacitor
    'C',
    # Current source
    'I',
    # Voltage source
    'V'
}


class Element:
    def __init__(self, symbol, symbolic_expression):
        self._symbol = symbol
        self._value = symbolic_expression

    @property
    def symbol(self):
        return self._symbol

    @property
    def type(self):
        return str(self.symbol)[0]

    @property
    def value(self):
        return self._value

    @property
    def terms(self):
        return self._value.as_terms()[-1]


class Edge(collections.namedtuple('Edge', ['u', 'v', 'element'])):
    pass


def parse_edge(n1: str, n2: str, c: str):
    """
    Format of the edge is simply: `a b Ux`, where a, b are integers
    and represent node numbers, Ux is a component (e.g. resistor).

    NOTE: node with the smallest numeric identifier is a ground node.
    """
    n1 = int(n1)
    n2 = int(n2)
    if c[0] not in SUPPORTED_COMPONENTS:
        raise ValueError("Unsupported component: %s" % c)

    symbol = sympy.sympify(c)
    # TODO: this is a very trivial impedance conversion. It requires
    # more parsing validation.
    value = c
    if c[0] == 'L':
        value = 's * {0}'.format(c)
    elif c[0] == 'C':
        value = '1 / (s * {0})'.format(c)

    return Edge(n1, n2, Element(symbol, sympy.sympify(value)))


def parse_dependent_source(n1: str, n2: str, name: str, *defn):
    """
    Format of the dependent source edge is (where {V,I} means either V or I):

        n1 n2 {Vx,Ix} expression
    """
    n1 = int(n1)
    n2 = int(n2)

    if name[0] not in ('V', 'I'):
        raise ValueError(
            "Dependent source can either be a voltage or current source")

    symbol = sympy.sympify(name)
    return Edge(n1, n2, Element(symbol, sympy.sympify(''.join(defn))))


class Network:
    def __init__(self):
        super().__init__()
        self._edges = set()
        self._nodes = set()
        self._consts = set()
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

    def add_const(self, const: sympy.Symbol):
        if not isinstance(const, sympy.Symbol):
            raise ValueError(
                "Only constants of class sympy.Symbol can be added to the Network")

        if const in self._symbols:
            raise ValueError(
                "Constant %s is already an element symbol" % const)

        self._consts.add(const)

    def unordered_nodes(self):
        return self._nodes

    def nodes(self):
        return sorted(self._nodes, key=str)

    def edges(self):
        return self._edges

    def consts(self):
        return self._consts

    def nonground_nodes(self):
        return filter(lambda u: u != self.ground_node(), self.nodes())

    def ground_node(self):
        if self._ground_node is None:
            raise ValueError("Set is empty, thus there is no ground node")
        return self._ground_node

    def incident_edges(self, node):
        return self._incident_edges_of_node[node]


def parse_network(input: str = None) -> Network:
    net = Network()
    for line in (io.StringIO(input) if input else sys.stdin):
        line = line.strip()

        if len(line) == 0:
            continue

        if line.startswith('const'):
            items = line.split()
            if len(items) > 2:
                raise ValueError(
                    "Constant names with spaces are not supported")
            net.add_const(sympy.sympify(items[-1]))
        else:
            items = line.split()
            if len(items) == 3:
                net.add_edge(parse_edge(*items))
            elif len(items) >= 4:
                net.add_edge(parse_dependent_source(*items))
            else:
                raise ValueError("Unrecognized command: %s" % line)

    return net


def solve_system(net: Network):
    ground_node = net.ground_node()

    # Elem is either a node or a supernode (e.g. voltage source).
    elem_index = dict()
    for index, node in enumerate(net.nonground_nodes()):
        elem_index[node] = index

    # Every voltage source introduces one unknown current through
    # it, but also one additional equation, thus keeping the system
    # solvable.
    for edge in (e for e in net.edges() if e.element.type == 'V'):
        elem_index[edge.element.symbol] = len(elem_index)

    n = len(elem_index)
    G = sympy.zeros(n, n)
    b = sympy.zeros(n, 1)

    for row, node in enumerate(net.nonground_nodes()):
        for edge in net.incident_edges(node):
            u, v, element = edge
            # From now on, assume `node` == u, and that the current through
            # passive components always flows into that node.
            if node == v:
                polarity = +1
                u, v = v, u
            else:
                polarity = -1

            if element.type in ('R', 'L', 'C'):
                # Current flows into u, we thus have a factor:
                # (Vv - Vu) * gx
                g = 1 / element.value
                assert u != ground_node
                G[row, elem_index[u]] -= g
                if v is not ground_node:
                    G[row, elem_index[v]] += g
            elif element.type == 'I':
                b[elem_index[node]] = -element.value
            elif element.type == 'V':
                G[row, elem_index[element.symbol]] = polarity
                G[elem_index[element.symbol], elem_index[node]] = polarity
                b[elem_index[element.symbol]] = element.value
            else:
                raise NotImplementedError

    # print(G)
    # print(b)

    solution = G.LUsolve(b)
    for x in elem_index:
        if not isinstance(x, int):
            continue
        print('Voltage at node %d' % x, solution[elem_index[x]].simplify())

    return solution, elem_index


def _main():
    net = parse_network()
    solve_system(net)


if __name__ == '__main__':
    _main()
