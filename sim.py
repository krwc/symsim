#!/usr/bin/env python3

import sympy
import sys
import collections
import io
import re

import elements as elem
import network as net
import solver

SUPPORTED_COMPONENTS = {
    'R': elem.Resistor,
    'L': elem.Inductor,
    'C': elem.Capacitor,
    'I': elem.CurrentSource,
    'V': elem.VoltageSource,
    'G': elem.DependentCurrentSource,
}

def parse_print(line: str) -> str:
    assert line.startswith('print')
    if len(line.split()) < 2:
        raise ValueError('`print` command without argument.')
    return line[len('print'):]


def parse_edge(line: str) -> net.Edge:
    """
    Every edge has the following form:

        nx ny {R,L,C,I,V,G}\w+ [dependent value] [constant scaling factor = 1]

    Where the '[dependent value]' may be of form either 'I(some element)', or
    'V(some element)'.
    """
    items = line.split()
    if len(items) not in (3, 4, 5):
        raise ValueError('Unrecognized format of an edge')

    n1 = int(items[0])
    n2 = int(items[1])
    name = items[2]
    type = name[0]
    if type not in SUPPORTED_COMPONENTS:
        raise ValueError('Unsupported component: %s' % c)

    elem_class = SUPPORTED_COMPONENTS[type]
    ctor_args = [ name ]
    if len(items) in (4, 5):
        if issubclass(elem_class, elem.Passive):
            raise ValueError('Passives with dependent values are not supported')
        assert elem_class == elem.DependentCurrentSource

        if len(items) == 4:
            dependent_value = items[-1]
        else:
            dependent_value = items[-2]

        # allow only I(element) or V(element).
        match = re.match(r'^[IV]\((.+)\)$', dependent_value)
        if not match:
            raise ValueError('Controlling value may be either I(element) or V(element)')
        element = match.group(1)
        if not element[0] in SUPPORTED_COMPONENTS:
            raise ValueError('Unknown element type %s' % element)

        element = SUPPORTED_COMPONENTS[element[0]](element)
        # append controlling value
        if match.group(0)[0] == 'I':
            ctor_args.append(elem.DependentValue.Current(element))
        elif match.group(0)[0] == 'V':
            ctor_args.append(elem.DependentValue.Voltage(element))
        # append scaling factor if any
        if len(items) == 5:
            ctor_args.append(items[-1])

    return net.Edge(n1, n2, elem_class(*ctor_args))

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
            if line.startswith('print'):
                print_commands.append(parse_print(line))
            else:
                result.add_edge(parse_edge(line))
        except ValueError as e:
            print('Parse error at line %d: %s' % (i + 1, e))

    return result, print_commands


def _main():
    net, prints = parse_network()
    voltages, currents = solver.solve_system(net)
    substitutions = {}

    def I(symbol):
        if symbol in currents:
            return currents[symbol]
        raise ValueError("No current information for %s" % symbol)

    def V(node):
        return voltages[node]

    locals = {
        'I': I,
        'V': V,
    }
    for p in prints:
        result = sympy.sympify(p, locals=locals)
        print('%s =' % p, result.expand().simplify())

if __name__ == '__main__':
    _main()
