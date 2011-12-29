import functools
from inspect import isclass

class TypeCheck(object):
  """
    Encapsulate the results of a type check pass.
  """
  class Error(Exception):
    pass

  @staticmethod
  def success():
    return TypeCheck(True, "")

  @staticmethod
  def failure(msg):
    return TypeCheck(False, msg)

  def __init__(self, success, message):
    self._success = success
    self._message = message

  def message(self):
    return self._message

  def ok(self):
    return self._success

  def __repr__(self):
    if self.ok():
      return 'TypeCheck(OK)'
    else:
      return 'TypeCheck(FAILED): %s' % self._message


class TypeFactoryType(type):
  _TYPE_FACTORIES = {}

  def __new__(mcs, name, parents, attributes):
    if 'PROVIDES' not in attributes:
      return type.__new__(mcs, name, parents, attributes)
    else:
      provides = attributes['PROVIDES']
      new_type = type.__new__(mcs, name, parents, attributes)
      TypeFactoryType._TYPE_FACTORIES[provides] = new_type
      return new_type


TypeFactoryClass = TypeFactoryType('TypeFactoryClass', (object,), {})
class TypeFactory(TypeFactoryClass):
  @staticmethod
  def get_factory(type_name):
    assert type_name in TypeFactoryType._TYPE_FACTORIES, (
      'Unknown type: %s, Existing factories: %s' % (
        type_name, TypeFactoryType._TYPE_FACTORIES.keys()))
    return TypeFactoryType._TYPE_FACTORIES[type_name]

  @staticmethod
  def create(type_dict, *type_parameters):
    """
      Implemented by the TypeFactory to produce a new type.

      Should return:
        reified type
        (with usable type.__name__)
    """
    raise NotImplementedError("create unimplemented for: %s" % repr(type_parameters))

  @staticmethod
  def new(type_dict, type_factory, *type_parameters):
    """
      Create a fully reified type from a type schema.
    """
    type_tuple = (type_factory,) + type_parameters
    if type_tuple not in type_dict:
      factory = TypeFactory.get_factory(type_factory)
      reified_type = factory.create(type_dict, *type_parameters)
      type_dict[type_tuple] = reified_type
    return type_dict[type_tuple]

  @staticmethod
  def wrap(type_info):
    if isinstance(type_info, Type):
      return type_info.serialize_type()
    else:
      raise ValueError("Expected a fully reified type: %s" % type_info)

  @staticmethod
  def wrapper(factory):
    assert issubclass(factory, TypeFactory)
    def wrapper_function(*type_parameters):
      return TypeFactory.new({}, factory.PROVIDES, *tuple(
        [typ.serialize_type() for typ in type_parameters]))
    return wrapper_function

  @staticmethod
  def load(type_tuple, into=None):
    """
      Determine all types touched by loading the type and deposit them into
      the particular namespace.
    """
    type_dict = {}
    TypeFactory.new(type_dict, *type_tuple)
    deposit = into if (into is not None and isinstance(into, dict)) else {}
    for reified_type in type_dict.values():
      deposit[reified_type.__name__] = reified_type
    return deposit


class TypeMetaclass(type):
  def __instancecheck__(cls, other):
    if not hasattr(other, 'type_parameters'):
      return False
    return cls.type_factory() == other.type_factory() and (
      cls.type_parameters() == other.type_parameters())

  def __new__(mcls, name, parents, attributes):
    return type.__new__(mcls, name, parents, attributes)

class Type(object):
  @classmethod
  def type_factory(cls):
    """ Return the name of the factory that produced this class. """
    raise NotImplementedError

  @classmethod
  def type_parameters(cls):
    """ Return the type parameters used to produce this class. """
    raise NotImplementedError

  @classmethod
  def serialize_type(cls):
    return (cls.type_factory(),) + cls.type_parameters()

  def check(self):
    """
      Returns a TypeCheck object explaining whether or not a particular
      instance of this object typechecks.
    """
    raise NotImplementedError
