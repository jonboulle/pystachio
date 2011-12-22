from pprint import pformat

from pystachio.naming import (
  Ref,
  Namable)

class MountTable(Namable):
  """
    A map from Ref => Object used for Mustache bindings.
  """

  @staticmethod
  def wrap(value):
    if isinstance(value, dict):
      return MountTable(value)
    elif isinstance(value, (MountTable, ObjectBase)):
      return value
    else:
      if isinstance(value, (int, long, float, basestring)):
        return str(value)
      else:
        raise ValueError('Error in MountTable.wrap(%s)' % repr(value))

  def _assimilate_dictionary(self, d):
    for key, val in d.items():
      val = MountTable.wrap(val)
      rkey = Ref.wrap(key)
      if isinstance(val, MountTable):
        for vkey, vval in val._table.items():
          self._table[rkey + vkey] = vval
      else:
        self._table[rkey] = val
  
  def _assimilate_table(self, mt):
    for key, val in mt._table.items():
      self._table[key] = val

  def __init__(self, *dicts, **kw):
    self._table = {}
    for d in list(dicts) + [kw]:
      if isinstance(d, dict):
        self._assimilate_dictionary(d)
      elif isinstance(d, MountTable):
        self._assimilate_table(d)
      else:
        raise ValueError("MountTable expects dict or MountTable, got %s" % repr(d))

  def find(self, ref):
    if ref in self._table:
      return self._table[ref]
    targets = [key for key in self._table if Ref.subscope(key, ref)]
    if not targets:
      raise Namable.NotFound(self, ref)
    else:
      for key in sorted(targets, cmp=Ref.compare, reverse=True):
        scope = self._table[key]
        if not isinstance(scope, Namable):
          continue
        subscope = Ref.subscope(key, ref)
        if subscope.is_empty():
          return scope
        else:
          try:
            resolved = scope.find(subscope)
            return resolved
          except Namable.Error as e:
            continue
    raise KeyError(ref)

  def __repr__(self):
    return 'MountTable(%s)' % pformat(self._table)

class ObjectBase(object):
  """
    ObjectBase base class, encapsulating a set of variable bindings scoped to this object.
  """

  class InterpolationError(Exception): pass

  @classmethod
  def checker(cls, obj):
    raise NotImplementedError

  def __init__(self):
    self._scopes = []

  def get(self):
    raise NotImplementedError

  def __hash__(self):
    si, _ = self.interpolate()
    return hash(si.get())

  def copy(self):
    """
      Return a copy of this object.
    """
    raise NotImplementedError

  @staticmethod
  def translate_to_scopes(*args, **kw):
    scopes = []
    for arg in args:
      scopes.append(arg if isinstance(arg, Namable) else MountTable.wrap(arg))
    scopes.extend([MountTable(kw)] if kw else [])
    return scopes

  def bind(self, *args, **kw):
    """
      Bind environment variables into this object's scope.
    """
    new_self = self.copy()
    new_scopes = ObjectBase.translate_to_scopes(*args, **kw)
    new_self._scopes = list(reversed(new_scopes)) + new_self._scopes
    return new_self

  def in_scope(self, *args, **kw):
    """
      Scope this object to a parent environment (like bind but reversed.)
    """
    new_self = self.copy()
    new_scopes = ObjectBase.translate_to_scopes(*args, **kw)
    new_self._scopes = new_self._scopes + new_scopes
    return new_self

  def scopes(self):
    return self._scopes

  def check(self):
    """
      Type check this object.
    """
    si, _ = self.interpolate()
    return self.checker(si)

  def __ne__(self, other):
    return not (self == other)

  def __mod__(self, namable):
    if isinstance(namable, dict):
      namable = MountTable.wrap(namable)
    interp, _ = self.in_scope(namable).interpolate()
    return interp

  def interpolate(self):
    """
      Interpolate this object in the context of the Object's environment.

      Should return a 2-tuple:
        The object with as much interpolated as possible.
        The remaining unbound Refs necessary to fully interpolate the object.

      If the object is fully interpolated, it should be typechecked prior to
      return.
    """
    raise NotImplementedError