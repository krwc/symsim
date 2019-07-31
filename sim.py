import sympy
import sys
import collections

SUPPORTED_COMPONENTS = {
    # Resistor
    'R',
    # Inductor
    'L',
    # Capacitor
    'C',
    # Current source
    'I',
}


class Edge(collections.namedtuple('Edge', ['u', 'v', 'symbol'])):
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

    return Edge(u=n1, v=n2, symbol=sympy.symbols(c))


class EdgeSet(set):
    def __init__(self):
        super().__init__()
        self._ground_node = None
        self._nodes = set()
        self._incident_edges_of_node = collections.defaultdict(list)

    def add(self, elem):
        if not isinstance(elem, Edge):
            raise ValueError(
                "Only items of class Edge can be added to the EdgeSet")
        elif elem in self:
            return

        u, v, _ = elem
        if self._ground_node == None:
            self._ground_node = min(u, v)
        else:
            self._ground_node = min(self._ground_node, min(u, v))

        self._nodes.add(u)
        self._nodes.add(v)
        self._incident_edges_of_node[u] += elem
        self._incident_edges_of_node[v] += elem
        super().add(elem)

    def remove(self, elem):
        raise NotImplementedError

    def unordered_nodes(self):
        return self._nodes

    def nodes(self):
        return sorted(self._nodes, key=str)

    def nonground_nodes(self):
        return filter(lambda u: u != self.ground_node(), self.nodes())

    def ground_node(self):
        if self._ground_node is None:
            raise ValueError("Set is empty, thus there is no ground node")
        return self._ground_node

    def incident_edges(self, node):
        return self._incident_edges_of_node[node]


def parse_network() -> EdgeSet:
    edges = EdgeSet()
    for line in sys.stdin:
        items = line.strip().split()
        if len(items) == 3:
            edges.add(parse_edge(*items))
        # elif len(items) == 2:
        #    parse_inout(*items)

    return edges


def build_matrix(edges: EdgeSet):
    ground_node = edges.ground_node()
    n = len(edges.unordered_nodes()) - 1
    G = sympy.zeros(n, n)
    b = sympy.zeros(n)

    for row, node in enumerate(edges.nonground_nodes()):
        for edge in edges.incident_edges(node):
            u, v, symbol = edge
            # Assume current always flows into our `node` we analyze.
            if node == u:
                flow_sign = +1
            else:
                flow_sign = -1

        elem_type = str(symbol)[0]
        elem_index = int(str(symbol)[1:])
        if elem_type == 'R':
            g = flow_sign * 1 / symbol
            if u is not ground_node:
                G[row][elem_index] += g
            if v is not ground_node:
                G[row][elem_index] -= g
        elif elem_type == 'I':
            b[elem_index] = flow_sign * symbol
        else:
            raise NotImplementedError

    print(G)
    print(b)


def _main():
    net = parse_network()


if __name__ == '__main__':
    _main()
