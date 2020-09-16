# ----------------------------------------------------------------------
# |
# |  SimpleSchemaVisitor_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-09-15 22:37:59
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for SimpleSchemaVisitor"""

import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

from CommonSimpleSchemaGenerator.TypeInfo.FundamentalTypes.Serialization.SimpleSchemaVisitor import *

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Standard(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_Types(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(BoolTypeInfo(), "foo", SimpleSchemaType.Standard), "<foo bool>")
        self.assertEqual(SimpleSchemaVisitor.Accept(BoolTypeInfo(), "foo", SimpleSchemaType.Attribute), "[foo bool]")
        self.assertEqual(SimpleSchemaVisitor.Accept(BoolTypeInfo(), "foo", SimpleSchemaType.Definition), "(foo bool)")

    # ----------------------------------------------------------------------
    def test_EmptyName(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(), None), "<int>")
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(min=20), None), "<int min=20 unsigned=True>")

    # ----------------------------------------------------------------------
    def test_Bool(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(BoolTypeInfo(), "foo"), "<foo bool>")

    # ----------------------------------------------------------------------
    def test_DateTime(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(DateTimeTypeInfo(), "foo"), "<foo datetime>")

    # ----------------------------------------------------------------------
    def test_Date(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(DateTypeInfo(), "foo"), "<foo date>")

    # ----------------------------------------------------------------------
    def test_Directory(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(DirectoryTypeInfo(), "foo"), "<foo directory>")
        self.assertEqual(SimpleSchemaVisitor.Accept(DirectoryTypeInfo(ensure_exists=True), "foo"), "<foo directory>")
        self.assertEqual(SimpleSchemaVisitor.Accept(DirectoryTypeInfo(ensure_exists=False), "foo"), "<foo directory ensure_exists=False>")
        self.assertEqual(SimpleSchemaVisitor.Accept(DirectoryTypeInfo(validation_expression="expr"), "foo"), '<foo directory validation_expression="expr">')
        self.assertEqual(SimpleSchemaVisitor.Accept(DirectoryTypeInfo(ensure_exists=False, validation_expression="expr"), "foo"), '<foo directory ensure_exists=False validation_expression="expr">')

    # ----------------------------------------------------------------------
    def test_Duration(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(DurationTypeInfo(), "foo"), "<foo duration>")

    # ----------------------------------------------------------------------
    def test_Enum(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(EnumTypeInfo(["one", "two", "three"]), "foo"), '<foo enum values=["one", "two", "three"]>')
        self.assertEqual(SimpleSchemaVisitor.Accept(EnumTypeInfo(["one", "two", "three"], friendly_values=["1", "2", "3"]), "foo"), '<foo enum values=["one", "two", "three"] friendly_values=["1", "2", "3"]>')

    # ----------------------------------------------------------------------
    def test_Filename(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(FilenameTypeInfo(), "foo"), "<foo filename>")
        self.assertEqual(SimpleSchemaVisitor.Accept(FilenameTypeInfo(ensure_exists=True), "foo"), "<foo filename>")
        self.assertEqual(SimpleSchemaVisitor.Accept(FilenameTypeInfo(ensure_exists=False), "foo"), "<foo filename ensure_exists=False>")
        self.assertEqual(SimpleSchemaVisitor.Accept(FilenameTypeInfo(match_any=True), "foo"), "<foo filename match_any=True>")
        self.assertEqual(SimpleSchemaVisitor.Accept(FilenameTypeInfo(validation_expression="expr"), "foo"), '<foo filename validation_expression="expr">')
        self.assertEqual(SimpleSchemaVisitor.Accept(FilenameTypeInfo(ensure_exists=False, validation_expression="expr"), "foo"), '<foo filename ensure_exists=False validation_expression="expr">')

    # ----------------------------------------------------------------------
    def test_Float(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(FloatTypeInfo(), "foo"), "<foo number>")
        self.assertEqual(SimpleSchemaVisitor.Accept(FloatTypeInfo(min=1.0), "foo"), "<foo number min=1.0>")
        self.assertEqual(SimpleSchemaVisitor.Accept(FloatTypeInfo(max=56.1234), "foo"), "<foo number max=56.1234>")
        self.assertEqual(SimpleSchemaVisitor.Accept(FloatTypeInfo(min=1, max=56.1234), "foo"), "<foo number min=1.0 max=56.1234>")

    # ----------------------------------------------------------------------
    def test_Guid(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(GuidTypeInfo(), "foo"), "<foo guid>")

    # ----------------------------------------------------------------------
    def test_Int(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(), "foo"), "<foo int>")
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(min=1), "foo"), "<foo int min=1 unsigned=True>")
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(min=-1), "foo"), "<foo int min=-1>")
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(max=23), "foo"), "<foo int max=23>")
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(bytes=2), "foo"), "<foo int min=-32768 max=32767 bytes=2>")
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(unsigned=False), "foo"), "<foo int>")
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(unsigned=True), "foo"), "<foo int min=0 unsigned=True>")
        self.assertEqual(SimpleSchemaVisitor.Accept(IntTypeInfo(min=1, max=23, bytes=4, unsigned=True), "foo"), "<foo int min=1 max=23 bytes=4 unsigned=True>")

    # ----------------------------------------------------------------------
    def test_String(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(StringTypeInfo(), "foo"), "<foo string min_length=1>")
        self.assertEqual(SimpleSchemaVisitor.Accept(StringTypeInfo(validation_expression="expr"), "foo"), '<foo string validation_expression="expr">')
        self.assertEqual(SimpleSchemaVisitor.Accept(StringTypeInfo(min_length=2), "foo"), "<foo string min_length=2>")
        self.assertEqual(SimpleSchemaVisitor.Accept(StringTypeInfo(max_length=40), "foo"), "<foo string min_length=1 max_length=40>")
        self.assertEqual(SimpleSchemaVisitor.Accept(StringTypeInfo(min_length=2, max_length=30), "foo"), '<foo string min_length=2 max_length=30>')

    # ----------------------------------------------------------------------
    def test_Time(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(TimeTypeInfo(), "foo"), "<foo time>")

    # ----------------------------------------------------------------------
    def test_Uri(self):
        self.assertEqual(SimpleSchemaVisitor.Accept(UriTypeInfo(), "foo"), "<foo uri>")


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            unittest.main(
                verbosity=2,
            ),
        )
    except KeyboardInterrupt:
        pass
