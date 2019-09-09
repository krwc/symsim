import unittest
import sympy

import network as net
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
            v_out, _ = solver.solve_system(net)

            for node, value in self.OUT.items():
                self.assertEqual(v_out[node].simplify(),
                                 sympy.sympify(value).simplify())


class VoltageSourceParalelWithResistor(Test.Base):
    IN = """
    R1 0 1
    V1 1 0
    """
    OUT = {'1': "-V1"}


class VoltageSourceBetweenTwoResistors(Test.Base):
    IN = """
    R1 0 1
    V3 1 2
    R2 2 0
    """

    OUT = {'1': "-R1 * V3 / (R1 + R2)"}


class CurrentSource(Test.Base):
    IN = """
    I1 0 1
    R1 1 2
    R2 2 0
    """

    OUT = {'1': "I1*(R1 + R2)", '2': "I1*R2"}


class CurrentSourcePushingToGround(Test.Base):
    IN = """
    I1 1 0
    R1 1 0
    """

    OUT = {'1': "-I1*R1"}

class CurrentSourcePullingFromGround(Test.Base):
    IN = """
    I1 0 1
    R1 1 0
    """

    OUT = {'1': "I1*R1"}

class VoltageSourceRlc(Test.Base):
    IN = """
    C1 0 1
    L1 0 1
    V3 1 2
    R2 2 0
    """

    OUT = {'1': "-L1*V3*s/(L1*s + R2*(C1*L1*s**2 + 1))",
           '2': "R2*V3*(C1*L1*s**2 + 1)/(L1*s + R2*(C1*L1*s**2 + 1))"}

class SmallCaseNames(Test.Base):
    IN = """
    r1 0 1
    v1 0 1
    """

    OUT = {'1': 'v1'}

class StringNodeNames(Test.Base):
    IN = """
    r1 0 node1
    v1 0 node1
    """

    OUT = {'node1': 'v1'}

if __name__ == '__main__':
    unittest.main()
