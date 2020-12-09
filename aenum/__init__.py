"""Python Advanced Enumerations & NameTuples"""

import sys as _sys
pyver = float('%s.%s' % _sys.version_info[:2])

import re

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict
from collections import defaultdict
try:
    import sqlite3
except ImportError:
    sqlite3 = None

if pyver >= 3:
    from functools import reduce

from operator import or_ as _or_, and_ as _and_, xor as _xor_, inv as _inv_
from operator import abs as _abs_, add as _add_, floordiv as _floordiv_
from operator import lshift as _lshift_, rshift as _rshift_, mod as _mod_
from operator import mul as _mul_, neg as _neg_, pos as _pos_, pow as _pow_
from operator import truediv as _truediv_, sub as _sub_
if pyver < 3:
    from operator import div as _div_

if pyver >= 3:
    from inspect import getfullargspec
    def getargspec(method):
        args, varargs, keywords, defaults, _, _, _ = getfullargspec(method)
        return args, varargs, keywords, defaults
else:
    from inspect import getargspec


__all__ = [
        'NamedConstant', 'constant', 'skip', 'nonmember', 'member', 'no_arg',
        'Enum', 'IntEnum', 'AutoNumberEnum', 'OrderedEnum', 'UniqueEnum',
        'StrEnum', 'UpperStrEnum', 'LowerStrEnum',
        'Flag', 'IntFlag',
        'AutoNumber', 'MultiValue', 'NoAlias', 'Unique',
        'enum', 'extend_enum', 'unique', 'enum_property',
        'NamedTuple', 'SqliteEnum',
        ]
if sqlite3 is None:
    __all__.remove('SqliteEnum')

version = 2, 2, 6

try:
    any
except NameError:
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False

try:
    basestring
except NameError:
    # In Python 2 basestring is the ancestor of both str and unicode
    # in Python 3 it's just str, but was missing in 3.1
    basestring = str

try:
    unicode
except NameError:
    # In Python 3 unicode no longer exists (it's just str)
    unicode = str

try:
    long
    baseinteger = int, long
except NameError:
    baseinteger = int
# deprecated
baseint = baseinteger

try:
    NoneType
except NameError:
    NoneType = type(None)

try:
    # derive from stdlib enum if possible
    import enum
    if hasattr(enum, 'version'):
        StdlibEnumMeta = StdlibEnum = None
    else:
        from enum import EnumMeta as StdlibEnumMeta, Enum as StdlibEnum
    del enum
except ImportError:
    StdlibEnumMeta = StdlibEnum = None

# will be exported later
AutoValue = AutoNumber = MultiValue = NoAlias = Unique = None

class enum_property(object):
    """
    This is a descriptor, used to define attributes that act differently
    when accessed through an enum member and through an enum class.
    Instance access is the same as property(), but access to an attribute
    through the enum class will look in the class' _member_map_.
    """

    def __init__(self, fget=None, doc=None, name=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.name = name

    def __call__(self, func, doc=None):
        self.fget = func
        self.__doc__ = self.__doc__ or doc or func.__doc__

    def __get__(self, instance, ownerclass=None):
        if instance is None:
            try:
                return ownerclass._member_map_[self.name]
            except KeyError:
                raise AttributeError('%r not found in %r' % (self.name, ownerclass.__name__))
        else:
            if self.fget is not None:
                return self.fget(instance)
            else:
                # search through mro
                for base in ownerclass.__mro__[1:]:
                    if self.name in base.__dict__:
                        attr = base.__dict__[self.name]
                        break
                else:
                    raise AttributeError('%r not found in %r' % (self.name, instance))
                if isinstance(attr, classmethod):
                    attr = attr.__func__
                    return lambda *args, **kwds: attr(ownerclass, *args, **kwds)
                elif isinstance(attr, staticmethod):
                    return attr.__func__
                elif isinstance(attr, (property, enum_property)):
                    return attr.__get__(instance, ownerclass)
                elif callable(attr):
                    return lambda *arg, **kwds: attr(instance, *arg, **kwds)
                else:
                    return attr

    def __set__(self, instance, value):
        ownerclass = instance.__class__
        for base in ownerclass.__mro__[1:]:
            if self.name in base.__dict__:
                attr = base.__dict__[self.name]
                if isinstance(attr, property):
                    setter = attr.__set__
                    if setter is not None:
                        return setter(instance, value)
        else:
            raise AttributeError("can't set attribute %r" % (self.name, ))

    def __delete__(self, instance):
        raise AttributeError("can't delete attribute %r" % (self.name, ))

_RouteClassAttributeToGetattr = enum_property

class NonMember(object):
    """
    Protects item from becaming an Enum member during class creation.
    """
    def __init__(self, value):
        self.value = value

    def __get__(self, instance, ownerclass=None):
        return self.value
skip = nonmember = NonMember

class Member(object):
    """
    Forces item to became an Enum member during class creation.
    """
    def __init__(self, value):
        self.value = value
member = Member

class _NoInitSubclass(object):
    @classmethod
    def __init_subclass__(cls, **kwds):
        pass

def _is_descriptor(obj):
    """Returns True if obj is a descriptor, False otherwise."""
    return (
            hasattr(obj, '__get__') or
            hasattr(obj, '__set__') or
            hasattr(obj, '__delete__'))


def _is_dunder(name):
    """Returns True if a __dunder__ name, False otherwise."""
    return (len(name) > 4 and
            name[:2] == name[-2:] == '__' and
            name[2] != '_' and
            name[-3] != '_')


def _is_sunder(name):
    """Returns True if a _sunder_ name, False otherwise."""
    return (len(name) > 2 and
            name[0] == name[-1] == '_' and
            name[1] != '_' and
            name[-2] != '_')

def _is_internal_class(cls_name, obj):
    # only 3.3 and up, always return False in 3.2 and below
    if pyver < 3.3:
        return False
    else:
        qualname = getattr(obj, '__qualname__', False)
        return not _is_descriptor(obj) and qualname and re.search(r"\.?%s\.\w+$" % cls_name, qualname)

def _is_private_name(cls_name, name):
    pattern = '^_%s__\w+[^_]_?$' % (cls_name, )
    return re.search(pattern, name)

def _make_class_unpicklable(cls):
    """Make the given class un-picklable."""
    def _break_on_call_reduce(self, protocol=None):
        raise TypeError('%r cannot be pickled' % (self, ))
    cls.__reduce_ex__ = _break_on_call_reduce
    cls.__module__ = '<unknown>'

def _check_auto_args(method):
    """check if new generate method supports *args and **kwds"""
    if isinstance(method, staticmethod):
        method = method.__get__(type)
    method = getattr(method, 'im_func', method)
    args, varargs, keywords, defaults = getargspec(method)
    return varargs is not None and keywords is not None

def _get_attr_from_chain(cls, attr):
    sentinel = object()
    for basecls in cls.mro():
        obj = basecls.__dict__.get(attr, sentinel)
        if obj is not sentinel:
            return obj

def _value(obj):
    if isinstance(obj, (auto, constant)):
        return obj.value
    else:
        return obj

################
# Constant stuff
################

# metaclass and class dict for NamedConstant

class constant(object):
    '''
    Simple constant descriptor for NamedConstant and Enum use.
    '''
    def __init__(self, value, doc=None):
        self.value = value
        self.__doc__ = doc

    def __get__(self, *args):
        return self.value

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.value)

    def __and__(self, other):
        return _and_(self.value, _value(other))

    def __rand__(self, other):
        return _and_(_value(other), self.value)

    def __invert__(self):
        return _inv_(self.value)

    def __or__(self, other):
        return _or_(self.value, _value(other))

    def __ror__(self, other):
        return _or_(_value(other), self.value)

    def __xor__(self, other):
        return _xor_(self.value, _value(other))

    def __rxor__(self, other):
        return _xor_(_value(other), self.value)

    def __abs__(self):
        return _abs_(self.value)

    def __add__(self, other):
        return _add_(self.value, _value(other))

    def __radd__(self, other):
        return _add_(_value(other), self.value)

    def __neg__(self):
        return _neg_(self.value)

    def __pos__(self):
        return _pos_(self.value)

    if pyver < 3:
        def __div__(self, other):
            return _div_(self.value, _value(other))

    def __rdiv__(self, other):
        return _div_(_value(other), (self.value))

    def __floordiv__(self, other):
        return _floordiv_(self.value, _value(other))

    def __rfloordiv__(self, other):
        return _floordiv_(_value(other), self.value)

    def __truediv__(self, other):
        return _truediv_(self.value, _value(other))

    def __rtruediv__(self, other):
        return _truediv_(_value(other), self.value)

    def __lshift__(self, other):
        return _lshift_(self.value, _value(other))

    def __rlshift__(self, other):
        return _lshift_(_value(other), self.value)

    def __rshift__(self, other):
        return _rshift_(self.value, _value(other))

    def __rrshift__(self, other):
        return _rshift_(_value(other), self.value)

    def __mod__(self, other):
        return _mod_(self.value, _value(other))

    def __rmod__(self, other):
        return _mod_(_value(other), self.value)

    def __mul__(self, other):
        return _mul_(self.value, _value(other))

    def __rmul__(self, other):
        return _mul_(_value(other), self.value)

    def __pow__(self, other):
        return _pow_(self.value, _value(other))

    def __rpow__(self, other):
        return _pow_(_value(other), self.value)

    def __sub__(self, other):
        return _sub_(self.value, _value(other))

    def __rsub__(self, other):
        return _sub_(_value(other), self.value)



NamedConstant = None

class _NamedConstantDict(dict):
    """Track constant order and ensure names are not reused.

    NamedConstantMeta will use the names found in self._names as the
    Constant names.
    """
    def __init__(self):
        super(_NamedConstantDict, self).__init__()
        self._names = []

    def __setitem__(self, key, value):
        """Changes anything not dundered or not a constant descriptor.

        If an constant name is used twice, an error is raised; duplicate
        values are not checked for.

        Single underscore (sunder) names are reserved.
        """
        if _is_sunder(key):
            raise ValueError(
                    '_sunder_ names, such as %r, are reserved for future NamedConstant use'
                    % (key, )
                    )
        elif _is_dunder(key):
            pass
        elif key in self._names:
            # overwriting an existing constant?
            raise TypeError('attempt to reuse name: %r' % (key, ))
        elif isinstance(value, constant) or not _is_descriptor(value):
            if key in self:
                # overwriting a descriptor?
                raise TypeError('%s already defined as: %r' % (key, self[key]))
            self._names.append(key)
        super(_NamedConstantDict, self).__setitem__(key, value)


class NamedConstantMeta(type):
    """
    Block attempts to reassign NamedConstant attributes.
    """

    def __new__(metacls, cls, bases, clsdict):
        if type(clsdict) is dict:
            original_dict = clsdict
            clsdict = _NamedConstantDict()
            for k, v in original_dict.items():
                clsdict[k] = v
        newdict = {}
        constants = {}
        for name, obj in clsdict.items():
            if name in clsdict._names:
                constants[name] = obj
                continue
            elif isinstance(obj, nonmember):
                obj = obj.value
            newdict[name] = obj
        newcls = super(NamedConstantMeta, metacls).__new__(metacls, cls, bases, newdict)
        newcls._named_constant_cache_ = {}
        newcls._members_ = {}
        for name, obj in constants.items():
            new_k = newcls.__new__(newcls, name, obj)
            newcls._members_[name] = new_k
        return newcls

    def __bool__(cls):
        return True

    def __delattr__(cls, attr):
        cur_obj = cls.__dict__.get(attr)
        if NamedConstant is not None and isinstance(cur_obj, NamedConstant):
            raise AttributeError('cannot delete constant <%s.%s>' % (cur_obj.__class__.__name__, cur_obj._name_))
        super(NamedConstantMeta, cls).__delattr__(attr)

    def __iter__(cls):
        return (k for k in cls._members_.values())

    def __reversed__(cls):
        return (k for k in reversed(cls._members_.values()))

    def __len__(cls):
        return len(cls._members_)

    __nonzero__ = __bool__

    def __setattr__(cls, name, value):
        """Block attempts to reassign NamedConstants.
        """
        cur_obj = cls.__dict__.get(name)
        if NamedConstant is not None and isinstance(cur_obj, NamedConstant):
            raise AttributeError('cannot rebind constant <%s.%s>' % (cur_obj.__class__.__name__, cur_obj._name_))
        super(NamedConstantMeta, cls).__setattr__(name, value)

temp_constant_dict = {}
temp_constant_dict['__doc__'] = "NamedConstants protection.\n\n    Derive from this class to lock NamedConstants.\n\n"

