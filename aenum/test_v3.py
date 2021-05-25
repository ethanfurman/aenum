from aenum import EnumMeta, Enum, IntEnum, Flag, UniqueEnum, AutoEnum
from aenum import NamedTuple, TupleSize, MagicValue, AddValue, NoAlias, Unique, MultiValue
from aenum import AutoNumberEnum,MultiValueEnum, OrderedEnum, unique, skip, extend_enum

from collections import OrderedDict
from datetime import timedelta
from pickle import dumps, loads, PicklingError, HIGHEST_PROTOCOL
from unittest import TestCase, main

import os
import tempfile
import textwrap
import sys
pyver = float('%s.%s' % sys.version_info[:2])


class TestEnumV3(TestCase):

    def setUp(self):
        class Season(Enum):
            SPRING = 1
            SUMMER = 2
            AUTUMN = 3
            WINTER = 4
        self.Season = Season

        class Konstants(float, Enum):
            E = 2.7182818
            PI = 3.1415926
            TAU = 2 * PI
        self.Konstants = Konstants

        class Grades(IntEnum):
            A = 5
            B = 4
            C = 3
            D = 2
            F = 0
        self.Grades = Grades

        class Directional(str, Enum):
            EAST = 'east'
            WEST = 'west'
            NORTH = 'north'
            SOUTH = 'south'
        self.Directional = Directional

        from datetime import date
        class Holiday(date, Enum):
            NEW_YEAR = 2013, 1, 1
            IDES_OF_MARCH = 2013, 3, 15
        self.Holiday = Holiday

    def test_auto_init(self):
        class Planet(Enum, init='mass radius'):
            MERCURY = (3.303e+23, 2.4397e6)
            VENUS   = (4.869e+24, 6.0518e6)
            EARTH   = (5.976e+24, 6.37814e6)
            MARS    = (6.421e+23, 3.3972e6)
            JUPITER = (1.9e+27,   7.1492e7)
            SATURN  = (5.688e+26, 6.0268e7)
            URANUS  = (8.686e+25, 2.5559e7)
            NEPTUNE = (1.024e+26, 2.4746e7)
            @property
            def surface_gravity(self):
                # universal gravitational constant  (m3 kg-1 s-2)
                G = 6.67300E-11
                return G * self.mass / (self.radius * self.radius)
        self.assertEqual(round(Planet.EARTH.surface_gravity, 2), 9.80)
        self.assertEqual(Planet.EARTH.value, (5.976e+24, 6.37814e6))

    def test_auto_init_with_value(self):
        class Color(Enum, init='value, rgb'):
            RED = 1, (1, 0, 0)
            BLUE = 2, (0, 1, 0)
            GREEN = 3, (0, 0, 1)
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.BLUE.value, 2)
        self.assertEqual(Color.GREEN.value, 3)
        self.assertEqual(Color.RED.rgb, (1, 0, 0))
        self.assertEqual(Color.BLUE.rgb, (0, 1, 0))
        self.assertEqual(Color.GREEN.rgb, (0, 0, 1))

    def test_auto_turns_off(self):
        with self.assertRaises(NameError):
            class Color(Enum, settings=MagicValue):
                red
                green
                blue
                def hello(self):
                    print('Hello!  My serial is %s.' % self.value)
                rose
        with self.assertRaises(NameError):
            class Color(Enum, settings=MagicValue):
                red
                green
                blue
                def __init__(self, *args):
                    pass
                rose

    def test_magic(self):
        class Color(Enum, settings=MagicValue):
            red, green, blue
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue])
        self.assertEqual(Color.red.value, 1)

    def test_ignore_not_overridden(self):
        with self.assertRaisesRegex(TypeError, 'object is not callable'):
            class Color(Flag):
                _ignore_ = 'irrelevent'
                _settings_ = MagicValue
                @property
                def shade(self):
                    print('I am light', self.name.lower())

    def test_magic_start(self):
        class Color(Enum, settings=MagicValue, start=0):
            red, green, blue
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue])
        self.assertEqual(Color.red.value, 0)

    def test_dir_on_class(self):
        Season = self.Season
        self.assertEqual(
            set(dir(Season)),
            set(['__class__', '__doc__', '__members__', '__module__',
                'SPRING', 'SUMMER', 'AUTUMN', 'WINTER']),
            )

    def test_dir_on_item(self):
        Season = self.Season
        self.assertEqual(
            set(dir(Season.WINTER)),
            set(['__class__', '__doc__', '__module__', 'name', 'value', 'values']),
            )

    def test_dir_with_added_behavior(self):
        class Test(Enum):
            this = 'that'
            these = 'those'
            def wowser(self):
                return ("Wowser! I'm %s!" % self.name)
        self.assertEqual(
                set(dir(Test)),
                set(['__class__', '__doc__', '__members__', '__module__', 'this', 'these']),
                )
        self.assertEqual(
                set(dir(Test.this)),
                set(['__class__', '__doc__', '__module__', 'name', 'value', 'values', 'wowser']),
                )

    def test_dir_on_sub_with_behavior_on_super(self):
        # see issue22506
        class SuperEnum(Enum):
            def invisible(self):
                return "did you see me?"
        class SubEnum(SuperEnum):
            sample = 5
        self.assertEqual(
                set(dir(SubEnum.sample)),
                set(['__class__', '__doc__', '__module__', 'name', 'value', 'values', 'invisible']),
                )

    def test_members_are_always_ordered(self):
        class AlwaysOrdered(Enum):
            first = 1
            second = 2
            third = 3
        self.assertTrue(type(AlwaysOrdered.__members__) is OrderedDict)

    def test_comparisons(self):
        def bad_compare():
            Season.SPRING > 4
        Season = self.Season
        self.assertNotEqual(Season.SPRING, 1)
        self.assertRaises(TypeError, bad_compare)

        class Part(Enum):
            SPRING = 1
            CLIP = 2
            BARREL = 3

        self.assertNotEqual(Season.SPRING, Part.SPRING)
        def bad_compare():
            Season.SPRING < Part.CLIP
        self.assertRaises(TypeError, bad_compare)

    def test_duplicate_name(self):
        with self.assertRaises(TypeError):
            class Color1(Enum):
                red = 1
                green = 2
                blue = 3
                red = 4

        with self.assertRaises(TypeError):
            class Color2(Enum):
                red = 1
                green = 2
                blue = 3
                def red(self):
                    return 'red'

        with self.assertRaises(TypeError):
            class Color3(Enum):
                @property
                def red(self):
                    return 'redder'
                red = 1
                green = 2
                blue = 3

    def test_duplicate_value_with_unique(self):
        with self.assertRaises(ValueError):
            class Color(Enum, settings=Unique):
                red = 1
                green = 2
                blue = 3
                rojo = 1

    def test_duplicate_value_with_noalias(self):
        class Color(Enum, settings=NoAlias):
            red = 1
            green = 2
            blue = 3
            rojo = 1
        self.assertFalse(Color.red is Color.rojo)
        self.assertEqual(Color.red.value, 1)
        self.assertEqual(Color.rojo.value, 1)
        self.assertEqual(len(Color), 4)
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue, Color.rojo])

    def test_noalias_value_lookup(self):
        class Color(Enum, settings=NoAlias):
            red = 1
            green = 2
            blue = 3
            rojo = 1
        self.assertRaises(TypeError, Color, 2)

    def test_multivalue(self):
        class Color(Enum, settings=MultiValue):
            red = 1, 'red'
            green = 2, 'green'
            blue = 3, 'blue'
        self.assertEqual(Color.red.value, 1)
        self.assertIs(Color('green'), Color.green)
        self.assertEqual(Color.blue.values, (3, 'blue'))

    def test_multivalue_with_duplicate_values(self):
        with self.assertRaises(ValueError):
            class Color(Enum, settings=MultiValue):
                red = 1, 'red'
                green = 2, 'green'
                blue = 3, 'blue', 'red'

    def test_multivalue_with_duplicate_values_and_noalias(self):
        with self.assertRaises(TypeError):
            class Color(Enum, settings=(MultiValue, NoAlias)):
                red = 1, 'red'
                green = 2, 'green'
                blue = 3, 'blue', 'red'

    def test_multivalue_and_auto(self):
        with self.assertRaisesRegex(TypeError, r'MultiValue and MagicValue are mutually exclusive'):
            class Color(Enum, settings=(MultiValue, MagicValue)):
                red
                green = 3, 'green'
                blue

    def test_autonumber_and_init(self):
        class Field(IntEnum, settings=AddValue, init='__doc__'):
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
        self.assertEqual(Field.TYPE, 1)
        self.assertEqual(Field.START, 2)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')
        self.assertFalse(hasattr(Field, '_order_'))

    def test_autovalue_and_init(self):
        class Field(IntEnum, init='value __doc__'):
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
        self.assertEqual(Field.TYPE, 1)
        self.assertEqual(Field.START.__doc__, 'Field offset in record')

    def test_autonumber_and_start(self):
        class Field(IntEnum, init='__doc__', settings=AddValue, start=0):
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
        self.assertEqual(Field.TYPE, 0)
        self.assertEqual(Field.START, 1)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')

    def test_autonumber_and_init_and_some_values(self):
        class Field(IntEnum, init='value __doc__'):
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
            BLAH = 5, "test blah"
            BELCH = 'test belch'
        self.assertEqual(Field.TYPE, 1)
        self.assertEqual(Field.START, 2)
        self.assertEqual(Field.BLAH, 5)
        self.assertEqual(Field.BELCH, 6)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')
        self.assertEqual(Field.BLAH.__doc__, 'test blah')
        self.assertEqual(Field.BELCH.__doc__, 'test belch')

    def test_autonumber_with_irregular_values(self):
        class Point(AutoNumberEnum, init='x y'):
            first = 7, 9
            second = 11, 13
        self.assertEqual(Point.first.value, 1)
        self.assertEqual(Point.first.x, 7)
        self.assertEqual(Point.first.y, 9)
        self.assertEqual(Point.second.value, 2)
        self.assertEqual(Point.second.x, 11)
        self.assertEqual(Point.second.y, 13)
        with self.assertRaisesRegex(TypeError, '.*number of fields provided do not match init ...x., .y.. != .3, 11, 13..'):
            class Point(AutoNumberEnum, init='x y'):
                first = 7, 9
                second = 3, 11, 13
        class Color(AutoNumberEnum, init='__doc__'):
            # interactions between AutoNumberEnum and _generate_next_value_ may not be pretty
            red = ()
            green = 'red'
            blue = ()
        self.assertTrue(Color.red.__doc__, 1)
        self.assertEqual(Color.green.__doc__, 'red')
        self.assertTrue(Color.blue.__doc__, 2)

    def test_autonumber_and_property(self):
        with self.assertRaises(TypeError):
            class Color(AutoEnum):
                _ignore_ = ()
                red = ()
                green = ()
                blue = ()
                @property
                def cap_name(self) -> str:
                    return self.name.title()

    def test_autoenum(self):
        class Color(AutoEnum):
            red
            green
            blue
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue])
        self.assertEqual([m.value for m in Color], [1, 2, 3])
        self.assertEqual([m.name for m in Color], ['red', 'green', 'blue'])

    def test_autoenum_with_str(self):
        class Color(AutoEnum):
            def _generate_next_value_(name, start, count, last_values):
                return name
            red
            green
            blue
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue])
        self.assertEqual([m.value for m in Color], ['red', 'green', 'blue'])
        self.assertEqual([m.name for m in Color], ['red', 'green', 'blue'])

    def test_autoenum_and_default_ignore(self):
        class Color(AutoEnum):
            red
            green
            blue
            @property
            def cap_name(self):
                return self.name.title()
        self.assertEqual(Color.blue.cap_name, 'Blue')

    def test_autonumber_and_overridden_ignore(self):
        with self.assertRaises(TypeError):
            class Color(AutoEnum):
                _ignore_ = 'staticmethod'
                red
                green
                blue
                @property
                def cap_name(self) -> str:
                    return self.name.title()

    def test_autonumber_and_multiple_assignment(self):
        class Color(AutoEnum):
            _ignore_ = 'property'
            red
            green
            blue = cyan
            @property
            def cap_name(self) -> str:
                return self.name.title()
        self.assertEqual(Color.blue.cap_name, 'Cyan')

    def test_multivalue_and_autonumber_inherited(self):
        class Measurement(int, Enum, settings=(MultiValue, AddValue), start=0):
            one = "20110721"
            two = "20120911"
            three = "20110518"
        M = Measurement
        self.assertEqual(M.one, 0)
        self.assertTrue(M.one is M(0) is M('20110721'))

    def test_combine_new_settings_with_old_settings(self):
        class Auto(Enum, settings=Unique):
            pass
        with self.assertRaises(ValueError):
            class AutoUnique(Auto, settings=MagicValue):
                BLAH
                BLUH
                ICK = 1

    def test_timedelta(self):
        class Period(timedelta, Enum):
            '''
            different lengths of time
            '''
            _init_ = 'value period'
            _settings_ = NoAlias
            _ignore_ = 'Period i'
            Period = vars()
            for i in range(31):
                Period['day_%d' % i] = i, 'day'
            for i in range(15):
                Period['week_%d' % i] = i*7, 'week'
            for i in range(12):
                Period['month_%d' % i] = i*30, 'month'
            OneDay = day_1
            OneWeek = week_1
        self.assertFalse(hasattr(Period, '_ignore_'))
        self.assertFalse(hasattr(Period, 'Period'))
        self.assertFalse(hasattr(Period, 'i'))
        self.assertTrue(isinstance(Period.day_1, timedelta))

    def test_extend_enum_plain(self):
        class Color(UniqueEnum):
            red = 1
            green = 2
            blue = 3
        extend_enum(Color, 'brown', 4)
        self.assertEqual(Color.brown.name, 'brown')
        self.assertEqual(Color.brown.value, 4)
        self.assertTrue(Color.brown in Color)
        self.assertEqual(len(Color), 4)

    def test_extend_enum_shadow(self):
        class Color(UniqueEnum):
            red = 1
            green = 2
            blue = 3
        extend_enum(Color, 'value', 4)
        self.assertEqual(Color.value.name, 'value')
        self.assertEqual(Color.value.value, 4)
        self.assertTrue(Color.value in Color)
        self.assertEqual(len(Color), 4)
        self.assertEqual(Color.red.value, 1)

    def test_extend_enum_generate(self):
        class Foo(AutoEnum):
            def _generate_next_value_(name, start, count, values, *args, **kwds):
                return name
            a
            b
        #
        extend_enum(Foo, 'c')
        self.assertEqual(Foo.a.value, 'a')
        self.assertEqual(Foo.b.value, 'b')
        self.assertEqual(Foo.c.value, 'c')

    def test_extend_enum_unique_with_duplicate(self):
        with self.assertRaises(ValueError):
            class Color(Enum, settings=Unique):
                red = 1
                green = 2
                blue = 3
            extend_enum(Color, 'value', 1)

    def test_extend_enum_multivalue_with_duplicate(self):
        with self.assertRaises(ValueError):
            class Color(Enum, settings=MultiValue):
                red = 1, 'rojo'
                green = 2, 'verde'
                blue = 3, 'azul'
            extend_enum(Color, 'value', 2)

    def test_extend_enum_noalias_with_duplicate(self):
        class Color(Enum, settings=NoAlias):
            red = 1
            green = 2
            blue = 3
        extend_enum(Color, 'value', 3, )
        self.assertRaises(TypeError, Color, 3)
        self.assertFalse(Color.value is Color.blue)
        self.assertTrue(Color.value.value, 3)

    def test_no_duplicates(self):
        def bad_duplicates():
            class Color(UniqueEnum):
                red = 1
                green = 2
                blue = 3
            class Color(UniqueEnum):
                red = 1
                green = 2
                blue = 3
                grene = 2
        self.assertRaises(ValueError, bad_duplicates)

    def test_no_duplicates_kinda(self):
        class Silly(UniqueEnum):
            one = 1
            two = 'dos'
            name = 3
        class Sillier(IntEnum, UniqueEnum):
            single = 1
            name = 2
            triple = 3
            value = 4

    def test_auto_number(self):
        class Color(Enum, settings=MagicValue):
            red
            blue
            green

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 1)
        self.assertEqual(Color.blue.value, 2)
        self.assertEqual(Color.green.value, 3)

    def test_auto_name(self):
        class Color(Enum, settings=MagicValue):
            def _generate_next_value_(name, start, count, last):
                return name
            red
            blue
            green

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 'red')
        self.assertEqual(Color.blue.value, 'blue')
        self.assertEqual(Color.green.value, 'green')

    def test_auto_name_inherit(self):
        class AutoNameEnum(Enum):
            def _generate_next_value_(name, start, count, last):
                return name
        class Color(AutoNameEnum, settings=MagicValue):
            red
            blue
            green

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 'red')
        self.assertEqual(Color.blue.value, 'blue')
        self.assertEqual(Color.green.value, 'green')

    def test_auto_garbage(self):
        class Color(Enum):
            _settings_ = MagicValue
            red = 'red'
            blue
        self.assertEqual(Color.blue.value, 1)

    def test_auto_garbage_corrected(self):
        class Color(Enum, settings=MagicValue):
            red = 'red'
            blue = 2
            green

        self.assertEqual(list(Color), [Color.red, Color.blue, Color.green])
        self.assertEqual(Color.red.value, 'red')
        self.assertEqual(Color.blue.value, 2)
        self.assertEqual(Color.green.value, 3)

    def test_duplicate_auto(self):
        class Dupes(Enum, settings=MagicValue):
            first = primero
            second
            third
        self.assertEqual([Dupes.first, Dupes.second, Dupes.third], list(Dupes))

    def test_order_as_function(self):
        # first with _init_
        class TestSequence(Enum):
            _init_ = 'value, sequence'
            _order_ = lambda member: member.sequence
            item_id                  = 'An$(1,6)',      0     # Item Code
            company_id               = 'An$(7,2)',      1     # Company Code
            warehouse_no             = 'An$(9,4)',      2     # Warehouse Number
            company                  = 'Hn$(13,6)',     3     # 4 SPACES + COMPANY
            key_type                 = 'Cn$(19,3)',     4     # Key Type = '1**'
            available                = 'Zn$(1,1)',      5     # Available?
            contract_item            = 'Bn(2,1)',       6     # Contract Item?
            sales_category           = 'Fn',            7     # Sales Category
            gl_category              = 'Rn$(5,1)',      8     # G/L Category
            warehouse_category       = 'Sn$(6,1)',      9     # Warehouse Category
            inv_units                = 'Qn$(7,2)',     10     # Inv Units
        for i, member in enumerate(TestSequence):
            self.assertEqual(i, member.sequence)
        ts = TestSequence
        self.assertEqual(ts.item_id.name, 'item_id')
        self.assertEqual(ts.item_id.value, 'An$(1,6)')
        self.assertEqual(ts.item_id.sequence, 0)
        self.assertEqual(ts.company_id.name, 'company_id')
        self.assertEqual(ts.company_id.value, 'An$(7,2)')
        self.assertEqual(ts.company_id.sequence, 1)
        self.assertEqual(ts.warehouse_no.name, 'warehouse_no')
        self.assertEqual(ts.warehouse_no.value, 'An$(9,4)')
        self.assertEqual(ts.warehouse_no.sequence, 2)
        self.assertEqual(ts.company.name, 'company')
        self.assertEqual(ts.company.value, 'Hn$(13,6)')
        self.assertEqual(ts.company.sequence, 3)
        self.assertEqual(ts.key_type.name, 'key_type')
        self.assertEqual(ts.key_type.value, 'Cn$(19,3)')
        self.assertEqual(ts.key_type.sequence, 4)
        self.assertEqual(ts.available.name, 'available')
        self.assertEqual(ts.available.value, 'Zn$(1,1)')
        self.assertEqual(ts.available.sequence, 5)
        self.assertEqual(ts.contract_item.name, 'contract_item')
        self.assertEqual(ts.contract_item.value, 'Bn(2,1)')
        self.assertEqual(ts.contract_item.sequence, 6)
        self.assertEqual(ts.sales_category.name, 'sales_category')
        self.assertEqual(ts.sales_category.value, 'Fn')
        self.assertEqual(ts.sales_category.sequence, 7)
        self.assertEqual(ts.gl_category.name, 'gl_category')
        self.assertEqual(ts.gl_category.value, 'Rn$(5,1)')
        self.assertEqual(ts.gl_category.sequence, 8)
        self.assertEqual(ts.warehouse_category.name, 'warehouse_category')
        self.assertEqual(ts.warehouse_category.value, 'Sn$(6,1)')
        self.assertEqual(ts.warehouse_category.sequence, 9)
        self.assertEqual(ts.inv_units.name, 'inv_units')
        self.assertEqual(ts.inv_units.value, 'Qn$(7,2)')
        self.assertEqual(ts.inv_units.sequence, 10)
        # and then without
        class TestSequence(Enum):
            _order_ = lambda member: member.value[1]
            item_id                  = 'An$(1,6)',      0     # Item Code
            company_id               = 'An$(7,2)',      1     # Company Code
            warehouse_no             = 'An$(9,4)',      2     # Warehouse Number
            company                  = 'Hn$(13,6)',     3     # 4 SPACES + COMPANY
            key_type                 = 'Cn$(19,3)',     4     # Key Type = '1**'
            available                = 'Zn$(1,1)',      5     # Available?
            contract_item            = 'Bn(2,1)',       6     # Contract Item?
            sales_category           = 'Fn',            7     # Sales Category
            gl_category              = 'Rn$(5,1)',      8     # G/L Category
            warehouse_category       = 'Sn$(6,1)',      9     # Warehouse Category
            inv_units                = 'Qn$(7,2)',     10     # Inv Units
        for i, member in enumerate(TestSequence):
            self.assertEqual(i, member.value[1])
        ts = TestSequence
        self.assertEqual(ts.item_id.name, 'item_id')
        self.assertEqual(ts.item_id.value, ('An$(1,6)', 0))
        self.assertEqual(ts.company_id.name, 'company_id')
        self.assertEqual(ts.company_id.value, ('An$(7,2)', 1))
        self.assertEqual(ts.warehouse_no.name, 'warehouse_no')
        self.assertEqual(ts.warehouse_no.value, ('An$(9,4)', 2))
        self.assertEqual(ts.company.name, 'company')
        self.assertEqual(ts.company.value, ('Hn$(13,6)', 3))
        self.assertEqual(ts.key_type.name, 'key_type')
        self.assertEqual(ts.key_type.value, ('Cn$(19,3)', 4))
        self.assertEqual(ts.available.name, 'available')
        self.assertEqual(ts.available.value, ('Zn$(1,1)', 5))
        self.assertEqual(ts.contract_item.name, 'contract_item')
        self.assertEqual(ts.contract_item.value, ('Bn(2,1)', 6))
        self.assertEqual(ts.sales_category.name, 'sales_category')
        self.assertEqual(ts.sales_category.value, ('Fn', 7))
        self.assertEqual(ts.gl_category.name, 'gl_category')
        self.assertEqual(ts.gl_category.value, ('Rn$(5,1)', 8))
        self.assertEqual(ts.warehouse_category.name, 'warehouse_category')
        self.assertEqual(ts.warehouse_category.value, ('Sn$(6,1)', 9))
        self.assertEqual(ts.inv_units.name, 'inv_units')
        self.assertEqual(ts.inv_units.value, ('Qn$(7,2)', 10))
        # then with _init_ but without value
        with self.assertRaises(TypeError):
            class TestSequence(Enum):
                _init_ = 'sequence'
                _order_ = lambda member: member.sequence
                item_id                  = 'An$(1,6)',      0     # Item Code
                company_id               = 'An$(7,2)',      1     # Company Code
                warehouse_no             = 'An$(9,4)',      2     # Warehouse Number
                company                  = 'Hn$(13,6)',     3     # 4 SPACES + COMPANY
                key_type                 = 'Cn$(19,3)',     4     # Key Type = '1**'
                available                = 'Zn$(1,1)',      5     # Available?
                contract_item            = 'Bn(2,1)',       6     # Contract Item?
                sales_category           = 'Fn',            7     # Sales Category
                gl_category              = 'Rn$(5,1)',      8     # G/L Category
                warehouse_category       = 'Sn$(6,1)',      9     # Warehouse Category
                inv_units                = 'Qn$(7,2)',     10     # Inv Units
        # finally, out of order so Python 3 barfs
        with self.assertRaises(TypeError):
            class TestSequence(Enum):
                _init_ = 'sequence'
                _order_ = lambda member: member.sequence
                item_id                  = 'An$(1,6)',      0     # Item Code
                warehouse_no             = 'An$(9,4)',      2     # Warehouse Number
                company                  = 'Hn$(13,6)',     3     # 4 SPACES + COMPANY
                company_id               = 'An$(7,2)',      1     # Company Code
                inv_units                = 'Qn$(7,2)',     10     # Inv Units
                available                = 'Zn$(1,1)',      5     # Available?
                contract_item            = 'Bn(2,1)',       6     # Contract Item?
                sales_category           = 'Fn',            7     # Sales Category
                key_type                 = 'Cn$(19,3)',     4     # Key Type = '1**'
                gl_category              = 'Rn$(5,1)',      8     # G/L Category
                warehouse_category       = 'Sn$(6,1)',      9     # Warehouse Category

    if pyver >= 3.3:
        def test_missing(self):
            class Color(Enum):
                red = 1
                green = 2
                blue = 3
                @classmethod
                def _missing_(cls, item):
                    if item == 'three':
                        return cls.blue
                    elif item == 'bad return':
                        # trigger internal error
                        return 5
                    elif item == 'error out':
                        raise ZeroDivisionError
                    else:
                        # trigger not found
                        return None
            self.assertIs(Color('three'), Color.blue)
            self.assertRaises(ValueError, Color, 7)
            try:
                Color('bad return')
            except TypeError as exc:
                self.assertTrue(isinstance(exc.__cause__, ValueError))
            else:
                raise Exception('Exception not raised.')
            try:
                Color('error out')
            except ZeroDivisionError as exc:
                self.assertTrue(isinstance(exc.__cause__, ValueError))
            else:
                raise Exception('Exception not raised.')

    def test_enum_of_types(self):
        """Support using Enum to refer to types deliberately."""
        class MyTypes(Enum):
            i = int
            f = float
            s = str
        self.assertEqual(MyTypes.i.value, int)
        self.assertEqual(MyTypes.f.value, float)
        self.assertEqual(MyTypes.s.value, str)
        class Foo:
            pass
        class Bar:
            pass
        class MyTypes2(Enum):
            a = Foo
            b = Bar
        self.assertEqual(MyTypes2.a.value, Foo)
        self.assertEqual(MyTypes2.b.value, Bar)
        class SpamEnumNotInner:
            pass
        class SpamEnum(Enum):
            spam = SpamEnumNotInner
        self.assertEqual(SpamEnum.spam.value, SpamEnumNotInner)

    def test_nested_classes_in_enum_do_not_create_members(self):
        """Support locally-defined nested classes."""
        # manually set __qualname__ to remove testing framework noise
        class Outer(Enum):
            __qualname__ = "Outer"
            a = 1
            b = 2
            class Inner(Enum):
                __qualname__ = "Outer.Inner"
                foo = 10
                bar = 11
        self.assertTrue(isinstance(Outer.Inner, type))
        self.assertEqual(Outer.a.value, 1)
        self.assertEqual(Outer.Inner.foo.value, 10)
        self.assertEqual(
            list(Outer.Inner),
            [Outer.Inner.foo, Outer.Inner.bar],
            )
        self.assertEqual(
            list(Outer),
            [Outer.a, Outer.b],
            )

    if pyver == 3.4:
        def test_class_nested_enum_and_pickle_protocol_four(self):
            # would normally just have this directly in the class namespace
            class NestedEnum(Enum):
                twigs = 'common'
                shiny = 'rare'

            self.__class__.NestedEnum = NestedEnum
            self.NestedEnum.__qualname__ = '%s.NestedEnum' % self.__class__.__name__
            test_pickle_exception(
                    self.assertRaises, PicklingError, self.NestedEnum.twigs,
                    protocol=(0, 3))
            test_pickle_dump_load(self.assertTrue, self.NestedEnum.twigs,
                    protocol=(4, HIGHEST_PROTOCOL))

    elif pyver >= 3.5:
        def test_class_nested_enum_and_pickle_protocol_four(self):
            # would normally just have this directly in the class namespace
            class NestedEnum(Enum):
                twigs = 'common'
                shiny = 'rare'

            self.__class__.NestedEnum = NestedEnum
            self.NestedEnum.__qualname__ = '%s.NestedEnum' % self.__class__.__name__
            test_pickle_dump_load(self.assertTrue, self.NestedEnum.twigs,
                    protocol=(0, HIGHEST_PROTOCOL))

    if pyver >= 3.4:
        def test_enum_injection(self):
            class Color(Enum):
                _order_ = 'BLACK WHITE'
                BLACK = Color('black', '#000')
                WHITE = Color('white', '#fff')

                def __init__(self, label, hex):
                    self.label = label
                    self.hex = hex

            self.assertEqual([Color.BLACK, Color.WHITE], list(Color))
            self.assertEqual(Color.WHITE.hex, '#fff')
            self.assertEqual(Color.BLACK.label, 'black')

        def test_subclasses_with_getnewargs_ex(self):
            class NamedInt(int):
                __qualname__ = 'NamedInt'       # needed for pickle protocol 4
                def __new__(cls, *args):
                    _args = args
                    if len(args) < 2:
                        raise TypeError("name and value must be specified")
                    name, args = args[0], args[1:]
                    self = int.__new__(cls, *args)
                    self._intname = name
                    self._args = _args
                    return self
                def __getnewargs_ex__(self):
                    return self._args, {}
                @property
                def __name__(self):
                    return self._intname
                def __repr__(self):
                    # repr() is updated to include the name and type info
                    return "{}({!r}, {})".format(type(self).__name__,
                                                 self.__name__,
                                                 int.__repr__(self))
                def __str__(self):
                    # str() is unchanged, even if it relies on the repr() fallback
                    base = int
                    base_str = base.__str__
                    if base_str.__objclass__ is object:
                        return base.__repr__(self)
                    return base_str(self)
                # for simplicity, we only define one operator that
                # propagates expressions
                def __add__(self, other):
                    temp = int(self) + int( other)
                    if isinstance(self, NamedInt) and isinstance(other, NamedInt):
                        return NamedInt(
                            '({0} + {1})'.format(self.__name__, other.__name__),
                            temp )
                    else:
                        return temp

            class NEI(NamedInt, Enum):
                __qualname__ = 'NEI'      # needed for pickle protocol 4
                x = ('the-x', 1)
                y = ('the-y', 2)


            self.assertIs(NEI.__new__, Enum.__new__)
            self.assertEqual(repr(NEI.x + NEI.y), "NamedInt('(the-x + the-y)', 3)")
            globals()['NamedInt'] = NamedInt
            globals()['NEI'] = NEI
            NI5 = NamedInt('test', 5)
            self.assertEqual(NI5, 5)
            test_pickle_dump_load(self.assertEqual, NI5, 5, protocol=(4, HIGHEST_PROTOCOL))
            self.assertEqual(NEI.y.value, 2)
            test_pickle_dump_load(self.assertTrue, NEI.y, protocol=(4, HIGHEST_PROTOCOL))


