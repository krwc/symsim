import unittest
import sympy

import network as net
import elements as elem
import solver
import sim

class Test:
    class Base(unittest.TestCase):
        def setUp(self):
            if not getattr(self, 'IN'):
                raise RuntimeError("Please define IN in your test class")
            if not getattr(self, 'OUT'):
                raise RuntimeError("Please define OUT in your test class")

        def runTest(self):
            net, _ = sim.parse_network(self.IN)
            v_out = solver.solve_system(net)

            for node, value in self.OUT.items():
                self.assertEqual(v_out[node].simplify(),
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


class CurrentSourcePushingToGround(Test.Base):
    IN = """
    1 0 I1
    1 0 R1
    """

    OUT = {1: "-I1*R1"}

class CurrentSourcePullingFromGround(Test.Base):
    IN = """
    0 1 I1
    1 0 R1
    """

    OUT = {1: "I1*R1"}

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


#class ConstantVoltageSource(Test.Base):
#    IN = """
#    const Vx
#
#    0 1 V1 3*Vx
#    0 1 R1
#    """
#
#    OUT = {1: "3 * Vx"}
#
#
#class DependentCurrentSource(Test.Base):
#    IN = """
#    const gm
#    var Vx 2 0
#
#    0 1 R1
#    1 0 Ic gm*Vx
#
#    2 0 R2
#    0 2 Vin
#    """
#
#
if __name__ == '__main__':
    unittest.main()