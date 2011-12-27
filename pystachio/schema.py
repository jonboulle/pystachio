import functools
from inspect import isclass

# It seems like Struct should just be a metaclass that just translates the parameters into the 
# tuples understandable by the Type system, because honestly we should just be able to call
# factory.new(parameters) => type
#
# We should just have MapFactory, ListFactory, StructFactory, StringFactory, IntegerFactory, etc.
# The {Integer,String,Float}Factory.new() is parameterless.
# StructFactory.new() takes very rich structured information but is never called directly except
# during type serialization and deserialization.  Mostly StructMetaclass translates the class
# definition directly into this intermediate format.

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
  _PARAMETERS = {}   # parameters => emitted type name
  _TYPES = {}        # type name => fully reified type

  @staticmethod
  def get_factory(type_name):
    assert type_name in TypeFactoryType._TYPE_FACTORIES, (
      'Unknown type: %s, Existing factories: %s' % (
        type_name, TypeFactoryType._TYPE_FACTORIES.keys()))
    return TypeFactoryType._TYPE_FACTORIES[type_name]

  @staticmethod
  def create(*type_parameters):
    """
      Implemented by the TypeFactory to produce a new type.
      
      Should return:
        reified type
        (with usable type.__name__)
    """
    raise NotImplementedError("create unimplemented for: %s" % repr(type_parameters))

  @staticmethod
  def new(type_factory, *type_parameters):
    """
      Memoization of creates.
    """
    type_tuple = (type_factory,) + type_parameters
    print('Type tuple: %s' % repr(type_tuple))
    if type_tuple not in TypeFactory._PARAMETERS:
      factory = TypeFactory.get_factory(type_factory)
      reified_type = factory.create(*type_parameters)
      type_name = reified_type.__name__
      TypeFactory._PARAMETERS[type_tuple] = type_name
      TypeFactory._TYPES[type_name] = reified_type
    return TypeFactory._TYPES[TypeFactory._PARAMETERS[type_tuple]]

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
      return TypeFactory.new(factory.PROVIDES, *tuple(
        [typ.serialize_type() for typ in type_parameters]))
    #def wrapper_function(*type_parameters):
    #  return TypeFactory.new(factory.PROVIDES, *type_parameters)
    return wrapper_function

  @staticmethod
  def load(type_tuple, into=None):
    """
      Determine all types touched by loading the type and deposit them into
      the particular namespace.
      
      If a type takes parameters, we should dump the .create method as the
      PROVIDES type.  Otherwise, we should dump a fully reified type.
      
      For example:
        StringFactory.create() takes no parameters ==> dump StringFactory.PROVIDES as
        the output of StringFactory.create()
        
        MapFactory.create() takes parameters ==> dump MapFactory.PROVIDES as
        MapFactory.create()
        
        StructFactory.create takes parameters ==> but set PROVIDES to Structy, so that
        to create, you do Structy(foooo), then Struct is the metaclass.
      
      That doesn't make any sense.  Load doesn't load any type factories: only reified types.
      And the basic types (String, Integer, etc) should get loaded in course of loading from
      schema.  Don't worry...
    """
    deposit = {}


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
