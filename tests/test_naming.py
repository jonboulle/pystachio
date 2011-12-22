from copy import deepcopy
import pytest

from pystachio import (
  List,
  String,
  Integer,
  Struct,
  Map,
  Required)
from pystachio.naming import Ref, Namable
from pystachio.base import Environment

def makeref(address):
  return Ref.from_address(address)

def test_ref_parsing():
  for input in ['', None, type, 1, 3.0, 'hork bork']:
    with pytest.raises(Ref.InvalidRefError):
      makeref(input)

  makeref('a').components() == [Ref.Dereference('a')]
  makeref('.a').components() == [Ref.Dereference('a')]
  makeref('a.b').components() == [Ref.Dereference('a'), Ref.Dereference('b')]
  makeref('[a]').components() == [Ref.Index('a')]
  makeref('[0].a').components() == [Ref.Index('0'), Ref.Dereference('a')]
  makeref('[0][a]').components() == [Ref.Index('0'), Ref.Index('a')]
  for refstr in ['[a]b', '[]', '[[a]', 'b[[[', 'a.1', '1.a', '.[a]', '0']:
    with pytest.raises(Ref.InvalidRefError):
      makeref(refstr)


def test_ref_lookup():
  oe = Environment(a = 1)
  assert oe.find(makeref("a")) == '1'

  oe = Environment(a = {'b': 1})
  assert oe.find(makeref("a.b")) == '1'

  oe = Environment(a = {'b': {'c': 1}, 'c': Environment(d = 2)})
  assert oe.find(makeref('a.b.c')) == '1'
  assert oe.find(makeref('a.c.d')) == '2'

  for address in ["a", "a.b", "a.c"]:
    with pytest.raises(Namable.NotFound):
      oe.find(makeref(address))

  oe = List(String)(["a", "b", "c"])
  assert oe.find(makeref('[0]')) == String('a')
  with pytest.raises(Namable.NotFound):
    oe.find(makeref('[3]'))

  oe = List(Map(String,Integer))([{'a': 27}])
  oe.find(makeref('[0][a]')) == Integer(27)
  Environment(foo = oe).find(makeref('foo[0][a]')) == Integer(27)

def test_complex_lookup():
  class Employee(Struct):
    first = String
    last = String

  class Employer(Struct):
    name = String
    employees = List(Employee)

  twttr = Employer(
    name = 'Twitter',
    employees = [
         Employee(first = 'brian', last = 'wickman'),
         Employee(first = 'marius'),
         Employee(last = '{{default.last}}')
    ])


  assert Environment(twttr = twttr).find(makeref('twttr.employees[1].first')) == String('marius')
  assert Map(String,Employer)({'twttr': twttr}).find(makeref('[twttr].employees[1].first')) == String('marius')
  assert List(Employer)([twttr]).find(makeref('[0].employees[0].last')) == String('wickman')
  assert List(Employer)([twttr]).find(makeref('[0].employees[2].last')) == String('{{default.last}}')

def test_scope_lookup():
  refs = [makeref('mesos.ports[health]'), makeref('mesos.config'), makeref('logrotate.filename'),
          makeref('mesos.ports.http')]
  scoped_refs = filter(None, map(makeref('mesos.ports').scoped_to, refs))
  assert scoped_refs == [makeref('[health]'), makeref('http')]

  refs = [makeref('[a]'), makeref('[a][b]'), makeref('[a].b')]
  scoped_refs = filter(None, map(makeref('[a]').scoped_to, refs))
  assert scoped_refs == [makeref('[b]'), makeref('b')]

def test_scope_override():
  class MesosConfig(Struct):
    ports = Map(String, Integer)
  config = MesosConfig(ports = {'http': 80, 'health': 8888})
  env = Environment({makeref('config.ports[http]'): 5000}, config = config)
  assert env.find(makeref('config.ports[http]')) == '5000'
  assert env.find(makeref('config.ports[health]')) == Integer(8888)

def test_inherited_scope():
  class PhoneBookEntry(Struct):
    name = Required(String)
    number = Required(Integer)

  class PhoneBook(Struct):
    city = Required(String)
    people = List(PhoneBookEntry)

  sf = PhoneBook(city = "San Francisco").bind(areacode = 415)
  sj = PhoneBook(city = "San Jose").bind(areacode = 408)
  jenny = PhoneBookEntry(name = "Jenny", number = "{{areacode}}8675309")
  brian = PhoneBookEntry(name = "Brian", number = "{{areacode}}5551234")
  brian = brian.bind(areacode = 402)
  sfpb = sf(people = [jenny, brian])
  assert sfpb.find(makeref('people[0].number')) == Integer(4158675309)
  assert sfpb.bind(areacode = 999).find(makeref('people[0].number')) == Integer(9998675309)
  assert sfpb.find(makeref('people[1].number')) == Integer(4025551234)
  assert sfpb.bind(areacode = 999).find(makeref('people[1].number')) == Integer(4025551234)


def test_deepcopy_preserves_bindings():
  class PhoneBookEntry(Struct):
    name = Required(String)
    number = Required(Integer)
  brian = PhoneBookEntry(number = "{{areacode}}5551234")
  brian = brian.bind(areacode = 402)
  briancopy = deepcopy(brian)
  assert brian.find(makeref('number')) == Integer(4025551234)
  assert briancopy.find(makeref('number')) == Integer(4025551234)