def __new__(cls, name, value=None, doc=None):
    if value is None:
        # lookup, name is value
        value = name
        for name, obj in cls.__dict__.items():
            if isinstance(obj, cls) and obj._value_ == value:
                return obj
        else:
            raise ValueError('%r does not exist in %r' % (value, cls.__name__))
    cur_obj = cls.__dict__.get(name)
    if isinstance(cur_obj, NamedConstant):
        raise AttributeError('cannot rebind constant <%s.%s>' % (cur_obj.__class__.__name__, cur_obj._name_))
    elif isinstance(value, constant):
        doc = doc or value.__doc__
        value = value.value
    metacls = cls.__class__
    if isinstance(value, NamedConstant):
        # constants from other classes are reduced to their actual value
        value = value._value_
    actual_type = type(value)
    value_type = cls._named_constant_cache_.get(actual_type)
    if value_type is None:
        value_type = type(cls.__name__, (cls, type(value)), {})
        cls._named_constant_cache_[type(value)] = value_type
    obj = actual_type.__new__(value_type, value)
    obj._name_ = name
    obj._value_ = value
    obj.__doc__ = doc
    cls._members_[name] = obj
    metacls.__setattr__(cls, name, obj)
    return obj
temp_constant_dict['__new__'] = __new__
del __new__

def __repr__(self):
    return "<%s.%s: %r>" % (
            self.__class__.__name__, self._name_, self._value_)
temp_constant_dict['__repr__'] = __repr__
del __repr__

def __reduce_ex__(self, proto):
    return getattr, (self.__class__, self._name_)
temp_constant_dict['__reduce_ex__'] = __reduce_ex__
del __reduce_ex__


NamedConstant = NamedConstantMeta('NamedConstant', (object, ), temp_constant_dict)
Constant = NamedConstant
del temp_constant_dict

# now for a NamedTuple

class _NamedTupleDict(OrderedDict):
    """Track field order and ensure field names are not reused.

    NamedTupleMeta will use the names found in self._field_names to translate
    to indices.
    """
    def __init__(self, *args, **kwds):
        self._field_names = []
        super(_NamedTupleDict, self).__init__(*args, **kwds)

    def __setitem__(self, key, value):
        """Records anything not dundered or not a descriptor.

        If a field name is used twice, an error is raised.

        Single underscore (sunder) names are reserved.
        """
        if _is_sunder(key):
            if key not in ('_size_', '_order_'):
                raise ValueError(
                        '_sunder_ names, such as %r, are reserved for future NamedTuple use'
                        % (key, )
                        )
        elif _is_dunder(key):
            if key == '__order__':
                key = '_order_'
        elif key in self._field_names:
            # overwriting a field?
            raise TypeError('attempt to reuse field name: %r' % (key, ))
        elif not _is_descriptor(value):
            if key in self:
                # field overwriting a descriptor?
                raise TypeError('%s already defined as: %r' % (key, self[key]))
            self._field_names.append(key)
        super(_NamedTupleDict, self).__setitem__(key, value)


class _TupleAttributeAtIndex(object):

    def __init__(self, name, index, doc, default):
        self.name = name
        self.index = index
        if doc is undefined:
            doc = None
        self.__doc__ = doc
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if len(instance) <= self.index:
            raise AttributeError('%s instance has no value for %s' % (instance.__class__.__name__, self.name))
        return instance[self.index]

    def __repr__(self):
        return '%s(%d)' % (self.__class__.__name__, self.index)


class undefined(object):
    def __repr__(self):
        return 'undefined'
    def __bool__(self):
        return False
    __nonzero__ = __bool__
undefined = undefined()


class TupleSize(NamedConstant):
    fixed = constant('fixed', 'tuple length is static')
    minimum = constant('minimum', 'tuple must be at least x long (x is calculated during creation')
    variable = constant('variable', 'tuple length can be anything')

class NamedTupleMeta(type):
    """Metaclass for NamedTuple"""

    @classmethod
    def __prepare__(metacls, cls, bases, size=undefined):
        return _NamedTupleDict()

    def __init__(cls, *args , **kwds):
        super(NamedTupleMeta, cls).__init__(*args)

    def __new__(metacls, cls, bases, clsdict, size=undefined):
        if bases == (object, ):
            bases = (tuple, object)
        elif tuple not in bases:
            if object in bases:
                index = bases.index(object)
                bases = bases[:index] + (tuple, ) + bases[index:]
            else:
                bases = bases + (tuple, )
        # include any fields from base classes
        base_dict = _NamedTupleDict()
        namedtuple_bases = []
        for base in bases:
            if isinstance(base, NamedTupleMeta):
                namedtuple_bases.append(base)
        i = 0
        if namedtuple_bases:
            for name, index, doc, default in metacls._convert_fields(*namedtuple_bases):
                base_dict[name] = index, doc, default
                i = max(i, index)
        # construct properly ordered dict with normalized indexes
        for k, v in clsdict.items():
            base_dict[k] = v
        original_dict = base_dict
        if size is not undefined and '_size_' in original_dict:
            raise TypeError('_size_ cannot be set if "size" is passed in header')
        add_order = isinstance(clsdict, _NamedTupleDict)
        clsdict = _NamedTupleDict()
        clsdict.setdefault('_size_', size or TupleSize.fixed)
        unnumbered = OrderedDict()
        numbered = OrderedDict()
        _order_ = original_dict.pop('_order_', [])
        if _order_ :
            _order_ = _order_.replace(',',' ').split()
            add_order = False
        # and process this class
        for k, v in original_dict.items():
            if k not in original_dict._field_names:
                clsdict[k] = v
            else:
                # TODO:normalize v here
                if isinstance(v, baseinteger):
                    # assume an offset
                    v = v, undefined, undefined
                    i = v[0] + 1
                    target = numbered
                elif isinstance(v, basestring):
                    # assume a docstring
                    if add_order:
                        v = i, v, undefined
                        i += 1
                        target = numbered
                    else:
                        v = undefined, v, undefined
                        target = unnumbered
                elif isinstance(v, tuple) and len(v) in (2, 3) and isinstance(v[0], baseinteger) and isinstance(v[1], (basestring, NoneType)):
                    # assume an offset, a docstring, and (maybe) a default
                    if len(v) == 2:
                        v = v + (undefined, )
                    v = v
                    i = v[0] + 1
                    target = numbered
                elif isinstance(v, tuple) and len(v) in (1, 2) and isinstance(v[0], (basestring, NoneType)):
                    # assume a docstring, and (maybe) a default
                    if len(v) == 1:
                        v = v + (undefined, )
                    if add_order:
                        v = (i, ) + v
                        i += 1
                        target = numbered
                    else:
                        v = (undefined, ) + v
                        target = unnumbered
                else:
                    # refuse to guess further
                    raise ValueError('not sure what to do with %s=%r (should be OFFSET [, DOC [, DEFAULT]])' % (k, v))
                target[k] = v
        # all index values have been normalized
        # deal with _order_ (or lack thereof)
        fields = []
        aliases = []
        seen = set()
        max_len = 0
        if not _order_:
            if unnumbered:
                raise ValueError("_order_ not specified and OFFSETs not declared for %r" % (unnumbered.keys(), ))
            for name, (index, doc, default) in sorted(numbered.items(), key=lambda nv: (nv[1][0], nv[0])):
                if index in seen:
                    aliases.append(name)
                else:
                    fields.append(name)
                    seen.add(index)
                    max_len = max(max_len, index + 1)
            offsets = numbered
        else:
            # check if any unnumbered not in _order_
            missing = set(unnumbered) - set(_order_)
            if missing:
                raise ValueError("unable to order fields: %s (use _order_ or specify OFFSET" % missing)
            offsets = OrderedDict()
            # if any unnumbered, number them from their position in _order_
            i = 0
            for k in _order_:
                try:
                    index, doc, default = unnumbered.pop(k, None) or numbered.pop(k)
                except IndexError:
                    raise ValueError('%s (from _order_) not found in %s' % (k, cls))
                if index is not undefined:
                    i = index
                if i in seen:
                    aliases.append(k)
                else:
                    fields.append(k)
                    seen.add(i)
                offsets[k] = i, doc, default
                i += 1
                max_len = max(max_len, i)
            # now handle anything in numbered
            for k, (index, doc, default) in sorted(numbered.items(), key=lambda nv: (nv[1][0], nv[0])):
                if index in seen:
                    aliases.append(k)
                else:
                    fields.append(k)
                    seen.add(index)
                offsets[k] = index, doc, default
                max_len = max(max_len, index+1)

        # at this point fields and aliases should be ordered lists, offsets should be an
        # OrdededDict with each value an int, str or None or undefined, default or None or undefined
        assert len(fields) + len(aliases) == len(offsets), "number of fields + aliases != number of offsets"
        assert set(fields) & set(offsets) == set(fields), "some fields are not in offsets: %s" % set(fields) & set(offsets)
        assert set(aliases) & set(offsets) == set(aliases), "some aliases are not in offsets: %s" % set(aliases) & set(offsets)
        for name, (index, doc, default) in offsets.items():
            assert isinstance(index, baseinteger), "index for %s is not an int (%s:%r)" % (name, type(index), index)
            assert isinstance(doc, (basestring, NoneType)) or doc is undefined, "doc is not a str, None, nor undefined (%s:%r)" % (name, type(doc), doc)

        # create descriptors for fields
        for name, (index, doc, default) in offsets.items():
            clsdict[name] = _TupleAttributeAtIndex(name, index, doc, default)
        clsdict['__slots__'] = ()

        # create our new NamedTuple type
        namedtuple_class = super(NamedTupleMeta, metacls).__new__(metacls, cls, bases, clsdict)
        namedtuple_class._fields_ = fields
        namedtuple_class._aliases_ = aliases
        namedtuple_class._defined_len_ = max_len
        return namedtuple_class

    @staticmethod
    def _convert_fields(*namedtuples):
        "create list of index, doc, default triplets for cls in namedtuples"
        all_fields = []
        for cls in namedtuples:
            base = len(all_fields)
            for field in cls._fields_:
                desc = getattr(cls, field)
                all_fields.append((field, base+desc.index, desc.__doc__, desc.default))
        return all_fields

    def __add__(cls, other):
        "A new NamedTuple is created by concatenating the _fields_ and adjusting the descriptors"
        if not isinstance(other, NamedTupleMeta):
            return NotImplemented
        return NamedTupleMeta('%s%s' % (cls.__name__, other.__name__), (cls, other), {})

    def __call__(cls, *args, **kwds):
        """Creates a new NamedTuple class or an instance of a NamedTuple subclass.

        NamedTuple should have args of (class_name, names, module)

            `names` can be:

                * A string containing member names, separated either with spaces or
                  commas.  Values are auto-numbered from 1.
                * An iterable of member names.  Values are auto-numbered from 1.
                * An iterable of (member name, value) pairs.
                * A mapping of member name -> value.

                `module`, if set, will be stored in the new class' __module__ attribute;

                Note: if `module` is not set this routine will attempt to discover the
                calling module by walking the frame stack; if this is unsuccessful
                the resulting class will not be pickleable.

        subclass should have whatever arguments and/or keywords will be used to create an
        instance of the subclass
        """
        if cls is NamedTuple:
            original_args = args
            original_kwds = kwds.copy()
            # create a new subclass
            try:
                if 'class_name' in kwds:
                    class_name = kwds.pop('class_name')
                else:
                    class_name, args = args[0], args[1:]
                if 'names' in kwds:
                    names = kwds.pop('names')
                else:
                    names, args = args[0], args[1:]
                if 'module' in kwds:
                    module = kwds.pop('module')
                elif args:
                    module, args = args[0], args[1:]
                else:
                    module = None
                if 'type' in kwds:
                    type = kwds.pop('type')
                elif args:
                    type, args = args[0], args[1:]
                else:
                    type = None

            except IndexError:
                raise TypeError('too few arguments to NamedTuple: %s, %s' % (original_args, original_kwds))
            if args or kwds:
                raise TypeError('too many arguments to NamedTuple: %s, %s' % (original_args, original_kwds))
            if pyver < 3.0:
                # if class_name is unicode, attempt a conversion to ASCII
                if isinstance(class_name, unicode):
                    try:
                        class_name = class_name.encode('ascii')
                    except UnicodeEncodeError:
                        raise TypeError('%r is not representable in ASCII' % (class_name, ))
            # quick exit if names is a NamedTuple
            if isinstance(names, NamedTupleMeta):
                names.__name__ = class_name
                if type is not None and type not in names.__bases__:
                    names.__bases__ = (type, ) + names.__bases__
                return names

            metacls = cls.__class__
            bases = (cls, )
            clsdict = metacls.__prepare__(class_name, bases)

            # special processing needed for names?
            if isinstance(names, basestring):
                names = names.replace(',', ' ').split()
            if isinstance(names, (tuple, list)) and isinstance(names[0], basestring):
                names = [(e, i) for (i, e) in enumerate(names)]
            # Here, names is either an iterable of (name, index) or (name, index, doc, default) or a mapping.
            item = None  # in case names is empty
            for item in names:
                if isinstance(item, basestring):
                    # mapping
                    field_name, field_index = item, names[item]
                else:
                    # non-mapping
                    if len(item) == 2:
                        field_name, field_index = item
                    else:
                        field_name, field_index = item[0], item[1:]
                clsdict[field_name] = field_index
            if type is not None:
                if not isinstance(type, tuple):
                    type = (type, )
                bases = type + bases
            namedtuple_class = metacls.__new__(metacls, class_name, bases, clsdict)

            # TODO: replace the frame hack if a blessed way to know the calling
            # module is ever developed
            if module is None:
                try:
                    module = _sys._getframe(1).f_globals['__name__']
                except (AttributeError, ValueError, KeyError):
                    pass
            if module is None:
                _make_class_unpicklable(namedtuple_class)
            else:
                namedtuple_class.__module__ = module

            return namedtuple_class
        else:
            # instantiate a subclass
            namedtuple_instance = cls.__new__(cls, *args, **kwds)
            if isinstance(namedtuple_instance, cls):
                namedtuple_instance.__init__(*args, **kwds)
            return namedtuple_instance

    @property
    def __fields__(cls):
        return list(cls._fields_)
    # collections.namedtuple compatibility
    _fields = __fields__

    @property
    def __aliases__(cls):
        return list(cls._aliases_)

    def __repr__(cls):
        return "<NamedTuple %r>" % (cls.__name__, )

