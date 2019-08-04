import unittest
import sympy

from sim import parse_network, solve_system


class Test:
    class Base(unittest.TestCase):
        def setUp(self):
            if not getattr(self, 'IN'):
                raise RuntimeError("Please define IN in your test class")
            if not getattr(self, 'OUT'):
                raise RuntimeError("Please define OUT in your test class")

        def runTest(self):
            net = parse_network(self.IN)
            out, elem_index = solve_system(net)

            for node, value in self.OUT.items():
                self.assertEqual(out[elem_index[node]].simplify(),
                                 sympy.sympify(value).simplify())


class VoltageSourceParalelWithResistor(Test.Base):
    IN = """
    0 1 R1
    1 0 V1
    """
    OUT = {1: "-V1"}


class VoltageSourceBetweenTwoResistors(Test.Base):
    IN = """
    0 1 R1
    1 2 V3
    2 0 R2
    """

    OUT = {1: "-R1 * V3 / (R1 + R2)"}


class CurrentSource(Test.Base):
    IN = """
    0 1 I1
    1 2 R1
    2 0 R2
    """

    OUT = {1: "I1*(R1 + R2)", 2: "I1*R2"}


class VoltageSourceRlc(Test.Base):
    IN = """
    0 1 C1
    0 1 L1
    1 2 V3
    2 0 R2
    """

    OUT = {1: "-L1*V3*s/(L1*s + R2*(C1*L1*s**2 + 1))",
           2: "R2*V3*(C1*L1*s**2 + 1)/(L1*s + R2*(C1*L1*s**2 + 1))"}


class ConstantAndNoSource(Test.Base):
    IN = """
    const gm

    0 1 R1
    """

    OUT = {1: '0'}


class ConstantVoltageSource(Test.Base):
    IN = """
    const Vx

    0 1 V1 3*Vx
    0 1 R1
    """

    OUT = {1: "3 * Vx"}


if __name__ == '__main__':
    unittest.main()