class TestOrderV3(TestCase):
    """
    Test definition order versus _order_ order.
    """

    def test_same_members(self):
        class Color(Enum):
            _order_ = 'red green blue'
            red = 1
            green = 2
            blue = 3

    def test_same_members_with_aliases(self):
        class Color(Enum):
            _order_ = 'red green blue'
            red = 1
            green = 2
            blue = 3
            verde = green

    def test_same_members_wrong_order(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Enum):
                _order_ = 'red green blue'
                red = 1
                blue = 3
                green = 2

    def test_order_has_extra_members(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Enum):
                _order_ = 'red green blue purple'
                red = 1
                green = 2
                blue = 3

    def test_order_has_extra_members_with_aliases(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Enum):
                _order_ = 'red green blue purple'
                red = 1
                green = 2
                blue = 3
                verde = green

    def test_enum_has_extra_members(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Enum):
                _order_ = 'red green blue'
                red = 1
                green = 2
                blue = 3
                purple = 4

    def test_enum_has_extra_members_with_aliases(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Enum):
                _order_ = 'red green blue'
                red = 1
                green = 2
                blue = 3
                purple = 4
                verde = green

    def test_same_members_flag(self):
        class Color(Flag):
            _order_ = 'red green blue'
            red = 1
            green = 2
            blue = 4

    def test_same_members_with_aliases_flag(self):
        class Color(Flag):
            _order_ = 'red green blue'
            red = 1
            green = 2
            blue = 4
            verde = green

    def test_same_members_wrong_order_falg(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Flag):
                _order_ = 'red green blue'
                red = 1
                blue = 4
                green = 2

    def test_order_has_extra_members_flag(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Flag):
                _order_ = 'red green blue purple'
                red = 1
                green = 2
                blue = 4

    def test_order_has_extra_members_with_aliases_flag(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Flag):
                _order_ = 'red green blue purple'
                red = 1
                green = 2
                blue = 4
                verde = green

    def test_enum_has_extra_members_flag(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Flag):
                _order_ = 'red green blue'
                red = 1
                green = 2
                blue = 4
                purple = 8

    def test_enum_has_extra_members_with_aliases_flag(self):
        with self.assertRaisesRegex(TypeError, 'member order does not match _order_'):
            class Color(Flag):
                _order_ = 'red green blue'
                red = 1
                green = 2
                blue = 4
                purple = 8
                verde = green


