#!/usr/bin/env python3
import sympy
import elements as elem

from network import Network

def solve_system(net: Network):
    ground_node = net.ground_node

    # Elem is either a node or a supernode (e.g. voltage source).
    elem_index = dict()
    for index, node in enumerate(net.nonground_nodes):
        elem_index[node] = index

    # Every voltage source introduces one unknown current through
    # it, but also one additional equation, thus keeping the system
    # solvable.
    for edge in (e for e in net.edges if isinstance(e.element, elem.VoltageSource)):
        elem_index[edge.element.symbol] = len(elem_index)

    n = len(elem_index)
    G = sympy.zeros(n, n)
    b = sympy.zeros(n, 1)

    for row, node in enumerate(net.nonground_nodes):
        for edge in net.incident_edges(node):
            u, v, element = edge
            # From now on, assume `node` == u, and that the current through
            # passive components always flows into that node.
            if node == v:
                polarity = +1
                u, v = v, u
            else:
                polarity = -1

            if element.__class__ in (elem.Resistor,
                                     elem.Inductor,
                                     elem.Capacitor):
                # Current flows into u, we thus have a factor:
                # (Vv - Vu) * gx
                g = 1 / element.impedance
                assert u != ground_node
                G[row, elem_index[u]] -= g
                if v is not ground_node:
                    G[row, elem_index[v]] += g
            elif element.__class__ == elem.CurrentSource:
                b[elem_index[node]] = -polarity * element.value
            elif element.__class__ == elem.VoltageSource:
                G[row, elem_index[element.symbol]] = polarity
                G[elem_index[element.symbol], elem_index[node]] = polarity
                b[elem_index[element.symbol]] = element.value
            else:
                raise NotImplementedError

    solution = G.LUsolve(b)
    voltage_per_node = {}
    for x in elem_index:
        if not isinstance(x, int):
            continue
        voltage_per_node[x] = solution[elem_index[x]].simplify()

    return voltage_per_node

