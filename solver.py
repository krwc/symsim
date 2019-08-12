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
    for edge in (e for e in net.edges if e.element.__class__ == elem.VoltageSource):
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
                b[elem_index[node]] += -polarity * element.value
            elif element.__class__ == elem.VoltageSource:
                G[row, elem_index[element.symbol]] = polarity
                G[elem_index[element.symbol], elem_index[node]] = polarity
                b[elem_index[element.symbol]] = element.value
            elif element.__class__ == elem.DependentCurrentSource:
                expanded = element.value.expand()
                terms = expanded.as_terms()[-1]
                for term in terms:
                    if not term.is_Function:
                        continue
                    if not term.name in ('I', 'V'):
                        raise ValueError('Unknown function %s' % term.name)
                    if len(term.args) != 1:
                        raise ValueError(
                                'Expected at most 1 argument to function %s' % term.name)

                    edge = net.find_edge_by_elem_symbol(term.args[0])
                    if not edge:
                        raise ValueError(
                                'Reference to an unknown element %s' % term.args[0])

                    u, v, symbol = edge

                    if not symbol.__class__ in (elem.Resistor, elem.Inductor, elem.Capacitor):
                        raise ValueError('Expected R, L, or C')

                    if term.name == 'I':
                        # i = (V_u - V_v) / Z * coeffcient
                        # i = coeff/Z * V_u - coeff/Z * V_v
                        g = expanded.coeff(term) / symbol.impedance
                    else:
                        # i = (V_u - V_z) * coefficient
                        g = expanded.coeff(term)

                    if u is not ground_node:
                        G[row, elem_index[u]] += g
                    if v is not ground_node:
                        G[row, elem_index[v]] -= g
            else:
                raise NotImplementedError

    solution = G.LUsolve(b)
    voltage_per_node = {}
    for x in elem_index:
        if not isinstance(x, int):
            continue
        voltage_per_node[x] = solution[elem_index[x]].simplify()

    print(solution)
    print(elem_index)
    return voltage_per_node

