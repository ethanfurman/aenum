from aenum import Enum, IntEnum, UniqueEnum, NamedTuple, TupleSize, AutoNumber, NoAlias, Unique, MultiValue
from aenum import AutoNumberEnum, OrderedEnum, unique, skip, extend_enum

from collections import OrderedDict
from datetime import timedelta
from unittest import TestCase, main

class MagicAutoNumberEnum(Enum, settings=AutoNumber):
    pass

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
            class Color(Enum, settings=AutoNumber):
                red
                green
                blue
                def hello(self):
                    print('Hello!  My serial is %s.' % self.value)
                rose
        with self.assertRaises(NameError):
            class Color(Enum, settings=AutoNumber):
                red
                green
                blue
                def __init__(self, *args):
                    pass
                rose

    def test_magic(self):
        class Color(Enum, settings=AutoNumber):
            red, green, blue
        self.assertEqual(list(Color), [Color.red, Color.green, Color.blue])
        self.assertEqual(Color.red.value, 1)

    def test_magic_start(self):
        class Color(Enum, start=0):
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
        class Color(Enum, settings=(MultiValue, AutoNumber)):
            red
            green = 3, 'green'
            blue
        self.assertEqual(Color.red.value, 1)
        self.assertEqual(Color.green.value, 3)
        self.assertEqual(Color.blue.value, 4)
        self.assertIs(Color('green'), Color.green)
        self.assertIs(Color['green'], Color.green)

    def test_auto_and_init(self):
        class Field(IntEnum, settings=AutoNumber, init='__doc__'):
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
        self.assertEqual(Field.TYPE, 1)
        self.assertEqual(Field.START, 2)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')
        self.assertFalse(hasattr(Field, '_order_'))

    def test_auto_and_start(self):
        class Field(IntEnum, init='__doc__', start=0):
            TYPE = "Char, Date, Logical, etc."
            START = "Field offset in record"
        self.assertEqual(Field.TYPE, 0)
        self.assertEqual(Field.START, 1)
        self.assertEqual(Field.TYPE.__doc__, 'Char, Date, Logical, etc.')
        self.assertEqual(Field.START.__doc__, 'Field offset in record')

    def test_auto_and_init_and_some_values(self):
        class Field(IntEnum, init='__doc__', settings=AutoNumber):
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

    def test_auto_and_tuple(self):
        class Color(MagicAutoNumberEnum):
            red = ()
            green = ()
            blue = ()
        self.assertEqual(Color.blue.value, 3)

    def test_auto_and_property(self):
        with self.assertRaises(TypeError):
            class Color(MagicAutoNumberEnum):
                _ignore_ = ()
                red = ()
                green = ()
                blue = ()
                @property
                def cap_name(self) -> str:
                    return self.name.title()

    def test_auto_and_default_ignore(self):
        class Color(MagicAutoNumberEnum):
            red
            green
            blue
            @property
            def cap_name(self) -> str:
                return self.name.title()
        self.assertEqual(Color.blue.cap_name, 'Blue')

    def test_auto_and_overridden_ignore(self):
        with self.assertRaises(TypeError):
            class Color(MagicAutoNumberEnum):
                _ignore_ = 'staticmethod'
                red
                green
                blue
                @property
                def cap_name(self) -> str:
                    return self.name.title()

    def test_auto_and_multiple_assignment(self):
        class Color(MagicAutoNumberEnum):
            _ignore_ = 'property'
            red
            green
            blue = cyan
            @property
            def cap_name(self) -> str:
                return self.name.title()
        self.assertEqual(Color.blue.cap_name, 'Cyan')

    def test_combine_new_settings_with_old_settings(self):
        class Auto(Enum, settings=Unique):
            pass
        with self.assertRaises(ValueError):
            class AutoUnique(Auto, settings=AutoNumber):
                BLAH = ()
                BLUH = ()
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


if __name__ == '__main__':
    main()
