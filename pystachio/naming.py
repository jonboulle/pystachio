import copy
from itertools import chain
import re

class Namable(object):
  class Unresolvable(Exception): pass
  
  def lookup(self, name):
    """Return whatever is named by 'name', or raise Namable.Unresolvable"""
    raise NotImplementedError

class Indexed(Namable):
  pass

class Dereferenced(Namable):
  pass


class Ref(object):
  """
    A reference into to a hierarchically named object.

    E.g. "foo" references the name foo.  The reference "foo.bar" references
    the name "bar" in foo's scope.  If foo is not a dictionary, this will
    result in an interpolation/binding error.
  """

  _COMPONENT_RE = re.compile(r'^\w+$')
  _REF_RE = re.compile('(\[\w+\]|\w+)')
  _COMPONENT_SEPARATOR = '.'

  class Component(object):
    def __init__(self, value):
      self._value = value

    @property
    def value(self):
      return self._value

  class IndexedComponent(Component):
    def __repr__(self):
      return '[%s]' % self._value

  class DereferencedComponent(Component):
    def __repr__(self):
      return '.%s' % self._value

  class InvalidRefError(Exception): pass
  class UnnamableError(Exception): pass

  def __init__(self, address):
    self._components = Ref.split_components(address)

  def components(self):
    return self._components
  
  @staticmethod
  def split_components(address):
    def map_to_namable(component):
      if (component.startswith('[') and component.endswith(']') and 
          Ref._COMPONENT_RE.match(component[1:-1])):
        return Ref.IndexedComponent(component[1:-1])
      elif Ref._COMPONENT_RE.match(component):
        return Ref.DereferencedComponent(component)
      else:
        raise Ref.InvalidRefError(component)
    return map(map_to_namable, filter(None,
      [x for x in chain(*map(Ref._REF_RE.split, address.split('.')))]))

  def address(self):
    return ''.join(map(str, self._components))

  def __str__(self):
    return '{{%s}}' % self.address()

  def __repr__(self):
    return 'Ref(%s)' % self.address()

  def __eq__(self, other):
    return str(self) == str(other)

  def __hash__(self):
    return hash(str(self))

  def resolve(self, namable):
    """
      Resolve this Ref in the context of Namable namable.
      
      Raises Namable.Unresolvable on any miss.
    """
    for component in self.components():
      if isinstance(component, Ref.IndexedComponent) and isinstance(namable, Indexed) or (
         isinstance(component, Ref.DereferencedComponent) and isinstance(namable, Dereferenced)):
        namable = namable.lookup(component.value)
      else:
        raise Ref.UnnamableError("Cannot resolve Ref %s from object: %s" % (
          component, repr(namable)))
    return namable