temp_namedtuple_dict = {}
temp_namedtuple_dict['__doc__'] = "NamedTuple base class.\n\n    Derive from this class to define new NamedTuples.\n\n"

def __new__(cls, *args, **kwds):
    if cls._size_ is TupleSize.fixed and len(args) > cls._defined_len_:
        raise TypeError('%d fields expected, %d received' % (cls._defined_len_, len(args)))
    unknown = set(kwds) - set(cls._fields_) - set(cls._aliases_)
    if unknown:
        raise TypeError('unknown fields: %r' % (unknown, ))
    final_args = list(args) + [undefined] * (len(cls.__fields__) - len(args))
    for field, value in kwds.items():
        index = getattr(cls, field).index
        if final_args[index] != undefined:
            raise TypeError('field %s specified more than once' % field)
        final_args[index] = value
    missing = []
    for index, value in enumerate(final_args):
        if value is undefined:
            # look for default values
            name = cls.__fields__[index]
            default = getattr(cls, name).default
            if default is undefined:
                missing.append(name)
            else:
                final_args[index] = default
    if missing:
        if cls._size_ in (TupleSize.fixed, TupleSize.minimum):
            raise TypeError('values not provided for field(s): %s' % ', '.join(missing))
        while final_args and final_args[-1] is undefined:
            final_args.pop()
            missing.pop()
        if cls._size_ is not TupleSize.variable or undefined in final_args:
            raise TypeError('values not provided for field(s): %s' % ', '.join(missing))
    return tuple.__new__(cls, tuple(final_args))

temp_namedtuple_dict['__new__'] = __new__
del __new__

def __reduce_ex__(self, proto):
    return self.__class__, tuple(getattr(self, f) for f in self._fields_)
temp_namedtuple_dict['__reduce_ex__'] = __reduce_ex__
del __reduce_ex__

def __repr__(self):
    if len(self) == len(self._fields_):
        return "%s(%s)" % (
                self.__class__.__name__, ', '.join(['%s=%r' % (f, o) for f, o in zip(self._fields_, self)])
                )
    else:
        return '%s(%s)' % (self.__class__.__name__, ', '.join([repr(o) for o in self]))
temp_namedtuple_dict['__repr__'] = __repr__
del __repr__

def __str__(self):
    return "%s(%s)" % (
            self.__class__.__name__, ', '.join(['%r' % (getattr(self, f), ) for f in self._fields_])
            )
temp_namedtuple_dict['__str__'] = __str__
del __str__

## compatibility methods with stdlib namedtuple
@property
def __aliases__(self):
    return list(self.__class__._aliases_)
temp_namedtuple_dict['__aliases__'] = __aliases__
del __aliases__

@property
def __fields__(self):
    return list(self.__class__._fields_)
temp_namedtuple_dict['__fields__'] = __fields__
temp_namedtuple_dict['_fields'] = __fields__
del __fields__

def _make(cls, iterable, new=None, len=None):
    return cls.__new__(cls, *iterable)
temp_namedtuple_dict['_make'] = classmethod(_make)
del _make

def _asdict(self):
    return OrderedDict(zip(self._fields_, self))
temp_namedtuple_dict['_asdict'] = _asdict
del _asdict

def _replace(self, **kwds):
    current = self._asdict()
    current.update(kwds)
    return self.__class__(**current)
temp_namedtuple_dict['_replace'] = _replace
del _replace

NamedTuple = NamedTupleMeta('NamedTuple', (object, ), temp_namedtuple_dict)
del temp_namedtuple_dict

# defined now for immediate use

def enumsort(things):
    """
    sorts things by value if all same type; otherwise by name
    """
    if not things:
        return things
    sort_type = type(things[0])
    if not issubclass(sort_type, tuple):
        # direct sort or type error
        if not all((type(v) is sort_type) for v in things[1:]):
            raise TypeError('cannot sort items of different types')
        return sorted(things)
    else:
        # expecting list of (name, value) tuples
        sort_type = type(things[0][1])
        try:
            if all((type(v[1]) is sort_type) for v in things[1:]):
                return sorted(things, key=lambda i: i[1])
            else:
                raise TypeError('try name sort instead')
        except TypeError:
            return sorted(things, key=lambda i: i[0])

def export(collection, namespace=None):
    """
    export([collection,] namespace) -> Export members to target namespace.

    If collection is not given, act as a decorator.
    """
    if namespace is None:
        namespace = collection
        def export_decorator(collection):
            return export(collection, namespace)
        return export_decorator
    elif issubclass(collection, NamedConstant):
        for n, c in collection.__dict__.items():
            if isinstance(c, NamedConstant):
                namespace[n] = c
    elif issubclass(collection, Enum):
        data = collection.__members__.items()
        for n, m in data:
            namespace[n] = m
    else:
        raise TypeError('%r is not a supported collection' % (collection,) )
    return collection

# Constants used in Enum

@export(globals())
class EnumConstants(NamedConstant):
    AutoValue = constant('autovalue', 'values are automatically created from _generate_next_value_')
    AutoNumber = constant('autonumber', 'integer value is prepended to members, beginning from START')
    MultiValue = constant('multivalue', 'each member can have several values')
    NoAlias = constant('noalias', 'duplicate valued members are distinct, not aliased')
    Unique = constant('unique', 'duplicate valued members are not allowed')


############
# Enum stuff
############

# Dummy value for Enum as EnumMeta explicity checks for it, but of course until
# EnumMeta finishes running the first time the Enum class doesn't exist.  This
# is also why there are checks in EnumMeta like `if Enum is not None`
Enum = Flag = None

class enum(object):
    """
    Helper class to track args, kwds.
    """
    def __init__(self, *args, **kwds):
        self._args = args
        self._kwds = kwds.items()
        self._hash = hash(args)
        self.name = None

    @property
    def args(self):
        return self._args

    @property
    def kwds(self):
        return dict([(k, v) for k, v in self._kwds])

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.args == other.args and self.kwds == other.kwds

    def __ne__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.args != other.args or self.kwds != other.kwds

    def __repr__(self):
        final = []
        args = ', '.join(['%r' % (a, ) for a in self.args])
        if args:
            final.append(args)
        kwds = ', '.join([('%s=%r') % (k, v) for k, v in enumsort(list(self.kwds.items()))])
        if kwds:
            final.append(kwds)
        return '%s(%s)' % (self.__class__.__name__, ', '.join(final))

_auto_null = object()
class auto(enum):
    """
    Instances are replaced with an appropriate value in Enum class suites.
    """
    _value = _auto_null
    _operations = []

    def __and__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_and_, (self, other)))
        return new_auto

    def __rand__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_and_, (other, self)))
        return new_auto

    def __invert__(self):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_inv_, (self,)))
        return new_auto

    def __or__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_or_, (self, other)))
        return new_auto

    def __ror__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_or_, (other, self)))
        return new_auto

    def __xor__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_xor_, (self, other)))
        return new_auto

    def __rxor__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_xor_, (other, self)))
        return new_auto

    def __abs__(self):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_abs_, (self, )))
        return new_auto

    def __add__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_add_, (self, other)))
        return new_auto

    def __radd__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_add_, (other, self)))
        return new_auto

    def __neg__(self):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_neg_, (self, )))
        return new_auto

    def __pos__(self):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_pos_, (self, )))
        return new_auto

    if pyver < 3:
        def __div__(self, other):
            new_auto = self.__class__()
            new_auto._operations = self._operations[:]
            new_auto._operations.append((_div_, (self, other)))
            return new_auto

    def __rdiv__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_div_, (other, self)))
        return new_auto

    def __floordiv__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_floordiv_, (self, other)))
        return new_auto

    def __rfloordiv__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_floordiv_, (other, self)))
        return new_auto

    def __truediv__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_truediv_, (self, other)))
        return new_auto

    def __rtruediv__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_truediv_, (other, self)))
        return new_auto

    def __lshift__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_lshift_, (self, other)))
        return new_auto

    def __rlshift__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_lshift_, (other, self)))
        return new_auto

    def __rshift__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_rshift_, (self, other)))
        return new_auto

    def __rrshift__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_rshift_, (other, self)))
        return new_auto

    def __mod__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_mod_, (self, other)))
        return new_auto

    def __rmod__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_mod_, (other, self)))
        return new_auto

    def __mul__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_mul_, (self, other)))
        return new_auto

    def __rmul__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_mul_, (other, self)))
        return new_auto

    def __pow__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_pow_, (self, other)))
        return new_auto

    def __rpow__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_pow_, (other, self)))
        return new_auto

    def __sub__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_sub_, (self, other)))
        return new_auto

    def __rsub__(self, other):
        new_auto = self.__class__()
        new_auto._operations = self._operations[:]
        new_auto._operations.append((_sub_, (other, self)))
        return new_auto



    @property
    def value(self):
        if self._value is not _auto_null and self._operations:
            raise TypeError('auto() object out of sync')
        elif self._value is _auto_null and not self._operations:
            return self._value
        elif self._value is not _auto_null:
            return self._value
        else:
            return self._resolve()

    @value.setter
    def value(self, value):
        if self._operations:
            value = self._resolve(value)
        self._value = value

    def _resolve(self, base_value=None):
            cls = self.__class__
            for op, params in self._operations:
                values = []
                for param in params:
                    if isinstance(param, cls):
                        if param.value is _auto_null:
                            if base_value is None:
                                return _auto_null
                            else:
                                values.append(base_value)
                        else:
                            values.append(param.value)
                    else:
                        values.append(param)
                value = op(*values)
            self._operations[:] = []
            self._value = value
            return value

