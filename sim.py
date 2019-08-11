#!/usr/bin/env python3

import sympy
import sys
import collections
import io

import elements as elem
import network as net
import solver

SUPPORTED_COMPONENTS = {
    'R': elem.Resistor,
    'L': elem.Inductor,
    'C': elem.Capacitor,
    'I': elem.CurrentSource,
    'V': elem.VoltageSource,
}

def parse_const(line: str) -> sympy.Symbol:
    assert line.startswith('const')
    if len(line.split()) > 2:
        raise ValueError('Constants with spaces in names are not supported.')
    return sympy.sympify(line[len('const'):])


def parse_print(line: str) -> sympy.Symbol:
    assert line.startswith('print')
    if len(line.split()) < 2:
        raise ValueError('`print` command without argument.')
    return sympy.sympify(line[len('print'):])


def parse_edge(line: str) -> net.Edge:
    """
    Every edge has the following form:

        nx ny {R,L,C,I,V}\w+ [optional expression representing value (unsupported now)]
    """
    items = line.split()
    if len(items) != 3:
        raise ValueError('Unrecognized format of an edge')

    n1 = int(items[0])
    n2 = int(items[1])
    name = items[2]
    type = name[0]
    if type not in SUPPORTED_COMPONENTS:
        raise ValueError('Unsupported component: %s' % c)

    return net.Edge(n1, n2, SUPPORTED_COMPONENTS[type](name))

def parse_network(input: str = None) -> (net.Network, 'PrintCommands'):
    result = net.Network()
    print_commands = []

    for i, line in enumerate(io.StringIO(input) if input else sys.stdin):
        line = line.strip()

        if len(line) == 0:
            continue

        # Ignore comments
        if line.startswith('#'):
            continue

        try:
            if line.startswith('const'):
                result.add_const(parse_const(line))
            elif line.startswith('print'):
                print_commands.append(parse_print(line))
            else:
                result.add_edge(parse_edge(line))
        except ValueError as e:
            print('Parse error at line %d:' % (i + 1))
            print(e)

    return result, print_commands


def _main():
    net, prints = parse_network()
    #solution = solver.solve_system(net)
    """
    substitutions = {}
    for node in solution:
        substitutions[sympy.sympify(
            'V{0}'.format(node))] = solution[node]

    for p in prints:
        result = p.subs(substitutions)
        print('%s =' % p, result.simplify())
    """

if __name__ == '__main__':
    _main()
