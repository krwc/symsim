#!/usr/bin/env python3

import sympy
import sys
import collections
import io
import re

import network as net
import solver

SUPPORTED_COMPONENTS = {
    'R': net.Network.add_resistor,
    'L': net.Network.add_inductor,
    'C': net.Network.add_capacitor,
    'I': net.Network.add_current_source,
    'V': net.Network.add_voltage_source,
    'G': net.Network.add_dependent_current_source,
    'Q': net.Network.add_bjt,
}

def parse_print(line: str) -> str:
    assert line.startswith('print')
    if len(line.split()) < 2:
        raise ValueError('`print` command without argument.')
    return line[len('print'):]

def get_element_adder(element: str):
    if not element[0].upper() in SUPPORTED_COMPONENTS:
        raise ValueError('Unsupported element: %s' % element)

    return SUPPORTED_COMPONENTS[element[0].upper()]

def parse_network_defn(out_net: net.Network, line: str):
    """
    Every edge has the following form:

        {R,L,C,I,V,G}\w+ nx ny [dependent value] [constant scaling factor = 1]

    Where the '[dependent value]' may be of form either 'I(some element)', or
    'V(some element)'.
    """
    items = line.split()
    name = items[0]
    n1 = items[1]
    n2 = items[2]
    elem_adder = get_element_adder(name)
    args = [ n1, n2, name ]

    if name[0].upper() == 'G':
        # NOTE: This is a dependent current source
        if len(items) < 4:
            raise ValueError('Incorrect format of a dependent current source')

        # allow only [IV](something) scaling-expr
        match = re.match(r'^[IV]\((.+?)\)\s+(.+)$', ' '.join(items[3:]))
        if not match:
            raise ValueError('Bad format of controlling value and/or scaling factor')

        element = match.group(1).strip()
        scaling_factor = match.group(2).strip()
        # append controlling value
        if items[3][0] == 'I':
            args.append(net.Network.Quantity.CURRENT)
        else:
            args.append(net.Network.Quantity.VOLTAGE)

        args.append(element)
        args.append(scaling_factor)
    elif name[0].upper() == 'Q':
        # NOTE: This is a BJT.
        if len(items) != 4:
            raise ValueError('Incorrect format of a BJT')
        n3 = items[3]
        args = [ n1, n2, n3, name ]

    elem_adder(out_net, *args)

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
                parse_network_defn(result, line)
        except ValueError as e:
            print('Parse error at line %d:\n>> %s\n%s' % (i + 1, line, e))
            raise

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
        return voltages[str(node)]

    from tabulate import tabulate
    table_headers = ['Quantity', 'Value']
    table_rows = []
    for node in voltages:
        table_rows.append(['V(%s)' % node, voltages[node].expand().simplify()])

    for sym in currents:
        table_rows.append(['I(%s)' % sym, currents[sym].expand().simplify()])

    locals = {
        'I': I,
        'V': V,
    }
    for p in prints:
        result = sympy.sympify(p, locals=locals)
        # ratio=1 -> don't allow the expression to get too long.
        table_rows.append(['%s' % p, result.expand().simplify(ratio=1)])

    print(tabulate(table_rows, table_headers, tablefmt='psql'))

if __name__ == '__main__':
    _main()