class _EnumDict(dict):
    """Track enum member order and ensure member names are not reused.

    EnumMeta will use the names found in self._member_names as the
    enumeration member names.
    """
    def __init__(self, cls_name, settings, start, constructor_init, constructor_start):
        super(_EnumDict, self).__init__()
        self._cls_name = cls_name
        self._constructor_init = constructor_init
        self._constructor_start = constructor_start
        # for Flag enumerations, we may need to get the _init_ from __new__
        self._new_to_init = False
        # list of enum members
        self._member_names = []
        self._settings = settings
        autonumber = AutoNumber in settings
        autovalue = AutoValue in settings
        multivalue = MultiValue in settings
        if autonumber and start is None:
            # starting value for AutoNumber
            start = 1
        elif start is not None and not autonumber:
            autonumber = True
        if start is not None:
            self._value = start - 1
        else:
            self._value = None
        # when the magic turns off
        self._locked = not (autovalue or autonumber)
        # if auto or autonumber
        self._autovalue = autovalue
        self._autonumber = autonumber
        # if multiple values are allowed
        self._multivalue = multivalue
        # if init fields are specified
        self._init = None
        # list of temporary names
        self._ignore = []
        self._ignore_init_done = False
        # if _sunder_ values can be changed via the class body
        self._allow_init = True
        self._last_values = []

    def __getitem__(self, key):
        if key == self._cls_name and self._cls_name not in self:
            return enum
        elif key == '_auto_on_':
            self._locked = False
            if not self._autonumber:
                self._autovalue = True
            return None
        elif key == '_auto_off_':
            self._locked = True
            return None
        elif (
                self._locked
                or key in self
                or key in self._ignore
                or _is_sunder(key)
                or _is_dunder(key)
                ):
            return super(_EnumDict, self).__getitem__(key)
        elif self._autonumber:
            try:
                # try to generate the next value
                value = self._value + 1
                self._value += 1
            except:
                # couldn't work the magic, report error
                raise KeyError('%s not found' % (key,))
        elif self._autovalue:
            value = self._generate_next_value(key, 1, len(self._member_names), self._last_values[:])
        else:
            raise Exception('neither AutoNumber nor AutoValue set -- why am I here?')
        self.__setitem__(key, value)
        return value

    def __setitem__(self, key, value):
        """Changes anything not sundured, dundered, nor a descriptor.

        If an enum member name is used twice, an error is raised; duplicate
        values are not checked for.

        Single underscore (sunder) names are reserved.
        """
        if _is_internal_class(self._cls_name, value):
            pass
        elif _is_private_name(self._cls_name, key):
            pass
        elif _is_sunder(key):
            if key not in (
                    '_init_', '_settings_', '_order_', '_ignore_', '_start_',
                    '_create_pseudo_member_', '_create_pseudo_member_values_',
                    '_generate_next_value_',
                    '_missing_', '_missing_value_', '_missing_name_',
                    ):
                raise ValueError('_sunder_ names, such as %r, are reserved for future Enum use'
                        % (key, )
                        )
            elif not self._allow_init and key not in (
                    'create_pseudo_member_', '_missing_', '_missing_value_', '_missing_name_',
                ):
                # sunder is used during creation, must be specified first
                raise ValueError('cannot set %r after init phase' % (key, ))
            elif key == '_ignore_':
                if self._ignore_init_done:
                    raise TypeError('ignore can only be specified once')
                if isinstance(value, basestring):
                    value = value.split()
                else:
                    value = list(value)
                self._ignore = value
                already = set(value) & set(self._member_names)
                if already:
                    raise ValueError('_ignore_ cannot specify already set names: %r' % (already, ))
                self._ignore_init_done = True
            elif key == '_start_':
                if self._constructor_start:
                    raise TypeError('start specified in constructor and class body')
                if value is None:
                    self._value = None
                    self._autonumber = False
                    if not self._autovalue:
                        self._locked = True
                else:
                    self._value = value - 1
                    self._locked = False
                    self._autonumber = True
            elif key == '_settings_':
                if not isinstance(value, (set, tuple)):
                    value = (value, )
                if not isinstance(value, set):
                    value = set(value)
                self._settings |= value
                if NoAlias in value and Unique in value:
                    raise TypeError('cannot specify both NoAlias and Unique')
                elif MultiValue in value and NoAlias in value:
                    raise TypeError('cannot specify both MultiValue and NoAlias')
                elif AutoValue in value and AutoNumber in value:
                    raise TypeError('cannot specify both AutoValue and AutoNumber')
                allowed_settings = dict.fromkeys(['autovalue', 'autonumber', 'noalias', 'unique', 'multivalue'])
                for arg in value:
                    if arg not in allowed_settings:
                        raise TypeError('unknown qualifier: %r (from %r)' % (arg, value))
                    allowed_settings[arg] = True
                self._multivalue = allowed_settings['multivalue']
                self._autovalue = allowed_settings['autovalue']
                self._autonumber = allowed_settings['autonumber']
                self._locked = not (self._autonumber or self._autovalue)
                if (self._autovalue or self._autonumber) and not self._ignore_init_done:
                    self._ignore = ['property', 'classmethod', 'staticmethod', 'aenum', 'auto']
                if self._autonumber and self._value is None:
                    self._value = 0
                if self._autonumber and self._init and self._init[0:1] == ['value']:
                    self._init.pop(0)
                value = tuple(self._settings)
            elif key == '_init_':
                if self._constructor_init:
                    raise TypeError('init specified in constructor and in class body')
                _init_ = value
                if isinstance(_init_, basestring):
                    _init_ = _init_.replace(',',' ').split()
                if _init_[0:1] == ['value'] and self._autonumber:
                    _init_.pop(0)
                self._init = _init_
            elif key == '_generate_next_value_':
                if isinstance(value, staticmethod):
                    gnv = value.__func__
                elif isinstance(value, classmethod):
                    raise TypeError('_generate_next_value should be a staticmethod, not a classmethod')
                else:
                    gnv = value
                    value = staticmethod(value)
                setattr(self, '_generate_next_value', gnv)
                self._auto_args = _check_auto_args(value)
        elif _is_dunder(key):
            if key == '__order__':
                key = '_order_'
                if not self._allow_init:
                    # _order_ is used during creation, must be specified first
                    raise ValueError('cannot set %r after init phase' % (key, ))
            elif key == '__new__' and self._new_to_init:
                # ArgSpec(args=[...], varargs=[...], keywords=[...], defaults=[...]
                if isinstance(value, staticmethod):
                    value = value.__func__
                new_args = getargspec(value)[0][1:]
                self._init = new_args
            if _is_descriptor(value):
                self._locked = True
        elif key in self._member_names:
            # descriptor overwriting an enum?
            raise TypeError('attempt to reuse name: %r' % (key, ))
        elif key in self._ignore:
            pass
        elif not _is_descriptor(value):
            self._allow_init = False
            if key in self:
                # enum overwriting a descriptor?
                raise TypeError('%s already defined as: %r' % (key, self[key]))
            if self._multivalue:
                # make sure it's a tuple
                if not isinstance(value, tuple):
                    value = (value, )
                # do we need to calculate the next value?
                if self._autonumber:
                    if self._init:
                        target_length = len(self._init)
                        if self._init[0] != 'value':
                            target_length += 1
                        if len(value) != target_length:
                            value = (self._value + 1, ) + value
                        if isinstance(value[0], auto):
                            value = (self._value + 1, ) + value[1:]
                    else:
                        try:
                            value = (self._value + 1, ) + value
                        except TypeError:
                            pass
                    self._value = value[0]
            elif self._autovalue and self._init and not isinstance(value, auto):
                # call generate iff init is specified and calls for more values than are present
                target_values = len(self._init)
                if not isinstance(value, tuple):
                    value = (value, )
                source_values = len(value)
                if target_values != source_values:
                    gnv = self._generate_next_value
                    if self._auto_args:
                        value = gnv(
                                key, 1,
                                len(self._member_names),
                                self._last_values[:],
                                *value
                                )
                    else:
                        value = gnv(
                                key,
                                1,
                                len(self._member_names),
                                self._last_values[:],
                                )

            elif self._autonumber and not self._locked:
                # convert any auto instances to integers
                if isinstance(value, auto):
                    value = self._value + 1
                elif isinstance(value, basestring):
                    pass
                else:
                    try:
                        new_value = []
                        for v in value:
                            if isinstance(v, auto):
                                new_value.append(self._value + 1)
                            else:
                                new_value.append(v)
                        value = tuple(new_value)
                    except TypeError:
                        # value wasn't iterable
                        pass
                if isinstance(value, int):
                    self._value = value
                elif isinstance(value, tuple):
                    if self._init is None:
                        # old behavior -> if first item is int, use it as value
                        #                 otherwise, generate a value and prepend it
                        if value and isinstance(value[0], baseinteger):
                            self._value = value[0]
                        else:
                            self._value += 1
                            value = (self._value, ) + value
                    elif len(value) == len(self._init):
                        # provide actual value for member
                        self._value += 1
                        value = (self._value, ) + value
                    elif 'value'  not in self._init and len(value) == len(self._init) + 1:
                        # actual value for member is provided
                        self._value = value[0]
                    elif 'value' in self._init and len(value) == len(self._init) - 1:
                        count = self._value + 1
                        value = count, value
                        self._value = count
                    else:
                        # mismatch
                        raise TypeError('%s: number of fields provided do not match init' % key)
                else:
                    if self._init is not None and (len(self._init) != 1 or 'value' in self._init):
                        raise TypeError('%s: number of fields provided do not match init' % key)
                    count = self._value + 1
                    value = count, value
                    self._value = count
            elif isinstance(value, auto):
                # if AutoNumber set use built-in value, not _generate_next_value_
                if self._autonumber:
                    value = self._value + 1
                    self._value = value
                else:
                    if value.value == _auto_null:
                        gnv = self._generate_next_value
                        prev_values = []
                        for v in self._last_values:
                            if isinstance(v, auto):
                                prev_values.append(v.value)
                            else:
                                prev_values.append(v)
                        if isinstance(gnv, staticmethod):
                            gnv = gnv.__func__
                        if self._auto_args:
                            value.value = gnv(
                                    key,
                                    1,
                                    len(self._member_names),
                                    prev_values,
                                    *value.args,
                                    **value.kwds
                                    )
                        else:
                            value.value = gnv(
                                    key,
                                    1,
                                    len(self._member_names),
                                    prev_values,
                                    )
            elif isinstance(value, enum):
                value.name = key
            else:
                pass
            self._member_names.append(key)
        else:
            # not a new member, turn off the autoassign magic
            self._locked = True
            self._allow_init = False
        if not _is_sunder(key) and not _is_dunder(key) and not _is_descriptor(value):
            if (self._autonumber or self._multivalue) and isinstance(value, tuple):
                self._last_values.append(value[0])
            else:
                self._last_values.append(value)
        super(_EnumDict, self).__setitem__(key, value)


