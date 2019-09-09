import collections

from . import elements as elem

class Edge(collections.namedtuple('Edge', ['u', 'v', 'element'])):
    def __new__(cls, u, v, element: elem.Element):
        assert isinstance(element, elem.Element)
        self = super().__new__(cls, str(u), str(v), element)
        return self
