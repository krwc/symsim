#!/usr/bin/env python3
import sympy

class Element:
    def __init__(self, name: str):
        self._symbol = sympy.symbols(name)

    @property
    def symbol(self) -> sympy.Symbol:
        """ Symbolic name of the element - e.g. R1 """
        return self._symbol


class Passive(Element):
    @property
    def impedance(self) -> sympy.Symbol:
        """
        Symbolic expression for the impedance, e.g. 1/(s * C1) in case
        of a capacitor C1.
        """
        raise NotImplementedError


class Source(Element):
    @property
    def value(self) -> sympy.Symbol:
        """
        Symbolic expression for the value of the source. E.g. in case of
        trivial sources, it'd be the same as the source symbol.

        For dependent sources, it'd return the expression that represents
        the value of the source.
        """
        raise NotImplementedError


class Resistor(Passive):
    def __init__(self, name: str):
        super().__init__(name)

    @property
    def impedance(self):
        return self.symbol


class Capacitor(Passive):
    def __init__(self, name: str):
        super().__init__(name)

    @property
    def impedance(self):
        return 1 / (sympy.symbols('s') * self.symbol)


class Inductor(Passive):
    def __init__(self, name: str):
        super().__init__(name)

    @property
    def impedance(self):
        return sympy.symbols('s') * self.symbol


class CurrentSource(Source):
    def __init__(self, name: str):
        super().__init__(name)

    @property
    def value(self):
        return self.symbol

    @property
    def impedance(self):
        return sympy.common.S.Infinity


class VoltageSource(Source):
    def __init__(self, name: str):
        super().__init__(name)

    @property
    def value(self):
        return self.symbol

    @property
    def impedance(self):
        return 0


class DependentCurrentSource(Source):
    def __init__(self, name: str, controlling_element: str, scaling_factor: str = '1'):
        super().__init__(name)
        self._controlling_element = sympy.sympify(controlling_element)
        self._scaling_factor = sympy.sympify(scaling_factor)

    @property
    def controlling_element(self):
        return self._controlling_element

    @property
    def scaling_factor(self):
        return self._scaling_factor

class CurrentControlledCurrentSource(DependentCurrentSource):
    def __init__(self, name, controlling_element, scaling_factor):
        super().__init__(name, controlling_element, scaling_factor)


class VoltageControlledCurrentSource(DependentCurrentSource):
    def __init__(self, name, controlling_element, scaling_factor):
        super().__init__(name, controlling_element, scaling_factor)
