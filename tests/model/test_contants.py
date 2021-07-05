import unittest

from vspec.model.constants import VSSType, VSSDataType, Unit, StringStyle


class TestConstantsNode(unittest.TestCase):
    def test_string_styles(self):
        """
        Test correct parsing of string styles
        """

        self.assertEqual(StringStyle.NONE, StringStyle.from_str("none"))
        self.assertEqual(StringStyle.CAMEL_CASE, StringStyle.from_str("camelCase"))
        self.assertEqual(StringStyle.CAMEL_BACK, StringStyle.from_str("camelBack"))
        self.assertEqual(StringStyle.CAPITAL_CASE, StringStyle.from_str("capitalcase"))
        self.assertEqual(StringStyle.CONST_CASE, StringStyle.from_str("constcase"))
        self.assertEqual(StringStyle.LOWER_CASE, StringStyle.from_str("lowercase"))
        self.assertEqual(StringStyle.PASCAL_CASE, StringStyle.from_str("pascalcase"))
        self.assertEqual(StringStyle.SENTENCE_CASE, StringStyle.from_str("sentencecase"))
        self.assertEqual(StringStyle.SNAKE_CASE, StringStyle.from_str("snakecase"))
        self.assertEqual(StringStyle.TITLE_CASE, StringStyle.from_str("titlecase"))
        self.assertEqual(StringStyle.TRIM_CASE, StringStyle.from_str("trimcase"))
        self.assertEqual(StringStyle.UPPER_CASE, StringStyle.from_str("uppercase"))
        self.assertEqual(StringStyle.ALPHANUM_CASE, StringStyle.from_str("alphanumcase"))

    def test_invalid_string_styles(self):
        with self.assertRaises(Exception): StringStyle.from_str("not_a_valid_case")

    def test_units(self):
        """
        Test correct parsing of units
        """

        self.assertEqual(Unit.MILIMETER, Unit.from_str("mm"))
        self.assertEqual(Unit.CENTIMETER, Unit.from_str("cm"))
        self.assertEqual(Unit.METER, Unit.from_str("m"))
        self.assertEqual(Unit.KILOMETER, Unit.from_str("km"))
        self.assertEqual(Unit.KILOMETERPERHOUR, Unit.from_str("km/h"))
        self.assertEqual(Unit.METERSPERSECONDSQUARED, Unit.from_str("m/s^2"))
        self.assertEqual(Unit.LITER, Unit.from_str("l"))
        self.assertEqual(Unit.DEGREECELCIUS, Unit.from_str("celsius"))
        self.assertEqual(Unit.DEGREE, Unit.from_str("degrees"))
        self.assertEqual(Unit.DEGREEPERSECOND, Unit.from_str("degrees/s"))
        self.assertEqual(Unit.KILOWATT, Unit.from_str("kW"))
        self.assertEqual(Unit.KILOWATTHOURS, Unit.from_str("kWh"))
        self.assertEqual(Unit.KILOGRAMM, Unit.from_str("kg"))
        self.assertEqual(Unit.VOLT, Unit.from_str("V"))
        self.assertEqual(Unit.AMPERE, Unit.from_str("A"))
        self.assertEqual(Unit.SECOND, Unit.from_str("s"))
        self.assertEqual(Unit.MILLISECOND, Unit.from_str("ms"))
        self.assertEqual(Unit.MINUTE, Unit.from_str("min"))
        self.assertEqual(Unit.WEEKS, Unit.from_str("weeks"))
        self.assertEqual(Unit.MONTHS, Unit.from_str("months"))
        self.assertEqual(Unit.YEARS, Unit.from_str("years"))
        self.assertEqual(Unit.UNIXTIMESTAMP, Unit.from_str("UNIX Timestamp"))
        self.assertEqual(Unit.PASCAL, Unit.from_str("Pa"))
        self.assertEqual(Unit.KILOPASCAL, Unit.from_str("kPa"))
        self.assertEqual(Unit.PERCENT, Unit.from_str("percent"))
        self.assertEqual(Unit.CUBICMETER, Unit.from_str("cm^3"))
        self.assertEqual(Unit.HORSEPOWER, Unit.from_str("PS"))
        self.assertEqual(Unit.STARS, Unit.from_str("stars"))
        self.assertEqual(Unit.GRAMMPERSECOND, Unit.from_str("g/s"))
        self.assertEqual(Unit.GRAMMPERKM, Unit.from_str("g/km"))
        self.assertEqual(Unit.KILOWATTHOURSPER100KM, Unit.from_str("kWh/100km"))
        self.assertEqual(Unit.LITERPER100KM, Unit.from_str("l/100km"))
        self.assertEqual(Unit.LITERPERHOUR, Unit.from_str("l/h"))
        self.assertEqual(Unit.MILESPERGALLON, Unit.from_str("mpg"))
        self.assertEqual(Unit.POUND, Unit.from_str("lbs"))
        self.assertEqual(Unit.NEWTONMETER, Unit.from_str("Nm"))
        self.assertEqual(Unit.REVOLUTIONSPERMINUTE, Unit.from_str("rpm"))
        self.assertEqual(Unit.INCH, Unit.from_str("inch"))
        self.assertEqual(Unit.RATIO, Unit.from_str("ratio"))
        self.assertEqual(Unit.HERTZ, Unit.from_str("Hz"))
        self.assertEqual(Unit.LUX, Unit.from_str("lx"))
        self.assertEqual(Unit.MILLIBAR, Unit.from_str("mbar"))

    def test_invalid_unit(self):
        with self.assertRaises(Exception): Unit.from_str("not_a_valid_case")

    def test_vss_types(self):
        """
        Test correct parsing of VSS Types
        """

        self.assertEqual(VSSType.BRANCH, VSSType.from_str("branch"))
        self.assertEqual(VSSType.RBRANCH, VSSType.from_str("rbranch"))
        self.assertEqual(VSSType.ATTRIBUTE, VSSType.from_str("attribute"))
        self.assertEqual(VSSType.SENSOR, VSSType.from_str("sensor"))
        self.assertEqual(VSSType.ACTUATOR, VSSType.from_str("actuator"))
        self.assertEqual(VSSType.ELEMENT, VSSType.from_str("element"))

    def test_invalid_vss_types(self):
        with self.assertRaises(Exception): VSSType.from_str("not_a_valid_case")

    def test_vss_data_types(self):
        """
        Test correct parsing of VSS Data Types
        """

        self.assertEqual(VSSDataType.INT8, VSSDataType.from_str("int8"))
        self.assertEqual(VSSDataType.UINT8, VSSDataType.from_str("uint8"))
        self.assertEqual(VSSDataType.INT16, VSSDataType.from_str("int16"))
        self.assertEqual(VSSDataType.UINT16, VSSDataType.from_str("uint16"))
        self.assertEqual(VSSDataType.INT32, VSSDataType.from_str("int32"))
        self.assertEqual(VSSDataType.UINT32, VSSDataType.from_str("uint32"))
        self.assertEqual(VSSDataType.INT64, VSSDataType.from_str("int64"))
        self.assertEqual(VSSDataType.UINT64, VSSDataType.from_str("uint64"))
        self.assertEqual(VSSDataType.BOOLEAN, VSSDataType.from_str("boolean"))
        self.assertEqual(VSSDataType.FLOAT, VSSDataType.from_str("float"))
        self.assertEqual(VSSDataType.DOUBLE, VSSDataType.from_str("double"))
        self.assertEqual(VSSDataType.STRING, VSSDataType.from_str("string"))
        self.assertEqual(VSSDataType.UNIX_TIMESTAMP, VSSDataType.from_str("UNIX Timestamp"))

    def test_invalid_vss_data_types(self):
        with self.assertRaises(Exception): VSSDataType.from_str("not_a_valid_case")


if __name__ == '__main__':
    unittest.main()