no_arg = object()
class EnumMeta(StdlibEnumMeta or type):
    """Metaclass for Enum"""
    @classmethod
    def __prepare__(metacls, cls, bases, init=None, start=None, settings=()):
        # settings are a combination of current and all past settings
        constructor_init = init is not None
        constructor_start = start is not None
        if not isinstance(settings, tuple):
            settings = settings,
        settings = set(settings)
        generate = None
        order = None
        # inherit previous flags
        member_type, first_enum = metacls._get_mixins_(bases)
        if first_enum is not None:
            settings |= first_enum._settings_
            init = init or first_enum._auto_init_
            order = first_enum._order_function_
            if start is None:
                start = first_enum._start_
            generate = getattr(first_enum, '_generate_next_value_', None)
            generate = getattr(generate, 'im_func', generate)
        # check for custom settings
        if NoAlias in settings and Unique in settings:
            raise TypeError('cannot specify both NoAlias and Unique')
        elif MultiValue in settings and NoAlias in settings:
            raise TypeError('cannot specify both MultiValue and NoAlias')
        elif AutoValue in settings and AutoNumber in settings:
            raise TypeError('cannot specify both AutoValue and AutoNumber')
        allowed_settings = dict.fromkeys(['autovalue', 'autonumber', 'noalias', 'unique', 'multivalue'])
        for arg in settings:
            if arg not in allowed_settings:
                raise TypeError('unknown qualifier: %r' % (arg, ))
            allowed_settings[arg] = True
        enum_dict = _EnumDict(cls_name=cls, settings=settings, start=start, constructor_init=constructor_init, constructor_start=constructor_start)
        if settings & set([AutoValue, AutoNumber]) or start is not None:
            enum_dict['_ignore_'] = ['property', 'classmethod', 'staticmethod']
            enum_dict._ignore_init_done = False
        if generate:
            enum_dict['_generate_next_value_'] = generate
        if init is not None:
            if isinstance(init, basestring):
                init = init.replace(',',' ').split()
            if init[0:1] == ['value'] and AutoNumber in settings:
                init.pop(0)
            enum_dict._init = init
        elif Flag is not None and any(issubclass(b, Flag) for b in bases) and member_type not in (int, object):
            enum_dict._new_to_init = True
            if Flag in bases:
                # only happens on first mixin with Flag
                def _generate_next_value_(name, start, count, values, *args, **kwds):
                    return (2 ** count, ) + args
                enum_dict['_generate_next_value_'] = staticmethod(_generate_next_value_)
                def __new__(cls, flag_value, type_value):
                    obj = member_type.__new__(cls, type_value)
                    obj._value_ = flag_value
                    return obj
                enum_dict['__new__'] = __new__
            else:
                try:
                    new_args = getargspec(first_enum.__new_member__)[0][1:]
                    enum_dict._init = new_args
                except TypeError:
                    pass
        if order is not None:
            enum_dict['_order_'] = staticmethod(order)
        return enum_dict

    def __init__(cls, *args , **kwds):
        super(EnumMeta, cls).__init__(*args)

    def __new__(metacls, cls, bases, clsdict, init=None, start=None, settings=(), **mc_kwds):
        # handle py2 case first
        if type(clsdict) is not _EnumDict:
            # py2 ard/or functional API gyrations
            init = clsdict.pop('_init_', None)
            start = clsdict.pop('_start_', None)
            settings = clsdict.pop('_settings_', ())
            _order_ = clsdict.pop('_order_', clsdict.pop('__order__', None))
            _ignore_ = clsdict.pop('_ignore_', None)
            _create_pseudo_member_ = clsdict.pop('_create_pseudo_member_', None)
            _create_pseudo_member_values_ = clsdict.pop('_create_pseudo_member_values_', None)
            _generate_next_value_ = clsdict.pop('_generate_next_value_', None)
            _missing_ = clsdict.pop('_missing_', None)
            _missing_value_ = clsdict.pop('_missing_value_', None)
            _missing_name_ = clsdict.pop('_missing_name_', None)
            __new__ = clsdict.pop('__new__', None)
            enum_members = dict([
                    (k, v) for (k, v) in clsdict.items()
                    if not (_is_sunder(k) or _is_dunder(k) or _is_descriptor(v))
                    ])
            original_dict = clsdict
            clsdict = metacls.__prepare__(cls, bases, init=init, start=start, settings=settings)
            init = init or clsdict._init
            if _order_ is None:
                _order_ = clsdict.get('_order_')
                if _order_ is not None:
                    _order_ = _order_.__get__(cls)
            if isinstance(original_dict, OrderedDict):
                calced_order = original_dict
            elif _order_ is None:
                calced_order = [name for (name, value) in enumsort(list(enum_members.items()))]
            elif isinstance(_order_, basestring):
                calced_order = _order_ = _order_.replace(',', ' ').split()
            elif callable(_order_):
                if init:
                    if not isinstance(init, basestring):
                        init = ' '.join(init)
                member = NamedTuple('member', init and 'name ' + init or ['name', 'value'])
                calced_order = []
                for name, value in enum_members.items():
                    if init:
                        if not isinstance(value, tuple):
                            value = (value, )
                        name_value = (name, ) + value
                    else:
                        name_value = tuple((name, value))
                    if member._defined_len_ != len(name_value):
                        raise TypeError('%d values expected (%s), %d received (%s)' % (
                            member._defined_len_,
                            ', '.join(member._fields_),
                            len(name_value),
                            ', '.join([repr(v) for v in name_value]),
                            ))
                    calced_order.append(member(*name_value))
                calced_order = [m.name for m in sorted(calced_order, key=_order_)]
            else:
                calced_order = _order_
            for name in (
                    '_ignore_', '_create_pseudo_member_', '_create_pseudo_member_values_',
                    '_generate_next_value_', '_order_', '__new__',
                    '_missing_', '_missing_value_', '_missing_name_',
                ):
                attr = locals()[name]
                if attr is not None:
                    clsdict[name] = attr
            # now add members
            for k in calced_order:
                clsdict[k] = original_dict[k]
            for k, v in original_dict.items():
                if k not in calced_order:
                    clsdict[k] = v
            del _order_, _ignore_, _create_pseudo_member_, _create_pseudo_member_values_,
            del _generate_next_value_, _missing_, _missing_value_, _missing_name_

        # resume normal path
        if clsdict._new_to_init:
            # remove calculated _init_ as it's no longer needed
            clsdict._init = None
        clsdict._locked = True
        member_type, first_enum = metacls._get_mixins_(bases)
        _order_ = clsdict.pop('_order_', None)
        if isinstance(_order_, basestring):
            _order_ = _order_.replace(',',' ').split()
        init = clsdict._init
        start = clsdict._value
        settings = clsdict._settings
        if start is not None:
            start += 1
        creating_init = []
        auto_init = False
        if init is None and (AutoNumber in settings or start is not None):
                creating_init = ['value']
        elif init is not None:
            auto_init = True
            if (AutoNumber in settings or start is not None) and 'value' not in  init:
                creating_init = ['value'] + init
            else:
                creating_init = init[:]
        autonumber = AutoNumber in settings
        autovalue = AutoValue in settings
        multivalue = MultiValue in settings
        noalias = NoAlias in settings
        unique = Unique in settings
        # an Enum class cannot be mixed with other types (int, float, etc.) if
        #   it has an inherited __new__ unless a new __new__ is defined (or
        #   the resulting class will fail).
        # an Enum class is final once enumeration items have been defined;
        #
        # remove any keys listed in _ignore_
        clsdict.setdefault('_ignore_', []).append('_ignore_')
        ignore = clsdict['_ignore_']
        for key in ignore:
            clsdict.pop(key, None)
        # get the method to create enum members
        __new__, save_new, new_uses_args = metacls._find_new_(
                clsdict,
                member_type,
                first_enum,
                )
        # save enum items into separate mapping so they don't get baked into
        # the new class
        enum_members = dict((k, clsdict[k]) for k in clsdict._member_names)
        for name in clsdict._member_names:
            del clsdict[name]
        # move skipped values out of the descriptor, and add names to DynamicAttributes
        for name, obj in clsdict.items():
            if isinstance(obj, nonmember):
                dict.__setitem__(clsdict, name, obj.value)
            elif isinstance(obj, enum_property):
                obj.name = name
        # check for illegal enum names (any others?)
        invalid_names = set(enum_members) & set(['mro', ''])
        if invalid_names:
            raise ValueError('Invalid enum member name(s): %s' % (
                ', '.join(invalid_names), ))
        # check for invalid method values
        if '__init_subclass__' in clsdict and clsdict['__init_subclass__'] is None:
            raise TypeError('%s.__init_subclass__ cannot be None')
        # remove current __init_subclass__ so previous one can be found with getattr
        new_init_subclass = clsdict.pop('__init_subclass__', None)
        # create our new Enum type, possibly with an extra do-nothing class, and possibly
        # calling __set_name__ ourselves
        if pyver >= 3.6:
            bases = (_NoInitSubclass, ) + bases
            enum_class = type.__new__(metacls, cls, bases, clsdict)
            enum_class.__bases__ = enum_class.__bases__[1:]
        else:
            enum_class = type.__new__(metacls, cls, bases, clsdict)
            for name, obj in enum_class.__dict__.items():
                if hasattr(obj, '__set_name__'):
                    obj.__set_name__(enum_class, name)
        old_init_subclass = getattr(enum_class, '__init_subclass__', None)
        # and restore the new one (if there was one)
        if new_init_subclass is not None:
            # staticmethod use is to preserve Python 2 compatibility
            enum_class.__init_subclass__ = classmethod(new_init_subclass)
        enum_class._member_names_ = []               # names in random order
        enum_class._member_map_ = OrderedDict()
        enum_class._member_type_ = member_type
        # save current flags for subclasses
        enum_class._settings_ = settings
        enum_class._start_ = start
        enum_class._auto_init_ = _auto_init_ = init
        enum_class._order_function_ = None
        if 'value' in creating_init and creating_init[0] != 'value':
            raise TypeError("'value', if specified, must be the first item in 'init'")
        # save attributes from super classes so we know if we can take
        # the shortcut of storing members in the class dict
        base_attributes = set([a for b in enum_class.mro() for a in b.__dict__])
        # Reverse value->name map for hashable values.
        enum_class._value2member_map_ = {}
        enum_class._value2member_seq_ = ()
        # instantiate them, checking for duplicates as we go
        # we instantiate first instead of checking for duplicates first in case
        # a custom __new__ is doing something funky with the values -- such as
        # auto-numbering ;)
        if __new__ is None:
            __new__ = enum_class.__new__
        for member_name in clsdict._member_names:
            value = enum_members[member_name]
            if isinstance(value, auto):
                value = value.value
            kwds = {}
            new_args = ()
            init_args = ()
            extra_mv_args = ()
            if isinstance(value, enum):
                args = value.args
                kwds = value.kwds
            elif isinstance(value, Member):
                value = value.value
                args = (value, )
            elif not isinstance(value, tuple):
                args = (value, )
            else:
                args = value
            # possibilities
            #
            # - no init, multivalue  -> __new__[0], __init__(*[:]), extra=[1:]
            # - init w/o value, multivalue  -> __new__[0], __init__(*[:]), extra=[1:]
            #
            # - init w/value, multivalue  -> __new__[0], __init__(*[1:]),  extra=[1:]
            #
            # - init w/value, no multivalue  -> __new__[0], __init__(*[1:]), extra=[]
            #
            # - init w/o value, no multivalue  -> __new__[:], __init__(*[:]), extra=[]
            # - no init, no multivalue  ->  __new__[:], __init__(*[:]), extra=[]
            if multivalue or 'value' in creating_init:
                if multivalue:
                    # when multivalue is True, creating_init can be anything
                    new_args = args[0:1]
                    extra_mv_args = args[1:]
                    if 'value' in creating_init:
                        init_args = args[1:]
                    else:
                        init_args = args
                else:
                    # 'value' is definitely in creating_init
                    new_args = args[0:1]
                    if auto_init:
                        # don't pass in value
                        init_args = args[1:]
                    else:
                        # keep the all args for user-defined __init__
                        init_args = args
                value = new_args[0]
            else:
                # either no creating_init, or it doesn't have 'value'
                new_args = args
                init_args = args
            if member_type is tuple:   # special case for tuple enums
                new_args = (new_args, )     # wrap it one more time
            if not new_uses_args:
                enum_member = __new__(enum_class)
                if not hasattr(enum_member, '_value_'):
                    enum_member._value_ = value
            else:
                enum_member = __new__(enum_class, *new_args, **kwds)
                if not hasattr(enum_member, '_value_'):
                    enum_member._value_ = member_type(*new_args, **kwds)
            value = enum_member._value_
            enum_member._name_ = member_name
            enum_member.__objclass__ = enum_class
            enum_member.__init__(*init_args, **kwds)
            # If another member with the same value was already defined, the
            # new member becomes an alias to the existing one.
            if noalias:
                # unless NoAlias was specified
                enum_class._member_names_.append(member_name)
            else:
                nonunique = defaultdict(list)
                for name, canonical_member in enum_class._member_map_.items():
                    if canonical_member.value == enum_member._value_:
                        if unique:
                            nonunique[name].append(member_name)
                            continue
                        enum_member = canonical_member
                        break
                else:
                    # Aliases don't appear in member names (only in __members__).
                    enum_class._member_names_.append(member_name)
                if nonunique:
                    # duplicates not allowed if Unique specified
                    message = []
                    for name, aliases in nonunique.items():
                        bad_aliases = ','.join(aliases)
                        message.append('%s --> %s [%r]' % (name, bad_aliases, enum_class[name].value))
                    raise ValueError(
                            'duplicate names found in %r: %s' %
                                (cls, ';  '.join(message))
                            )
            # members are added as enum_property's
            setattr(enum_class, member_name, enum_property(name=member_name))
            # now add to _member_map_
            enum_class._member_map_[member_name] = enum_member
            values = (value, ) + extra_mv_args
            enum_member._values_ = values
            for value in values:
                # first check if value has already been used
                if multivalue and (
                        value in enum_class._value2member_map_
                        or any(v == value for (v, m) in enum_class._value2member_seq_)
                        ):
                    raise ValueError('%r has already been used' % (value, ))
                try:
                    # This may fail if value is not hashable. We can't add the value
                    # to the map, and by-value lookups for this value will be
                    # linear.
                    if noalias:
                        raise TypeError('cannot use dict to store value')
                    enum_class._value2member_map_[value] = enum_member
                except TypeError:
                    enum_class._value2member_seq_ += ((value, enum_member), )
        # check for constants with auto() values
        for k, v in enum_class.__dict__.items():
            if isinstance(v, constant) and isinstance(v.value, auto):
                v.value = enum_class(v.value.value)
        # If a custom type is mixed into the Enum, and it does not know how
        # to pickle itself, pickle.dumps will succeed but pickle.loads will
        # fail.  Rather than have the error show up later and possibly far
        # from the source, sabotage the pickle protocol for this class so
        # that pickle.dumps also fails.
        #
        # However, if the new class implements its own __reduce_ex__, do not
        # sabotage -- it's on them to make sure it works correctly.  We use
        # __reduce_ex__ instead of any of the others as it is preferred by
        # pickle over __reduce__, and it handles all pickle protocols.
        unpicklable = False
        if '__reduce_ex__' not in clsdict:
            if member_type is not object:
                methods = ('__getnewargs_ex__', '__getnewargs__',
                        '__reduce_ex__', '__reduce__')
                if not any(m in member_type.__dict__ for m in methods):
                    _make_class_unpicklable(enum_class)
                    unpicklable = True

        # double check that repr and friends are not the mixin's or various
        # things break (such as pickle)

        for name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            enum_class_method = enum_class.__dict__.get(name, None)
            if enum_class_method:
                # class has defined/imported/copied the method
                continue
            class_method = getattr(enum_class, name)
            obj_method = getattr(member_type, name, None)
            enum_method = getattr(first_enum, name, None)
            if obj_method is not None and obj_method == class_method:
                if name == '__reduce_ex__' and unpicklable:
                    continue
                setattr(enum_class, name, enum_method)

        # method resolution and int's are not playing nice
        # Python's less than 2.6 use __cmp__

        if pyver < 2.6:

            if issubclass(enum_class, int):
                setattr(enum_class, '__cmp__', getattr(int, '__cmp__'))

        elif pyver < 3.0:

            if issubclass(enum_class, int):
                for method in (
                        '__le__',
                        '__lt__',
                        '__gt__',
                        '__ge__',
                        '__eq__',
                        '__ne__',
                        '__hash__',
                        ):
                    setattr(enum_class, method, getattr(int, method))

        # replace any other __new__ with our own (as long as Enum is not None,
        # anyway) -- again, this is to support pickle
        if Enum is not None:
            # if the user defined their own __new__, save it before it gets
            # clobbered in case they subclass later
            if save_new:
                setattr(enum_class, '__new_member__', enum_class.__dict__['__new__'])
            setattr(enum_class, '__new__', Enum.__dict__['__new__'])

        # py3 support for definition order (helps keep py2/py3 code in sync)
        if _order_:
            if isinstance(_order_, staticmethod):
                # _order_ = staticmethod.__get__(enum_class)
                # _order_ = getattr(_order_, 'im_func', _order_)
                _order_ = _order_.__func__
            if callable(_order_):
                # save order for future subclasses
                enum_class._order_function_ = staticmethod(_order_)
                # create ordered list for comparison
                _order_ = [m.name for m in sorted(enum_class, key=_order_)]
            if _order_ != enum_class._member_names_:
                raise TypeError('member order does not match _order_: %r %r' % (enum_class._member_names_, enum_class._member_map_.items()))
        # call parents' __init_subclass__
        if Enum is not None and old_init_subclass is not None:
            old_init_subclass(**mc_kwds)
        return enum_class

    def __bool__(cls):
        """
        classes/types should always be True.
        """
        return True

    def __call__(cls, value=no_arg, names=None, module=None, type=None, start=1):
        """Either returns an existing member, or creates a new enum class.

        This method is used both when an enum class is given a value to match
        to an enumeration member (i.e. Color(3)) and for the functional API
        (i.e. Color = Enum('Color', names='red green blue')).

        When used for the functional API: `module`, if set, will be stored in
        the new class' __module__ attribute; `type`, if set, will be mixed in
        as the first base class.

        Note: if `module` is not set this routine will attempt to discover the
        calling module by walking the frame stack; if this is unsuccessful
        the resulting class will not be pickleable.
        """
        if names is None:  # simple value lookup
            return cls.__new__(cls, value)
        # otherwise, functional API: we're creating a new Enum type
        return cls._create_(value, names, module=module, type=type, start=start)

    def __contains__(cls, member):
        if not isinstance(member, Enum):
            raise TypeError("%r (%r) is not an <aenum 'Enum'>" % (member, type(member)))
        if not isinstance(member, cls):
            return False
        return True

    def __delattr__(cls, attr):
        # nicer error message when someone tries to delete an attribute
        # (see issue19025).
        if attr in cls._member_map_:
            raise AttributeError(
                    "%s: cannot delete Enum member %r." % (cls.__name__, attr),
                    )
        if isinstance(_get_attr_from_chain(cls, attr), constant):
            raise AttributeError(
                    "%s: cannot delete constant %r" % (cls.__name__, attr),
                    )
        super(EnumMeta, cls).__delattr__(attr)

    def __dir__(self):
        return (['__class__', '__doc__', '__members__', '__module__'] +
                self._member_names_)

    @property
    def __members__(cls):
        """Returns a mapping of member name->value.

        This mapping lists all enum members, including aliases. Note that this
        is a copy of the internal mapping.
        """
        return cls._member_map_.copy()

    def __getitem__(cls, name):
        try:
            return cls._member_map_[name]
        except KeyError:
            exc = _sys.exc_info()[1]
        if issubclass(cls, Flag) and '|' in name:
            try:
                # may be an __or__ed name
                result = cls(0)
                for n in name.split('|'):
                    result |= cls[n]
                return result
            except KeyError:
                raise exc
        result = cls._missing_name_(name)
        if isinstance(result, cls):
            return result
        else:
            raise exc

    def __iter__(cls):
        return (cls._member_map_[name] for name in cls._member_names_)

    def __reversed__(cls):
        return (cls._member_map_[name] for name in reversed(cls._member_names_))

    def __len__(cls):
        return len(cls._member_names_)

    __nonzero__ = __bool__

    def __repr__(cls):
        return "<aenum %r>" % (cls.__name__, )

    def __setattr__(cls, name, value):
        """Block attempts to reassign Enum members/constants.

        A simple assignment to the class namespace only changes one of the
        several possible ways to get an Enum member from the Enum class,
        resulting in an inconsistent Enumeration.
        """
        member_map = cls.__dict__.get('_member_map_', {})
        if name in member_map:
            raise AttributeError(
                    '%s: cannot rebind member %r.' % (cls.__name__, name),
                    )
        cur_obj = cls.__dict__.get(name)
        if isinstance(cur_obj, constant):
            raise AttributeError(
                    '%s: cannot rebind constant %r' % (cls.__name__, name),
                    )
        super(EnumMeta, cls).__setattr__(name, value)

    def _create_(cls, class_name, names, module=None, type=None, start=1):
        """Convenience method to create a new Enum class.

        `names` can be:

        * A string containing member names, separated either with spaces or
          commas.  Values are auto-numbered from 1.
        * An iterable of member names.  Values are auto-numbered from 1.
        * An iterable of (member name, value) pairs.
        * A mapping of member name -> value.
        """
        if pyver < 3.0:
            # if class_name is unicode, attempt a conversion to ASCII
            if isinstance(class_name, unicode):
                try:
                    class_name = class_name.encode('ascii')
                except UnicodeEncodeError:
                    raise TypeError('%r is not representable in ASCII' % (class_name, ))
        metacls = cls.__class__
        if type is None:
            bases = (cls, )
        else:
            bases = (type, cls)
        _, first_enum = cls._get_mixins_(bases)
        generate = getattr(first_enum, '_generate_next_value_', None)
        generate = getattr(generate, 'im_func', generate)
        # special processing needed for names?
        if isinstance(names, basestring):
            names = names.replace(',', ' ').split()
        if isinstance(names, (tuple, list)) and names and isinstance(names[0], basestring):
            original_names, names = names, []
            last_values = []
            for count, name in enumerate(original_names):
                value = generate(name, start, count, last_values[:])
                last_values.append(value)
                names.append((name, value))
        # Here, names is either an iterable of (name, value) or a mapping.
        item = None  # in case names is empty
        clsdict = None
        for item in names:
            if clsdict is None:
                # first time initialization
                if isinstance(item, basestring):
                    clsdict = {}
                else:
                    # remember the order
                    clsdict = metacls.__prepare__(class_name, bases)
            if isinstance(item, basestring):
                member_name, member_value = item, names[item]
            else:
                member_name, member_value = item
            clsdict[member_name] = member_value
        if clsdict is None:
            # in case names was empty
            clsdict = metacls.__prepare__(class_name, bases)
        enum_class = metacls.__new__(metacls, class_name, bases, clsdict)
        # TODO: replace the frame hack if a blessed way to know the calling
        # module is ever developed
        if module is None:
            try:
                module = _sys._getframe(2).f_globals['__name__']
            except (AttributeError, KeyError):
                pass
        if module is None:
            _make_class_unpicklable(enum_class)
        else:
            enum_class.__module__ = module
        return enum_class

    @staticmethod
    def _get_mixins_(bases):
        """Returns the type for creating enum members, and the first inherited
        enum class.

        bases: the tuple of bases that was given to __new__
        """
        if not bases or Enum is None:
            return object, Enum
        def _find_data_type(bases):
            for chain in bases:
                for base in chain.__mro__:
                    if base is object or base is StdlibEnum:
                        continue
                    elif '__new__' in base.__dict__:
                        if issubclass(base, Enum):
                            continue
                        return base

        # ensure final parent class is an Enum derivative, find any concrete
        # data type, and check that Enum has no members
        first_enum = bases[-1]
        if not issubclass(first_enum, Enum):
            raise TypeError("new enumerations should be created as "
                    "`EnumName([mixin_type, ...] [data_type,] enum_type)`")
        member_type = _find_data_type(bases) or object
        if first_enum._member_names_:
            raise TypeError("cannot extend enumerations via subclassing")

        return member_type, first_enum

    if pyver < 3.0:
        @staticmethod
        def _find_new_(clsdict, member_type, first_enum):
            """Returns the __new__ to be used for creating the enum members.

            clsdict: the class dictionary given to __new__
            member_type: the data type whose __new__ will be used by default
            first_enum: enumeration to check for an overriding __new__
            """
            # now find the correct __new__, checking to see of one was defined
            # by the user; also check earlier enum classes in case a __new__ was
            # saved as __new_member__
            __new__ = clsdict.get('__new__', None)
            if __new__:
                return None, True, True      # __new__, save_new, new_uses_args

            N__new__ = getattr(None, '__new__')
            O__new__ = getattr(object, '__new__')
            if Enum is None:
                E__new__ = N__new__
            else:
                E__new__ = Enum.__dict__['__new__']
            # check all possibles for __new_member__ before falling back to
            # __new__
            for method in ('__new_member__', '__new__'):
                for possible in (member_type, first_enum):
                    try:
                        target = possible.__dict__[method]
                    except (AttributeError, KeyError):
                        target = getattr(possible, method, None)
                    if target not in [
                            None,
                            N__new__,
                            O__new__,
                            E__new__,
                            ]:
                        if method == '__new_member__':
                            clsdict['__new__'] = target
                            return None, False, True
                        if isinstance(target, staticmethod):
                            target = target.__get__(member_type)
                        __new__ = target
                        break
                if __new__ is not None:
                    break
            else:
                __new__ = object.__new__

            # if a non-object.__new__ is used then whatever value/tuple was
            # assigned to the enum member name will be passed to __new__ and to the
            # new enum member's __init__
            if __new__ is object.__new__:
                new_uses_args = False
            else:
                new_uses_args = True

            return __new__, False, new_uses_args
    else:
        @staticmethod
        def _find_new_(clsdict, member_type, first_enum):
            """Returns the __new__ to be used for creating the enum members.

            clsdict: the class dictionary given to __new__
            member_type: the data type whose __new__ will be used by default
            first_enum: enumeration to check for an overriding __new__
            """
            # now find the correct __new__, checking to see of one was defined
            # by the user; also check earlier enum classes in case a __new__ was
            # saved as __new_member__
            __new__ = clsdict.get('__new__', None)

            # should __new__ be saved as __new_member__ later?
            save_new = __new__ is not None

            if __new__ is None:
                # check all possibles for __new_member__ before falling back to
                # __new__
                for method in ('__new_member__', '__new__'):
                    for possible in (member_type, first_enum):
                        target = getattr(possible, method, None)
                        if target not in (
                                None,
                                None.__new__,
                                object.__new__,
                                Enum.__new__,
                                StdlibEnum.__new__
                                ):
                            __new__ = target
                            break
                    if __new__ is not None:
                        break
                else:
                    __new__ = object.__new__
            # if a non-object.__new__ is used then whatever value/tuple was
            # assigned to the enum member name will be passed to __new__ and to the
            # new enum member's __init__
            if __new__ is object.__new__:
                new_uses_args = False
            else:
                new_uses_args = True

            return __new__, save_new, new_uses_args


