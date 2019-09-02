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

            if isinstance(element, elem.Passive):
                # Current flows into u, we thus have a factor:
                # (Vv - Vu) * gx
                g = 1 / element.impedance
                assert u != ground_node
                G[row, elem_index[u]] -= g
                if v is not ground_node:
                    G[row, elem_index[v]] += g
            elif isinstance(element, elem.CurrentSource):
                b[elem_index[node]] += -polarity * element.value
            elif isinstance(element, elem.VoltageSource):
                G[row, elem_index[element.symbol]] = polarity
                G[elem_index[element.symbol], elem_index[node]] = polarity
                b[elem_index[element.symbol]] = element.value
            elif isinstance(element, elem.DependentCurrentSource):
                edge = net.find_edge_by_elem_symbol(element.dependent_value.symbol)
                if not edge:
                    raise ValueError('Reference to an unknown element %s' % element.dependent_value)

                u, v, symbol = edge
                # TODO: support sources.
                assert isinstance(symbol, elem.Passive)

                if element.current_controlled:
                    # i = (V_u - V_v) / Z * coeffcient
                    # i = coeff/Z * V_u - coeff/Z * V_v
                    g = element.scaling_factor / symbol.impedance
                else:
                    assert element.voltage_controlled
                    # i = (V_u - V_z) * coefficient
                    g = element.scaling_factor

                if u is not ground_node:
                    G[row, elem_index[u]] += g
                if v is not ground_node:
                    G[row, elem_index[v]] -= g
            else:
                raise NotImplementedError

    solution = G.LUsolve(b)
    voltage_per_node = {}
    voltage_per_node[net.ground_node] = sympy.sympify('0')

    for x in elem_index:
        if not isinstance(x, int):
            continue
        voltage_per_node[x] = solution[elem_index[x]].simplify()

    current_per_symbol = {}
    for edge in net.edges:
        u, v, element = edge

        if isinstance(element, elem.Resistor) or \
            isinstance(element, elem.Inductor) or \
            isinstance(element, elem.Capacitor):
            current_per_symbol[element.symbol] = (voltage_per_node[u] - voltage_per_node[v]) / element.impedance
        elif isinstance(element, elem.CurrentSource):
            current_per_symbol[element.symbol] = element.value
        elif isinstance(element, elem.VoltageSource):
            current_per_symbol[element.symbol] = solution[elem_index[element.symbol]]
        elif isinstance(element, elem.DependentCurrentSource):
            pass

    return voltage_per_node, current_per_symbol

