import pytest
from pystachio.base import MountTable
from pystachio.naming import Ref
from pystachio.objects import Integer
from pystachio.container import List

def dtd(d):
  return dict((Ref.from_address(key), str(val)) for key, val in d.items())

def ref(address):
  return Ref.from_address(address)

def test_environment_constructors():
  oe = MountTable(a = 1, b = 2)
  assert oe._table == dtd({'a': 1, 'b': 2})

  oe = MountTable({'a': 1, 'b': 2})
  assert oe._table == dtd({'a': 1, 'b': 2})

  oe = MountTable({'a': 1}, b = 2)
  assert oe._table == dtd({'a': 1, 'b': 2})

  oe = MountTable({'a': 1}, a = 2)
  assert oe._table == dtd({'a': 2}), "last update should win"

  oe = MountTable({'b': 1}, a = 2)
  assert oe._table == dtd({'a': 2, 'b': 1})
  
  oe = MountTable(oe, a = 3)
  assert oe._table == dtd({'a': 3, 'b': 1})

def test_environment_find():
  oe1 = MountTable(a = { 'b': 1 })
  oe2 = MountTable(a = { 'b': { 'c': List(Integer)([1,2,3]) } } )
  oe = MountTable(oe1, oe2)
  assert oe.find(ref('a.b')) == '1'
  assert oe.find(ref('a.b.c[0]')) == Integer(1)
  assert oe.find(ref('a.b.c[1]')) == Integer(2)
  assert oe.find(ref('a.b.c[2]')) == Integer(3)

def test_environment_merge():
  oe1 = MountTable(a = 1)
  oe2 = MountTable(b = 2)
  assert MountTable(oe1, oe2)._table == {
    ref('a'): '1',
    ref('b'): '2'
  }

  oe1 = MountTable(a = 1, b = 2)
  oe2 = MountTable(a = 1, b = {'c': 2})
  assert MountTable(oe1, oe2)._table == {
    ref('a'): '1',
    ref('b'): '2',
    ref('b.c'): '2'
  }

  oe1 = MountTable(a = 1, b = 2)
  oe2 = MountTable(a = 1, b = {'c': 2})
  assert MountTable(oe2, oe1)._table == {
    ref('a'): '1',
    ref('b'): '2',
    ref('b.c'): '2'
  }

  oe1 = MountTable(a = { 'b': 1 })
  oe2 = MountTable(a = { 'c': 2 })
  assert MountTable(oe1, oe2)._table == {
    ref('a.b'): '1',
    ref('a.c'): '2'
  }
  assert MountTable(oe2, oe1)._table == {
    ref('a.b'): '1',
    ref('a.c'): '2'
  }


def test_environment_bad_values():
  bad_values = [None, type, object()]
  for val in bad_values:
    with pytest.raises(ValueError):
      MountTable(a = val)