########################################################
# In order to support Python 2 and 3 with a single
# codebase we have to create the Enum methods separately
# and then use the `type(name, bases, dict)` method to
# create the class.
########################################################
temp_enum_dict = EnumMeta.__prepare__('Enum', (object, ))
temp_enum_dict['__doc__'] = "Generic enumeration.\n\n    Derive from this class to define new enumerations.\n\n"

def __init__(self, *args, **kwds):
    # auto-init method
    _auto_init_ = self._auto_init_
    if _auto_init_ is None:
        return
    if 'value' in _auto_init_:
        # remove 'value' from _auto_init_ as it has already been handled
        _auto_init_ = _auto_init_[1:]
    if _auto_init_:
        if len(_auto_init_) < len(args):
            raise TypeError('%d arguments expected (%s), %d received (%s)'
                    % (len(_auto_init_), _auto_init_, len(args), args))
        for name, arg in zip(_auto_init_, args):
            setattr(self, name, arg)
        if len(args) < len(_auto_init_):
            remaining_args = _auto_init_[len(args):]
            for name in remaining_args:
                value = kwds.pop(name, undefined)
                if value is undefined:
                    raise TypeError('missing value for: %r' % (name, ))
                setattr(self, name, value)
            if kwds:
                # too many keyword arguments
                raise TypeError('invalid keyword(s): %s' % ', '.join(kwds.keys()))
