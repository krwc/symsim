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


DEPENDENT_VARS = {
    'I': sympy.Function('I'),
    'V': sympy.Function('V'),
}

class DependentValue:
    class Current:
        def __init__(self, element: Element):
            if not isinstance(element, Passive) and \
                not isinstance(element, CurrentSource):
                raise ValueError('Current can be measured only on passive devices and current sources')
            self.symbol = element.symbol

    class Voltage:
        def __init__(self, element: Element):
            if not isinstance(element, Passive) and \
                not isinstance(element, VoltageSource):
                raise ValueError('Voltage can be measured only on passive devices and voltage sources')
            self.symbol = element.symbol

class DependentCurrentSource(Source):
    def __init__(self, name: str, dependent_value: DependentValue, scaling_factor: str = '1'):
        super().__init__(name)
        self._dependent_value = dependent_value
        self._scaling_factor = sympy.sympify(scaling_factor)

    @property
    def dependent_value(self):
        return self._dependent_value

    @property
    def scaling_factor(self):
        return self._scaling_factor

    @property
    def voltage_controlled(self):
        return isinstance(self.dependent_value, DependentValue.Voltage)

    @property
    def current_controlled(self):
        return isinstance(self.dependent_value, DependentValue.Current)
