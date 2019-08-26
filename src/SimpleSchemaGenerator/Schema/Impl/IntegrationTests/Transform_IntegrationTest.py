# ----------------------------------------------------------------------
# |
# |  Transform_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-10 15:52:28
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Unit test for Transform.py"""

import os
import sys
import textwrap
import unittest

import six

import CommonEnvironment
from CommonEnvironment.Interface import *
from CommonEnvironment.TypeInfo import Arity
from CommonEnvironment.TypeInfo.All import *

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ...Elements import *
    from ...Parse import ParseStrings
    from ....Plugin import Plugin, ParseFlag

# ----------------------------------------------------------------------
SIMPLE_SCHEMA                               = textwrap.dedent(
    """\
    <test_base>:
        <a string *>

    <test_derived test_base>:
        <b bool>
        <c string min_length=12 *>

        <v1 (b|string|int min=20)>
        <v2 (bool|v1)>
        <v3 (uri|v2|filename ensure_exists=true)>

        <c_ref0 c>                                          # Plain reference
        <c_ref1 c max_length=20>                            # Reference with augmented metadata
        <c_ref2 c refines_arity=true {20}>                  # Reference updating arity
        <c_ref25 c max_length=20 refines_arity=true {20}>   # Reference with augmented metadata and updated arity
        <c_ref3 c {5}>                                      # List of strings
        <c_ref4 c_ref3 {10}>                                # List of list of strings

        <test_derived_ref1 test_derived>
        <test_derived_ref2 test_derived {10}>
        <test_derived_ref3 test_derived_ref2>
        <test_derived_ref4 test_derived_ref2 refines_arity=true {30}>
        <test_derived_ref5 test_derived_ref2 {20}>
    """,
)

# ----------------------------------------------------------------------
class InternalPlugin(Plugin):
    Name                                    = DerivedProperty("InternalPlugin")
    Description                             = DerivedProperty("")
    Flags                                   = DerivedProperty(
        # ParseFlag.SupportAttributes |
        ParseFlag.SupportIncludeStatements |                                                                                                                                                                         # ParseFlag.SupportConfigStatements |
                                                                                                                                                                                                                     # ParseFlag.SupportExtensionsStatements |
                                                                                                                                                                                                                     # ParseFlag.SupportUnnamedDeclarations |
                                                                                                                                                                                                                     # ParseFlag.SupportUnnamedObjects |
        ParseFlag.SupportNamedDeclarations | ParseFlag.SupportNamedObjects | ParseFlag.SupportRootDeclarations | ParseFlag.SupportRootObjects | ParseFlag.SupportChildDeclarations | ParseFlag.SupportChildObjects | # ParseFlag.SupportCustomElements |
                                                                                                                                                                                                                     # ParseFlag.SupportAnyElements |
        ParseFlag.SupportReferenceElements | ParseFlag.SupportListElements |                                                                                                                                         # ParseFlag.SupportSimpleObjectElements |
        ParseFlag.SupportVariantElements | ParseFlag.ResolveReferences,
    )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def GenerateCustomSettingsAndDefaults():
        if False:
            yield None

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def IsValidEnvironment():
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def GenerateOutputFilenames(context):
        if False:
            yield None

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def Generate(
        simple_schema_generator,
        invoke_reason,
        input_filenames,
        output_filenames,
        name,
        elements,
        include_indexes,
        status_stream,
        verbose_stream,
        verbose,
    ):
        self.elements = elements


# ----------------------------------------------------------------------
_elements                                   = ParseStrings(
    {"": SIMPLE_SCHEMA},
    InternalPlugin(),
    filter_unsupported_attributes=False,
    filter_unsupported_extensions=False,
)

# ----------------------------------------------------------------------
class TestBase(unittest.TestCase):

    # ----------------------------------------------------------------------
    def setUp(self):
        self.assertGreater(len(_elements), 0)
        self._element = _elements[0]

    # ----------------------------------------------------------------------
    def test_ElementInfo(self):
        self.assertTrue(isinstance(self._element, CompoundElement))
        self.assertEqual(self._element.Name, "test_base")
        self.assertEqual([child.Name for child in self._element.Children], ["a"])
        self.assertEqual(self._element.Base, None)
        self.assertEqual(
            set([other.Name for other in self._element.Derived]),
            set(["test_derived", "test_derived_ref2", "test_derived_ref4"]),
        )

        self.assertTrue(isinstance(self._element.Children[0], FundamentalElement))

    # ----------------------------------------------------------------------
    def test_TypeInfo(self):
        self.assertTrue(self._element.TypeInfo, ClassTypeInfo)
        self.assertEqual(self._element.TypeInfo.Arity, Arity(1, 1))
        self.assertEqual(
            self._element.TypeInfo,
            ClassTypeInfo(
                {
                    "a": StringTypeInfo(
                        arity="*",
                    ),
                },
                require_exact_match=True,
                arity=Arity(1, 1),
            ),
        )
        self.assertEqual(
            self._element.Children[0].TypeInfo,
            StringTypeInfo(
                arity="*",
            ),
        )


# ----------------------------------------------------------------------
class TestDerived(unittest.TestCase):

    # ----------------------------------------------------------------------
    def setUp(self):
        self.assertGreater(len(_elements), 1)
        self._element = _elements[1]

    # ----------------------------------------------------------------------
    def test_ElementInfo(self):
        self.assertTrue(isinstance(self._element, CompoundElement))
        self.assertEqual(self._element.Name, "test_derived")
        self.assertEqual(
            [child.Name for child in self._element.Children],
            [
                "b",
                "c",
                "v1",
                "v2",
                "v3",
                "c_ref0",
                "c_ref1",
                "c_ref2",
                "c_ref25",
                "c_ref3",
                "c_ref4",
                "test_derived_ref1",
                "test_derived_ref2",
                "test_derived_ref3",
                "test_derived_ref4",
                "test_derived_ref5",
            ],
        )
        self.assertEqual(self._element.Base.Name, "test_base")
        self.assertEqual(self._element.Derived, [])

    # ----------------------------------------------------------------------
    def test_TypeInfo(self):
        self._VerifyTestDerived(self._element.TypeInfo)
        self.assertEqual(self._element.TypeInfo.Arity, Arity(1, 1))

    # ----------------------------------------------------------------------
    def test_B(self):
        element = self._element.Children[0]
        self.assertEqual(element.Name, "b")
        self.assertTrue(isinstance(element, FundamentalElement))
        self.assertEqual(element.TypeInfo, BoolTypeInfo())

    # ----------------------------------------------------------------------
    def test_C(self):
        element = self._element.Children[1]
        self.assertEqual(element.Name, "c")
        self.assertTrue(isinstance(element, FundamentalElement))
        self.assertEqual(
            element.TypeInfo,
            StringTypeInfo(
                min_length=12,
                arity="*",
            ),
        )

    # ----------------------------------------------------------------------
    def test_V1(self):
        element = self._element.Children[2]
        self.assertEqual(element.Name, "v1")
        self.assertTrue(isinstance(element, VariantElement))
        self.assertEqual(
            element.TypeInfo,
            AnyOfTypeInfo(
                [
                    BoolTypeInfo(),
                    StringTypeInfo(),
                    IntTypeInfo(
                        min=20,
                    ),
                ],
            ),
        )

    # ----------------------------------------------------------------------
    def test_V2(self):
        element = self._element.Children[3]
        self.assertEqual(element.Name, "v2")
        self.assertTrue(isinstance(element, VariantElement))
        self.assertTrue(isinstance(element.Variations[1], ReferenceElement))
        self.assertEqual(
            element.TypeInfo,
            AnyOfTypeInfo(
                [
                    BoolTypeInfo(),
                    BoolTypeInfo(),
                    StringTypeInfo(),
                    IntTypeInfo(
                        min=20,
                    ),
                ],
            ),
        )

    # ----------------------------------------------------------------------
    def test_V3(self):
        element = self._element.Children[4]
        self.assertEqual(element.Name, "v3")
        self.assertTrue(isinstance(element, VariantElement))
        self.assertTrue(isinstance(element.Variations[1], ReferenceElement))
        self.assertEqual(
            element.TypeInfo,
            AnyOfTypeInfo(
                [
                    UriTypeInfo(),
                    BoolTypeInfo(),
                    BoolTypeInfo(),
                    StringTypeInfo(),
                    IntTypeInfo(
                        min=20,
                    ),
                    FilenameTypeInfo(
                        ensure_exists=True,
                    ),
                ],
            ),
        )

    # ----------------------------------------------------------------------
    def test_CRef0(self):
        element = self._element.Children[5]
        self.assertEqual(element.Name, "c_ref0")
        self.assertTrue(isinstance(element, ReferenceElement))
        self.assertEqual(
            element.TypeInfo,
            StringTypeInfo(
                min_length=12,
                arity="*",
            ),
        )

    # ----------------------------------------------------------------------
    def test_CRef1(self):
        element = self._element.Children[6]
        self.assertEqual(element.Name, "c_ref1")
        self.assertTrue(isinstance(element, FundamentalElement))
        self.assertEqual(
            element.TypeInfo,
            StringTypeInfo(
                min_length=12,
                max_length=20,
                arity="*",
            ),
        )

    # ----------------------------------------------------------------------
    def test_CRef2(self):
        element = self._element.Children[7]
        self.assertEqual(element.Name, "c_ref2")
        self.assertTrue(isinstance(element, FundamentalElement))
        self.assertEqual(
            element.TypeInfo,
            StringTypeInfo(
                min_length=12,
                arity=Arity(20, 20),
            ),
        )

    # ----------------------------------------------------------------------
    def test_CRef25(self):
        element = self._element.Children[8]
        self.assertEqual(element.Name, "c_ref25")
        self.assertTrue(isinstance(element, FundamentalElement))
        self.assertEqual(
            element.TypeInfo,
            StringTypeInfo(
                min_length=12,
                max_length=20,
                arity=Arity(20, 20),
            ),
        )

    # ----------------------------------------------------------------------
    def test_CRef3(self):
        element = self._element.Children[9]
        self.assertEqual(element.Name, "c_ref3")
        self.assertTrue(isinstance(element, ListElement))
        self.assertEqual(
            element.TypeInfo,
            ListTypeInfo(
                StringTypeInfo(
                    min_length=12,
                    arity="*",
                ),
                arity=Arity(5, 5),
            ),
        )

    # ----------------------------------------------------------------------
    def test_CRef4(self):
        element = self._element.Children[10]
        self.assertEqual(element.Name, "c_ref4")
        self.assertTrue(isinstance(element, ListElement))
        self.assertEqual(
            element.TypeInfo,
            ListTypeInfo(
                ListTypeInfo(
                    StringTypeInfo(
                        min_length=12,
                        arity="*",
                    ),
                    arity=Arity(5, 5),
                ),
                arity=Arity(10, 10),
            ),
        )

    # ----------------------------------------------------------------------
    def test_DerivedRef1(self):
        element = self._element.Children[11]
        self.assertEqual(element.Name, "test_derived_ref1")
        self._VerifyTestDerived(element.TypeInfo)
        self.assertEqual(element.TypeInfo.Arity, Arity(1, 1))

    # ----------------------------------------------------------------------
    def test_DerivedRef2(self):
        element = self._element.Children[12]
        self.assertEqual(element.Name, "test_derived_ref2")
        self._VerifyTestDerived(element.TypeInfo)
        self.assertEqual(element.TypeInfo.Arity, Arity(10, 10))

    # ----------------------------------------------------------------------
    def test_DerivedRef3(self):
        element = self._element.Children[13]
        self.assertEqual(element.Name, "test_derived_ref3")
        self._VerifyTestDerived(element.TypeInfo)
        self.assertEqual(element.TypeInfo.Arity, Arity(10, 10))

    # ----------------------------------------------------------------------
    def test_DerivedRef4(self):
        element = self._element.Children[14]
        self.assertEqual(element.Name, "test_derived_ref4")
        self._VerifyTestDerived(element.TypeInfo)
        self.assertEqual(element.TypeInfo.Arity, Arity(30, 30))

    # ----------------------------------------------------------------------
    def test_DerivedRef5(self):
        element = self._element.Children[15]
        self.assertEqual(element.Name, "test_derived_ref5")
        self.assertTrue(isinstance(element.TypeInfo, ListTypeInfo))
        self.assertEqual(element.TypeInfo.Arity, Arity(20, 20))
        self._VerifyTestDerived(element.TypeInfo.ElementTypeInfo)
        self.assertEqual(element.TypeInfo.ElementTypeInfo.Arity, Arity(10, 10))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _VerifyTestDerived(
        self,
        type_info,
        verify_derived_refs=True,
    ):
        self.assertTrue(isinstance(type_info, ClassTypeInfo))
        self.assertEqual(
            list(six.iterkeys(type_info.Items)),
            [
                "b",
                "c",
                "v1",
                "v2",
                "v3",
                "c_ref0",
                "c_ref1",
                "c_ref2",
                "c_ref25",
                "c_ref3",
                "c_ref4",
                "test_derived_ref1",
                "test_derived_ref2",
                "test_derived_ref3",
                "test_derived_ref4",
                "test_derived_ref5",
            ],
        )
        self.assertEqual(type_info.Items["b"], BoolTypeInfo())
        self.assertEqual(
            type_info.Items["c"],
            StringTypeInfo(
                min_length=12,
                arity="*",
            ),
        )
        self.assertEqual(
            type_info.Items["v1"],
            AnyOfTypeInfo(
                [
                    BoolTypeInfo(),
                    StringTypeInfo(),
                    IntTypeInfo(
                        min=20,
                    ),
                ],
            ),
        )
        self.assertEqual(
            type_info.Items["v2"],
            AnyOfTypeInfo(
                [
                    BoolTypeInfo(),
                    BoolTypeInfo(),
                    StringTypeInfo(),
                    IntTypeInfo(
                        min=20,
                    ),
                ],
            ),
        )
        self.assertEqual(
            type_info.Items["v3"],
            AnyOfTypeInfo(
                [
                    UriTypeInfo(),
                    BoolTypeInfo(),
                    BoolTypeInfo(),
                    StringTypeInfo(),
                    IntTypeInfo(
                        min=20,
                    ),
                    FilenameTypeInfo(
                        ensure_exists=True,
                    ),
                ],
            ),
        )
        self.assertEqual(
            type_info.Items["c_ref0"],
            StringTypeInfo(
                min_length=12,
                arity="*",
            ),
        )
        self.assertEqual(
            type_info.Items["c_ref1"],
            StringTypeInfo(
                min_length=12,
                max_length=20,
                arity="*",
            ),
        )
        self.assertEqual(
            type_info.Items["c_ref2"],
            StringTypeInfo(
                min_length=12,
                arity=Arity(20, 20),
            ),
        )
        self.assertEqual(
            type_info.Items["c_ref25"],
            StringTypeInfo(
                min_length=12,
                max_length=20,
                arity=Arity(20, 20),
            ),
        )
        self.assertEqual(
            type_info.Items["c_ref3"],
            ListTypeInfo(
                StringTypeInfo(
                    min_length=12,
                    arity="*",
                ),
                arity=Arity(5, 5),
            ),
        )
        self.assertEqual(
            type_info.Items["c_ref4"],
            ListTypeInfo(
                ListTypeInfo(
                    StringTypeInfo(
                        min_length=12,
                        arity="*",
                    ),
                    arity=Arity(5, 5),
                ),
                arity=Arity(10, 10),
            ),
        )

        self.assertTrue(isinstance(type_info.Items["test_derived_ref1"], ClassTypeInfo))
        self.assertTrue(isinstance(type_info.Items["test_derived_ref2"], ClassTypeInfo))
        self.assertTrue(isinstance(type_info.Items["test_derived_ref3"], ClassTypeInfo))
        self.assertTrue(isinstance(type_info.Items["test_derived_ref4"], ClassTypeInfo))
        self.assertTrue(isinstance(type_info.Items["test_derived_ref5"], ListTypeInfo))
        self.assertTrue(
            isinstance(type_info.Items["test_derived_ref5"].ElementTypeInfo, ClassTypeInfo),
        )

        if verify_derived_refs:
            self._VerifyTestDerived(
                type_info.Items["test_derived_ref1"],
                verify_derived_refs=False,
            )
            self._VerifyTestDerived(
                type_info.Items["test_derived_ref2"],
                verify_derived_refs=False,
            )
            self._VerifyTestDerived(
                type_info.Items["test_derived_ref3"],
                verify_derived_refs=False,
            )
            self._VerifyTestDerived(
                type_info.Items["test_derived_ref4"],
                verify_derived_refs=False,
            )
            self._VerifyTestDerived(
                type_info.Items["test_derived_ref5"].ElementTypeInfo,
                verify_derived_refs=False,
            )


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