temp_enum_dict['__init__'] = __init__
del __init__

def __new__(cls, value):
    # all enum instances are actually created during class construction
    # without calling this method; this method is called by the metaclass'
    # __call__ (i.e. Color(3) ), and by pickle
    if NoAlias in cls._settings_:
        raise TypeError('NoAlias enumerations cannot be looked up by value')
    if type(value) is cls:
        # For lookups like Color(Color.red)
        # value = value.value
        return value
    # by-value search for a matching enum member
    # see if it's in the reverse mapping (for hashable values)
    try:
        if value in cls._value2member_map_:
            return cls._value2member_map_[value]
    except TypeError:
        # not there, now do long search -- O(n) behavior
        for name, member in cls._value2member_seq_:
            if name == value:
                return member
    # still not found -- try _missing_ hook
    try:
        exc = None
        result = cls._missing_value_(value)
    except Exception as e:
        exc = e
        result = None
    if isinstance(result, cls):
        return result
    else:
        if value is no_arg:
            ve_exc = ValueError('%s() should be called with a value' % (cls.__name__, ))
        else:
            ve_exc = ValueError("%r is not a valid %s" % (value, cls.__name__))
        if result is None and exc is None:
            raise ve_exc
        elif exc is None:
            exc = TypeError(
                    'error in %s._missing_: returned %r instead of None or a valid member'
                    % (cls.__name__, result)
                    )
        exc.__context__ = ve_exc
        raise exc
temp_enum_dict['__new__'] = __new__
del __new__

def __init_subclass__(cls, **kwds):
    if pyver < 3.6:
        # end of the line
        if kwds:
            raise TypeError('unconsumed keyword arguments: %r' % (kwds, ))
    else:
        super(Enum, cls).__init_subclass__(**kwds)
temp_enum_dict['__init_subclass__'] = __init_subclass__

@staticmethod
def _generate_next_value_(name, start, count, last_values, *args, **kwds):
    for last_value in reversed(last_values):
        try:
            return last_value + 1
        except TypeError:
            pass
    else:
        return start
temp_enum_dict['_generate_next_value_'] = _generate_next_value_
del _generate_next_value_

@classmethod
def _missing_(cls, value):
    "deprecated, use _missing_value_ instead"
    return None
temp_enum_dict['_missing_'] = _missing_
del _missing_

@classmethod
def _missing_value_(cls, value):
    "used for failed value access"
    return cls._missing_(value)
temp_enum_dict['_missing_value_'] = _missing_value_
del _missing_value_

@classmethod
def _missing_name_(cls, name):
    "used for failed item access"
    return None
temp_enum_dict['_missing_name_'] = _missing_name_
del _missing_name_

def __repr__(self):
    return "<%s.%s: %r>" % (
            self.__class__.__name__, self._name_, self._value_)
temp_enum_dict['__repr__'] = __repr__
del __repr__

def __str__(self):
    return "%s.%s" % (self.__class__.__name__, self._name_)
temp_enum_dict['__str__'] = __str__
del __str__

if pyver >= 3.0:
    def __dir__(self):
        added_behavior = [
                m
                for cls in self.__class__.mro()
                for m in cls.__dict__
                if m[0] != '_' and m not in self._member_map_
                ]
        return (['__class__', '__doc__', '__module__', ] + added_behavior)
    temp_enum_dict['__dir__'] = __dir__
    del __dir__

def __format__(self, format_spec):
    # mixed-in Enums should use the mixed-in type's __format__, otherwise
    # we can get strange results with the Enum name showing up instead of
    # the value

    # pure Enum branch / overridden __str__ branch
    overridden_str = self.__class__.__str__ != Enum.__str__
    if self._member_type_ is object or overridden_str:
        cls = str
        val = str(self)
    # mix-in branch
    else:
        cls = self._member_type_
        val = self.value
    return cls.__format__(val, format_spec)
temp_enum_dict['__format__'] = __format__
del __format__

def __hash__(self):
    return hash(self._name_)
temp_enum_dict['__hash__'] = __hash__
del __hash__

def __reduce_ex__(self, proto):
    return self.__class__, (self._value_, )
temp_enum_dict['__reduce_ex__'] = __reduce_ex__
del __reduce_ex__


####################################
# Python's less than 2.6 use __cmp__

