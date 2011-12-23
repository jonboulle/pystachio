from inspect import isclass

# It seems like Struct should just be a metaclass that just translates the parameters into the 
# tuples understandable by the Type system, because honestly we should just be able to call
# factory.new(parameters) => type
#
# 
#

class Type(object):
  _TYPE_FACTORIES = {}
  _TYPES = {}

  @classmethod
  def new(cls):
    return cls

  @classmethod
  def type_name(cls):
    raise NotImplementedError
  
  @classmethod
  def type_parameters(cls):
    return None
  
  @classmethod
  def type_representation(cls):
    return (cls.type_name(), cls.type_parameters())

  @classmethod
  def serialize_type(cls):
    """Given a class, serialize its type structure to something easily deserializable."""
    raise NotImplementedError

  @staticmethod
  def deserialize_type(type_tuple):
    if type_tuple in self._TYPES:
      return self._TYPES[type_tuple]
    type_name, type_parameters = schema
    factory = Type.get_type_factory(type_name)
    if issubclass(factory, ParametricType):
      return factory.new(type_parameters)
    elif issubclass(factory, UnitType):
      return factory
    else:
      # TODO(wickman)  Oops.
      raise ValueError("What are you smoking?")

  @staticmethod
  def register_type_factory(cls):
    assert isclass(cls)
    assert issubclass(cls, Type)
    Type._TYPE_FACTORIES[cls.type_name()] = cls

  @staticmethod
  def get_type_factory(type_name):
    assert type_name in Type._TYPE_FACTORIES, 'Unknown type: %s' % type_name
    return Type._TYPE_FACTORIES[type_name]

  @staticmethod
  def load(into=None):
    deposit = {}

class UnitType(Type):
  pass

class ParametricType(Type):
  @classmethod
  def new(cls, parameters):
    pass

  @classmethod
  def type_parameters(cls):
    """Return the parameters that parameterize this type."""
    raise NotImplementedError
