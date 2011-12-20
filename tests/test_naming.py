from pystachio import (Struct, String, List)
from pystachio.naming import *
from pystachio.environment import Environment

def test_naming():
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
         Employee(first = 'marius')
    ])

  assert Ref('twttr.employees[1].first').resolve(Environment(twttr = twttr)) == String('marius')