if pyver < 2.6:

    def __cmp__(self, other):
        if type(other) is self.__class__:
            if self is other:
                return 0
            return -1
        return NotImplemented
        raise TypeError("unorderable types: %s() and %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__cmp__'] = __cmp__
    del __cmp__

else:

    def __le__(self, other):
        raise TypeError("unorderable types: %s() <= %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__le__'] = __le__
    del __le__

    def __lt__(self, other):
        raise TypeError("unorderable types: %s() < %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__lt__'] = __lt__
    del __lt__

    def __ge__(self, other):
        raise TypeError("unorderable types: %s() >= %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__ge__'] = __ge__
    del __ge__

    def __gt__(self, other):
        raise TypeError("unorderable types: %s() > %s()" % (self.__class__.__name__, other.__class__.__name__))
    temp_enum_dict['__gt__'] = __gt__
    del __gt__


def __eq__(self, other):
    if type(other) is self.__class__:
        return self is other
    return NotImplemented
temp_enum_dict['__eq__'] = __eq__
del __eq__

def __ne__(self, other):
    if type(other) is self.__class__:
        return self is not other
    return NotImplemented
temp_enum_dict['__ne__'] = __ne__
del __ne__

def __hash__(self):
    return hash(self._name_)
temp_enum_dict['__hash__'] = __hash__
del __hash__

def __reduce_ex__(self, proto):
    return self.__class__, (self._value_, )
temp_enum_dict['__reduce_ex__'] = __reduce_ex__
del __reduce_ex__

def _convert(cls, name, module, filter, source=None):
    """
    Create a new Enum subclass that replaces a collection of global constants
    """
    # convert all constants from source (or module) that pass filter() to
    # a new Enum called name, and export the enum and its members back to
    # module;
    # also, replace the __reduce_ex__ method so unpickling works in
    # previous Python versions
    module_globals = vars(_sys.modules[module])
    if source:
        source = vars(source)
    else:
        source = module_globals
    members = [(key, source[key]) for key in source.keys() if filter(key)]
    try:
        # sort by value, name
        members.sort(key=lambda t: (t[1], t[0]))
    except TypeError:
        # unless some values aren't comparable, in which case sort by just name
        members.sort(key=lambda t: t[0])
    cls = cls(name, members, module=module)
    cls.__reduce_ex__ = _reduce_ex_by_name
    module_globals.update(cls.__members__)
    module_globals[name] = cls
    return cls
temp_enum_dict['_convert'] = classmethod(_convert)
del _convert

# enum_property is used to provide access to the `name`, `value', etc.,
# properties of enum members while keeping some measure of protection
# from modification, while still allowing for an enumeration to have
# members named `name`, `value`, etc..  This works because enumeration
# members are not set directly on the enum class -- enum_property will
# look them up in _member_map_.

@enum_property
def name(self):
    return self._name_
temp_enum_dict['name'] = name
del name

@enum_property
def value(self):
    return self._value_
temp_enum_dict['value'] = value
del value

@enum_property
def values(self):
    return self._values_
temp_enum_dict['values'] = values
del values

def _reduce_ex_by_name(self, proto):
    return self.name

if StdlibEnum is not None:
    Enum = EnumMeta('Enum', (StdlibEnum, ), temp_enum_dict)
else:
    Enum = EnumMeta('Enum', (object, ), temp_enum_dict)
del temp_enum_dict

# Enum has now been created
###########################

class IntEnum(int, Enum):
    """Enum where members are also (and must be) ints"""

class StrEnum(str, Enum): 
    """Enum where members are also (and must already be) strings
    
        default value is member name
    """
    def __new__(cls, value, *args, **kwds):
        if args or kwds:
            raise TypeError('only a single string value may be specified')
        if not isinstance(value, str):
            raise TypeError('values for StrEnum must be strings, not %r' % type(value))
        obj = str.__new__(cls, value)
        obj._value_ = value
        return obj
    def _generate_next_value_(name, start, count, last_values, *args, **kwds):
        return name

class LowerStrEnum(StrEnum):
    """Enum where members are also (and must already be) lower-case strings
    
        default value is member name, lower-cased
    """
    def __new__(cls, value, *args, **kwds):
        obj = StrEnum.__new_member__(cls, value, *args, **kwds)
        if value != value.lower():
            raise ValueError('%r is not lower-case' % value)
        return obj
    def _generate_next_value_(name, start, count, last_values, *args, **kwds):
        return name.lower()

class UpperStrEnum(StrEnum):
    """Enum where members are also (and must already be) upper-case strings
    
        default value is member name, upper-cased
    """
    def __new__(cls, value, *args, **kwds):
        obj = StrEnum.__new_member__(cls, value, *args, **kwds)
        if value != value.upper():
            raise ValueError('%r is not upper-case' % value)
        return obj
    def _generate_next_value_(name, start, count, last_values, *args, **kwds):
        return name.upper()

if pyver >= 3:
    class AutoEnum(Enum):
        """
        automatically use _generate_next_value_ when values are missing (Python 3 only)
        """
        _settings_ = AutoValue

class AutoNumberEnum(Enum):
    """
    Automatically assign increasing values to members.

    Py3: numbers match creation order
    Py2: numbers are assigned alphabetically by member name
    """
    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

class MultiValueEnum(Enum):
    """
    Multiple values can map to each member.
    """
    _settings_ = MultiValue

class NoAliasEnum(Enum):
    """
    Duplicate value members are distinct, but cannot be looked up by value.
    """
    _settings_ = NoAlias

class OrderedEnum(Enum):
    """
    Add ordering based on values of Enum members.
    """
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self._value_ >= other._value_
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self._value_ > other._value_
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self._value_ <= other._value_
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self._value_ < other._value_
        return NotImplemented

if sqlite3:
    class SqliteEnum(Enum):
        def __conform__(self, protocol):
            if protocol is sqlite3.PrepareProtocol:
                return self.name

class UniqueEnum(Enum):
    """
    Ensure no duplicate values exist.
    """
    _settings_ = Unique


def convert(enum, name, module, filter, source=None):
    """
    Create a new Enum subclass that replaces a collection of global constants

    enum: Enum, IntEnum, ...
    name: name of new Enum
    module: name of module (__name__ in global context)
    filter: function that returns True if name should be converted to Enum member
    source: namespace to check (defaults to 'module')
    """
    # convert all constants from source (or module) that pass filter() to
    # a new Enum called name, and export the enum and its members back to
    # module;
    # also, replace the __reduce_ex__ method so unpickling works in
    # previous Python versions
    module_globals = vars(_sys.modules[module])
    if source:
        source = vars(source)
    else:
        source = module_globals
    members = dict((name, value) for name, value in source.items() if filter(name))
    enum = enum(name, members, module=module)
    enum.__reduce_ex__ = _reduce_ex_by_name
    module_globals.update(enum.__members__)
    module_globals[name] = enum

def extend_enum(enumeration, name, *args, **_private_kwds):
    """
    Add a new member to an existing Enum.
    """
    try:
        _member_map_ = enumeration._member_map_
        _member_names_ = enumeration._member_names_
        _member_type_ = enumeration._member_type_
        _value2member_map_ = enumeration._value2member_map_
        base_attributes = set([a for b in enumeration.mro() for a in b.__dict__])
    except AttributeError:
        raise TypeError('%r is not a supported Enum' % (enumeration, ))
    try:
        _value2member_seq_ = enumeration._value2member_seq_
        # _auto_number_ = enumeration._auto_number_
        _multi_value_ = MultiValue in enumeration._settings_
        _no_alias_ = NoAlias in enumeration._settings_
        _unique_ = Unique in enumeration._settings_
        # _unique_ = Unique in enumeration._settings_
        _auto_init_ = enumeration._auto_init_ or []
    except AttributeError:
        # standard Enum
        _value2member_seq_ = []
        # _auto_number_ = False
        _multi_value_ = False
        _no_alias_ = False
        # _unique_ = False
        _auto_init_ = []
    mt_new = _member_type_.__new__
    _new = getattr(enumeration, '__new_member__', mt_new)
    if not args:
        _gnv = getattr(enumeration, '_generate_next_value_')
        if _gnv is None:
            raise TypeError('value not provided and _generate_next_value_ missing')
        last_values = [m.value for m in enumeration]
        count = len(enumeration)
        start = getattr(enumeration, '_start_')
        if start is None:
            start = last_values and last_values[0] or 1
        args = ( _gnv(name, start, count, last_values), )
    if _new is object.__new__:
        new_uses_args = False
    else:
        new_uses_args = True
    if len(args) == 1:
        [value] = args
    else:
        value = args
    more_values = ()
    kwds = {}
    if isinstance(value, enum):
        args = value.args
        kwds = value.kwds
    if not isinstance(value, tuple):
        args = (value, )
    else:
        args = value
    # tease value out of auto-init if specified
    if 'value' in _auto_init_:
        if 'value' in kwds:
            value = kwds.pop('value')
        else:
            value, args = args[0], args[1:]
    elif _multi_value_:
        value, more_values, args = args[0], args[1:], ()
    if _member_type_ is tuple:
        args = (args, )
    if not new_uses_args:
        new_member = _new(enumeration)
        if not hasattr(new_member, '_value_'):
            new_member._value_ = value
    else:
        new_member = _new(enumeration, *args, **kwds)
        if not hasattr(new_member, '_value_'):
            new_member._value_ = _member_type_(*args)
    value = new_member._value_
    new_member._name_ = name
    new_member.__objclass__ = enumeration.__class__
    new_member.__init__(*args)
    if _private_kwds.get('create_only'):
        return new_member
    # If another member with the same value was already defined, the
    # new member becomes an alias to the existing one.
    is_alias = False
    if _no_alias_:
        # unless NoAlias was specified
        _member_names_.append(name)
        _member_map_[name] = new_member
    else:
        for canonical_member in _member_map_.values():
            _values_ = getattr(canonical_member, '_values_', [canonical_member._value_])
            for canonical_value in _values_:
                if canonical_value == new_member._value_:
                    # name is an alias
                    if _unique_ or _multi_value_:
                        # aliases not allowed if Unique specified
                        raise ValueError('%s is a duplicate of %s' % (name, canonical_member.name))
                    if name not in base_attributes:
                        setattr(enumeration, name, canonical_member)
                    else:
                        # check type of name
                        for parent in enumeration.mro()[1:]:
                            if name in parent.__dict__:
                                obj = parent.__dict__[name]
                                if not isinstance(obj, enum_property):
                                    raise TypeError('%r already used: %r' % (name, obj))
                                break
                    # Aliases don't appear in member names (only in __members__ and _member_map_).
                    _member_map_[new_member._name_] = canonical_member
                    new_member = canonical_member
                    is_alias = True
                    break
            if is_alias:
                break
        else:
            # not an alias
            values = (value, ) + more_values
            new_member._values_ = values
            for value in (value, ) + more_values:
                # first check if value has already been used
                if _multi_value_ and (
                        value in _value2member_map_
                        or any(v == value for (v, m) in _value2member_seq_)
                        ):
                    raise ValueError('%r has already been used' % (value, ))
                try:
                    # This may fail if value is not hashable. We can't add the value
                    # to the map, and by-value lookups for this value will be
                    # linear.
                    if _no_alias_:
                        raise TypeError('cannot use dict to store value')
                    _value2member_map_[value] = new_member
                except TypeError:
                    _value2member_seq_ += ((value, new_member), )
            if name not in base_attributes:
                setattr(enumeration, name, new_member)
            else:
                # check type of name
                for parent in enumeration.mro()[1:]:
                    if name in parent.__dict__:
                        obj = parent.__dict__[name]
                        if not isinstance(obj, enum_property):
                            raise TypeError('%r already used: %r' % (name, obj))
                        break
            _member_names_.append(name)
            _member_map_[name] = new_member
            try:
                _value2member_map_[value] = new_member
            except TypeError:
                pass

def unique(enumeration):
    """
    Class decorator that ensures only unique members exist in an enumeration.
    """
    duplicates = []
    for name, member in enumeration.__members__.items():
        if name != member.name:
            duplicates.append((name, member.name))
    if duplicates:
        duplicate_names = ', '.join(
                ["%s -> %s" % (alias, name) for (alias, name) in duplicates]
                )
        raise ValueError('duplicate names found in %r: %s' %
                (enumeration, duplicate_names)
                )
    return enumeration

class Flag(Enum):
    """Support for flags"""

    def _generate_next_value_(name, start, count, last_values):
        """
        Generate the next value when not given.

        name: the name of the member
        start: the initital start value or None
        count: the number of existing members
        last_value: the last value assigned or None
        """
        if not count:
            return (1, start)[start is not None]
        error = False
        for last_value in reversed(last_values):
            if isinstance(last_value, auto):
                last_value = last_value.value
            try:
                high_bit = _high_bit(last_value)
                break
            except Exception:
                error = True
                break
        if error:
            raise TypeError('invalid Flag value: %r' % (last_value, ))
        return 2 ** (high_bit+1)

    @classmethod
    def _missing_(cls, value):
        original_value = value
        if value < 0:
            value = ~value
        possible_member = cls._create_pseudo_member_(value)
        if original_value < 0:
            possible_member = ~possible_member
        return possible_member

    @classmethod
    def _create_pseudo_member_(cls, *values):
        """
        Create a composite member iff value contains only members.
        """
        value = values[0]
        pseudo_member = cls._value2member_map_.get(value, None)
        if pseudo_member is None:
            # verify all bits are accounted for
            members, extra_flags = _decompose(cls, value)
            if extra_flags:
                raise ValueError("%r is not a valid %s" % (value, cls.__name__))
            # give subclasses a chance to modify values for new pseudo-member
            values = cls._create_pseudo_member_values_(members, *values)
            # construct a singleton enum pseudo-member
            pseudo_member = extend_enum(cls, None, *values, create_only=True)
            # use setdefault in case another thread already created a composite
            # with this value
            pseudo_member = cls._value2member_map_.setdefault(value, pseudo_member)
        return pseudo_member

    @classmethod
    def _create_pseudo_member_values_(cls, members, *values):
        return values

    def __contains__(self, other):
        if not isinstance(other, Flag):
            raise TypeError("%r (%r) is not an <aenum 'Flag'>" % (other, type(other)))
        if not isinstance(other, self.__class__):
            return False
        return other._value_ & self._value_ == other._value_

    def __repr__(self):
        cls = self.__class__
        if self._name_ is not None:
            return '<%s.%s: %r>' % (cls.__name__, self._name_, self._value_)
        members, uncovered = _decompose(cls, self._value_)
        return '<%s.%s: %r>' % (
                cls.__name__,
                '|'.join([str(m._name_ or m._value_) for m in members]),
                self._value_,
                )

    def __str__(self):
        cls = self.__class__
        if self._name_ is not None:
            return '%s.%s' % (cls.__name__, self._name_)
        members, uncovered = _decompose(cls, self._value_)
        if len(members) == 1 and members[0]._name_ is None:
            return '%s.%r' % (cls.__name__, members[0]._value_)
        else:
            return '%s.%s' % (
                    cls.__name__,
                    '|'.join([str(m._name_ or m._value_) for m in members]),
                    )

    def __bool__(self):
        return bool(self._value_)
    if pyver < 3:
        __nonzero__ = __bool__
        del __bool__

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__class__(self._value_ | other._value_)

    def __and__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__class__(self._value_ & other._value_)

    def __xor__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__class__(self._value_ ^ other._value_)

    def __invert__(self):
        members, uncovered = _decompose(self.__class__, self._value_)
        inverted_members = [
                m for m in self.__class__
                if m not in members and not m._value_ & self._value_
                ]
        inverted = reduce(_or_, inverted_members, self.__class__(0))
        return self.__class__(inverted)

    def __iter__(self):
        members, extra_flags = _decompose(self.__class__, self.value)
        return (m for m in members if m._value_ != 0)


class IntFlag(int, Flag):
    """Support for integer-based Flags"""

    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, int):
            raise ValueError("%r is not a valid %s" % (value, cls.__name__))
        new_member = cls._create_pseudo_member_(value)
        return new_member

    @classmethod
    def _create_pseudo_member_(cls, value):
        pseudo_member = cls._value2member_map_.get(value, None)
        if pseudo_member is None:
            need_to_create = [value]
            # get unaccounted for bits
            _, extra_flags = _decompose(cls, value)
            while extra_flags:
                bit = _high_bit(extra_flags)
                flag_value = 2 ** bit
                if (flag_value not in cls._value2member_map_ and
                        flag_value not in need_to_create
                        ):
                    need_to_create.append(flag_value)
                if extra_flags == -flag_value:
                    extra_flags = 0
                else:
                    extra_flags ^= flag_value
            for value in reversed(need_to_create):
                # construct singleton pseudo-members
                pseudo_member = int.__new__(cls, value)
                pseudo_member._name_ = None
                pseudo_member._value_ = value
                # use setdefault in case another thread already created a composite
                # with this value
                pseudo_member = cls._value2member_map_.setdefault(value, pseudo_member)
        return pseudo_member

    def __or__(self, other):
        if not isinstance(other, (self.__class__, int)):
            return NotImplemented
        result = self.__class__(self._value_ | self.__class__(other)._value_)
        return result

    def __and__(self, other):
        if not isinstance(other, (self.__class__, int)):
            return NotImplemented
        return self.__class__(self._value_ & self.__class__(other)._value_)

    def __xor__(self, other):
        if not isinstance(other, (self.__class__, int)):
            return NotImplemented
        return self.__class__(self._value_ ^ self.__class__(other)._value_)

    __ror__ = __or__
    __rand__ = __and__
    __rxor__ = __xor__

    def __invert__(self):
        result = self.__class__(~self._value_)
        return result


def _high_bit(value):
    """returns index of highest bit, or -1 if value is zero or negative"""
    return value.bit_length() - 1

def _decompose(flag, value):
    """Extract all members from the value."""
    # _decompose is only called if the value is not named
    not_covered = value
    negative = value < 0
    # issue29167: wrap accesses to _value2member_map_ in a list to avoid race
    #             conditions between iterating over it and having more psuedo-
    #             members added to it
    if negative:
        # only check for named flags
        flags_to_check = [
                (m, v)
                for v, m in list(flag._value2member_map_.items())
                if m.name is not None
                ]
    else:
        # check for named flags and powers-of-two flags
        flags_to_check = [
                (m, v)
                for v, m in list(flag._value2member_map_.items())
                if m.name is not None or _power_of_two(v)
                ]
    members = []
    for member, member_value in flags_to_check:
        if member_value and member_value & value == member_value:
            members.append(member)
            not_covered &= ~member_value
    if not members and value in flag._value2member_map_:
        members.append(flag._value2member_map_[value])
    members.sort(key=lambda m: m._value_, reverse=True)
    if len(members) > 1 and members[0].value == value:
        # we have the breakdown, don't need the value member itself
        members.pop(0)
    return members, not_covered

def _power_of_two(value):
    if value < 1:
        return False
    return value == 2 ** _high_bit(value)


class module(object):

    def __init__(self, cls, *args):
        self.__name__ = cls.__name__
        self._parent_module = cls.__module__
        self.__all__ = []
        all_objects = cls.__dict__
        if not args:
            args = [k for k, v in all_objects.items() if isinstance(v, (NamedConstant, Enum))]
        for name in args:
            self.__dict__[name] = all_objects[name]
            self.__all__.append(name)

    def register(self):
        _sys.modules["%s.%s" % (self._parent_module, self.__name__)] = self