class TestNamedTupleV3(TestCase):

    def test_fixed_size(self):
        class Book(NamedTuple, size=TupleSize.fixed):
            title = 0
            author = 1
            genre = 2
        b = Book('Teckla', 'Steven Brust', 'fantasy')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertTrue('fantasy' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        self.assertRaises(TypeError, Book, 'Teckla', 'Steven Brust')
        self.assertRaises(TypeError, Book, 'Teckla')

    def test_minimum_size(self):
        class Book(NamedTuple, size=TupleSize.minimum):
            title = 0
            author = 1
        b = Book('Teckla', 'Steven Brust', 'fantasy')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertTrue('fantasy' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        self.assertEqual(b[2], 'fantasy')
        b = Book('Teckla', 'Steven Brust')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        self.assertRaises(TypeError, Book, 'Teckla')

    def test_variable_size(self):
        class Book(NamedTuple, size=TupleSize.variable):
            title = 0
            author = 1
            genre = 2
        b = Book('Teckla', 'Steven Brust', 'fantasy')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertTrue('fantasy' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        self.assertEqual(b.genre, 'fantasy')
        b = Book('Teckla', 'Steven Brust')
        self.assertTrue('Teckla' in b)
        self.assertTrue('Steven Brust' in b)
        self.assertEqual(b.title, 'Teckla')
        self.assertEqual(b.author, 'Steven Brust')
        self.assertRaises(AttributeError, getattr, b, 'genre')
        self.assertRaises(TypeError, Book, title='Teckla', genre='fantasy')
        self.assertRaises(TypeError, Book, author='Steven Brust')



class TestStackoverflowAnswersV3(TestCase):

    def test_self_referential_directions(self):
        # https://stackoverflow.com/a/64000706/208880
        class Directions(Enum):
            #
            NORTH = 1, 0
            WEST = 0, 1
            SOUTH = -1, 0
            EAST = 0, -1
            #
            def __init__(self, x, y):
                self.x = x
                self.y = y
                if len(self.__class__):
                    # make links
                    all = list(self.__class__)
                    left, right = all[0], all[-1]
                    self.left = left
                    self.right = right
                    left.right = self
                    right.left = self
        #
        D = Directions
        self.assertEqual(D.NORTH.value, (1, 0))
        self.assertTrue(D.NORTH.left is D.WEST)
        self.assertTrue(D.SOUTH.right is D.WEST)

    def test_self_referential_rock_paper_scissors(self):
        # https://stackoverflow.com/a/57085357/208880
        class RPS(Enum):
            #
            Rock = "rock"
            Paper = "paper"
            Scissors = "scissors"
            #
            def __init__(self, value):
                if len(self.__class__):
                    # make links
                    all = list(self.__class__)
                    first, previous = all[0], all[-1]
                    first.beats = self
                    self.beats = previous
        #
        self.assertTrue(RPS.Rock.beats is RPS.Scissors)
        self.assertTrue(RPS.Scissors.beats is RPS.Paper)
        self.assertTrue(RPS.Paper.beats is RPS.Rock)

    def test_arduino_headers(self):
        # https://stackoverflow.com/q/65048495/208880
        class CHeader(Enum):
            def __init_subclass__(cls, **kwds):
                # write Enums to C header file
                cls_name = cls.__name__
                header_path = getattr(cls, '_%s__header' % cls_name)
                with open(header_path, 'w') as fh:
                    fh.write('initial header stuff here\n')
                    for enum in cls:
                        fh.write('#define %s %r\n' % (enum.name, enum.value))
        class Arduino(CHeader):
            __header = os.path.join(tempdir, 'arduino.h')
            ONE = 1
            TWO = 2
        with open(os.path.join(tempdir, 'arduino.h')) as fh:
                data = fh.read()
        self.assertEqual(textwrap.dedent("""\
                initial header stuff here
                #define ONE 1
                #define TWO 2
                """),
                data,
                )

    def test_create_C_like_Enum(self):
        # https://stackoverflow.com/a/35965438/208880
        class Id(Enum, settings=MagicValue, start=0):
            #
            NONE  # 0x0
            HEARTBEAT  # 0x1
            FLUID_TRANSFER_REQUEST
            FLUID_TRANSFER_STATUS_MSG
            FLUID_TRANSFER_ERROR_MSG
            # ...
            #
            # Camera App Messages
            START_SENDING_PICTURES = 0x010000
            STOP_SENDING_PICTURES
            START_RECORDING_VIDEO_REQ
            STOP_RECORDING_VIDEO_REQ
            # ...
            #
            # Sensor Calibration
            VOLUME_REQUEST = 0x020000
            START_CAL
            CLI_COMMAND_REQUEST
            CLI_COMMAND_RESPONSE
            #
            # File Mananger
            NEW_DELIVERY_REQ = 0x30000
            GET_DELIVERY_FILE_REQ
            GET_FILE_REQ
            #
            ACK_NACK
            RESPONSE
            #
            LAST_ID
        #
        self.assertEqual(Id.NONE.value, 0)
        self.assertEqual(Id.FLUID_TRANSFER_ERROR_MSG.value, 4)
        self.assertEqual(Id.START_SENDING_PICTURES.value, 0x010000)
        self.assertEqual(Id.STOP_RECORDING_VIDEO_REQ.value, 0x010003)
        self.assertEqual(Id.START_CAL.value, 0x020001)
        self.assertEqual(Id.LAST_ID.value, 0x30005)


    if pyver >= 3.5:
        def test_c_header_scanner(self):
            # https://stackoverflow.com/questions/58732872/208880
            with open(os.path.join(tempdir, 'c_plus_plus.h'), 'w') as fh:
                fh.write("""
                        stuff before
                        enum hello {
                            Zero,
                            One,
                            Two,
                            Three,
                            Five=5,
                            Six,
                            Ten=10
                            };
                        in the middle
                        enum blah
                            {
                            alpha,
                            beta,
                            gamma = 10 ,
                            zeta = 50
                            };
                        at the end
                        """)
            from pyparsing import Group, Optional, Suppress, Word, ZeroOrMore
            from pyparsing import alphas, alphanums, nums
            #
            CPPEnum = None
            class CPPEnumType(EnumMeta):
                #
                @classmethod
                def __prepare__(metacls, clsname, bases, **kwds):
                    # return a standard dictionary for the initial processing
                    return {}
                #
                def __init__(clsname, *args , **kwds):
                    super(CPPEnumType, clsname).__init__(*args)
                #
                def __new__(metacls, clsname, bases, clsdict, **kwds):
                    if CPPEnum is None:
                        # first time through, ignore the rest
                        enum_dict = super(CPPEnumType, metacls).__prepare__(clsname, bases, **kwds)
                        enum_dict.update(clsdict)
                        return super(CPPEnumType, metacls).__new__(metacls, clsname, bases, enum_dict, **kwds)
                    members = []
                    #
                    # remove _file and _name using `pop()` as they will cause problems in EnumMeta
                    try:
                        file = clsdict.pop('_file')
                    except KeyError:
                        raise TypeError('_file not specified')
                    cpp_enum_name = clsdict.pop('_name', clsname.lower())
                    with open(file) as fh:
                        file_contents = fh.read()
                    #
                    # syntax we don't want to see in the final parse tree
                    LBRACE, RBRACE, EQ, COMMA = map(Suppress, "{}=,")
                    _enum = Suppress("enum")
                    identifier = Word(alphas, alphanums + "_")
                    integer = Word(nums)
                    enumValue = Group(identifier("name") + Optional(EQ + integer("value")))
                    enumList = Group(enumValue + ZeroOrMore(COMMA + enumValue))
                    enum = _enum + identifier("enum") + LBRACE + enumList("names") + RBRACE
                    #
                    # find the cpp_enum_name ignoring other syntax and other enums
                    for item, start, stop in enum.scanString(file_contents):
                        if item.enum != cpp_enum_name:
                            continue
                        id = 0
                        for entry in item.names:
                            if entry.value != "":
                                id = int(entry.value)
                            members.append((entry.name.upper(), id))
                            id += 1
                    #
                    # get the real EnumDict
                    enum_dict = super(CPPEnumType, metacls).__prepare__(clsname, bases, **kwds)
                    # transfer the original dict content, names starting with '_' first
                    items = list(clsdict.items())
                    items.sort(key=lambda p: (0 if p[0][0] == '_' else 1, p))
                    for name, value in items:
                        enum_dict[name] = value
                    # add the members
                    for name, value in members:
                        enum_dict[name] = value
                    return super(CPPEnumType, metacls).__new__(metacls, clsname, bases, enum_dict, **kwds)
            #
            class CPPEnum(IntEnum, metaclass=CPPEnumType):
                pass
            #
            class Hello(CPPEnum):
                _file = os.path.join(tempdir, 'c_plus_plus.h')
            #
            class Blah(CPPEnum):
                _file = os.path.join(tempdir, 'c_plus_plus.h')
                _name = 'blah'
            #
            self.assertEqual(
                    list(Hello),
                    [Hello.ZERO, Hello.ONE, Hello.TWO, Hello.THREE, Hello.FIVE, Hello.SIX, Hello.TEN],
                    )
            self.assertEqual(Hello.ZERO.value, 0)
            self.assertEqual(Hello.THREE.value, 3)
            self.assertEqual(Hello.SIX.value, 6)
            self.assertEqual(Hello.TEN.value, 10)
            #
            self.assertEqual(
                    list(Blah),
                    [Blah.ALPHA, Blah.BETA, Blah.GAMMA, Blah.ZETA],
                    )
            self.assertEqual(Blah.ALPHA.value, 0)
            self.assertEqual(Blah.BETA.value, 1)
            self.assertEqual(Blah.GAMMA.value, 10)
            self.assertEqual(Blah.ZETA.value, 50)


if __name__ == '__main__':
    tempdir = tempfile.mkdtemp()
    try:
        unittest.main()
    finally:
        shutil.rmtree(tempdir, True)
