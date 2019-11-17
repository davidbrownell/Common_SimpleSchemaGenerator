# ----------------------------------------------------------------------
# |
# |  Populate_UnitTest.py
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
"""Unit test for Populate.py"""

import os
import sys
import textwrap
import unittest

import CommonEnvironment
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.TypeInfo import Arity

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..Populate import *
    from ... import Exceptions
    from ....Plugin import ParseFlag

# ----------------------------------------------------------------------
class StringSuite(unittest.TestCase):
    # The include statement is s simple way to test string

    # ----------------------------------------------------------------------
    def test_Quote(self):
        Populate({_script_fullpath: lambda: 'simple_schema_include("{}")'.format(_script_name)}, ParseFlag.AllFlags)

    # ----------------------------------------------------------------------
    def test_SingleQuote(self):
        Populate({_script_fullpath: lambda: "simple_schema_include('{}')".format(_script_name)}, ParseFlag.AllFlags)


# ----------------------------------------------------------------------
class EnhancedStringSuite(unittest.TestCase):
    # The config statement is a simple way to test enhanced strings

    # ----------------------------------------------------------------------
    def test_StandardTriple(self):
        content = _Invoke(
            textwrap.dedent(
                '''
                simple_schema_config("config_name"):
                    one = """
                          This is
                            a
                          multi-
                          line
                          test.
                          """
                ''',
            ),
        )
        self.assertTrue("config_name" in content.config)
        self.assertEqual(len(content.config["config_name"]), 1)
        self.assertTrue("one" in content.config["config_name"][0].Values)
        self.assertEqual(content.config["config_name"][0].Values["one"].Value, "This is\n  a\nmulti-\nline\ntest.")

    # ----------------------------------------------------------------------
    def test_StandardDouble(self):
        content = _Invoke(
            textwrap.dedent(
                """
                simple_schema_config("config_name"):
                    one = '''
                          This is
                            a
                          multi-
                          line
                          test.
                          '''
                """,
            ),
        )
        self.assertTrue("config_name" in content.config)
        self.assertEqual(len(content.config["config_name"]), 1)
        self.assertTrue("one" in content.config["config_name"][0].Values)
        self.assertEqual(content.config["config_name"][0].Values["one"].Value, "This is\n  a\nmulti-\nline\ntest.")

    # ----------------------------------------------------------------------
    def test_InvalidHeader(self):
        self.assertRaises(
            Exceptions.PopulateInvalidTripleStringHeaderException,
            lambda: _Invoke(
                textwrap.dedent(
                    """\
                    simple_schema_config("test"):
                        one = '''Must be an initial newline'''
                    """,
                ),
            ),
        )

    # ----------------------------------------------------------------------
    def test_InvalidFooter(self):
        self.assertRaises(
            Exceptions.PopulateInvalidTripleStringFooterException,
            lambda: _Invoke(
                textwrap.dedent(
                    """\
                    simple_schema_config("test"):
                        one = '''
                              Must be trailing newline'''
                    """,
                ),
            ),
        )

    # ----------------------------------------------------------------------
    def test_InvalidWhitespace(self):
        self.assertRaises(
            Exceptions.PopulateInvalidTripleStringPrefixException,
            lambda: _Invoke(
                textwrap.dedent(
                    """\
                    simple_schema_config("test"):
                        one = '''
                              Misaligned footer
                        '''
                    """,
                ),
            ),
        )

        self.assertRaises(
            Exceptions.PopulateInvalidTripleStringPrefixException,
            lambda: _Invoke(
                textwrap.dedent(
                    """\
                    simple_schema_config("test"):
                        one = '''
                              Misaligned
                            prefix
                              '''
                    """,
                ),
            ),
        )

    # ----------------------------------------------------------------------
    def test_Tabs(self):
        content = _Invoke(
            textwrap.dedent(
                """
                simple_schema_config("config_name"):
                    one = '''
                          Line 1
                  \t\tLine 2
                          '''
                """,
            ),
        )
        self.assertTrue("config_name" in content.config)
        self.assertEqual(len(content.config["config_name"]), 1)
        self.assertTrue("one" in content.config["config_name"][0].Values)
        self.assertEqual(content.config["config_name"][0].Values["one"].Value, "Line 1\nLine 2")

    # ----------------------------------------------------------------------
    def test_LineFeed(self):
        content = _Invoke(
            textwrap.dedent(
                """
                simple_schema_config("config_name"):
                    one = '''
                          Line 1
                    \r\n
                          Line 2
                          '''
                """,
            ),
        )
        self.assertTrue("config_name" in content.config)
        self.assertEqual(len(content.config["config_name"]), 1)
        self.assertTrue("one" in content.config["config_name"][0].Values)
        self.assertEqual(content.config["config_name"][0].Values["one"].Value, "Line 1\n\r\n\nLine 2")


# ----------------------------------------------------------------------
class StringListSuite(unittest.TestCase):
    # The config statement is a simple way to test enhanced strings

    # ----------------------------------------------------------------------
    def test_Standard(self):
        content = _Invoke(
            textwrap.dedent(
                """\
                simple_schema_config("test"):
                    one = [ 'a', 'b', 'c', ]
                """,
            ),
        )

        self.assertTrue("test" in content.config)
        self.assertEqual(len(content.config["test"]), 1)
        self.assertTrue("one" in content.config["test"][0].Values)
        self.assertEqual(content.config["test"][0].Values["one"].Value, ["a", "b", "c"])

        content = _Invoke(
            textwrap.dedent(
                """\
                simple_schema_config("test"):
                    one = [ "one", "two", "three", ]
                """,
            ),
        )

        self.assertTrue("test" in content.config)
        self.assertEqual(len(content.config["test"]), 1)
        self.assertTrue("one" in content.config["test"][0].Values)
        self.assertEqual(content.config["test"][0].Values["one"].Value, ["one", "two", "three"])


# ----------------------------------------------------------------------
class MetadataSuite(unittest.TestCase):
    # Use unnamed declarations to test metadata

    # ----------------------------------------------------------------------
    def test_None(self):
        item = _Invoke("<foo>").items[0]

        self.assertEqual(item.metadata.Values, {})

    # ----------------------------------------------------------------------
    def test_Single(self):
        item = _Invoke("<foo one='two'>").items[0]

        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")

    # ----------------------------------------------------------------------
    def test_Multiple(self):
        item = _Invoke("<foo one='two' three=4>").items[0]

        self.assertEqual(list(item.metadata.Values.keys()), ["one", "three"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.metadata.Values["three"].Value, 4)

    # ----------------------------------------------------------------------
    def test_FunkySpacing(self):
        item = _Invoke(
            textwrap.dedent(
                """\
                <foo     one='two'  three   =4
                    five=    6.5>
                """,
            ),
        ).items[0]

        self.assertEqual(list(item.metadata.Values.keys()), ["one", "three", "five"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.metadata.Values["three"].Value, 4)
        self.assertEqual(item.metadata.Values["five"].Value, 6.5)

    # ----------------------------------------------------------------------
    def test_DuplicateError(self):
        self.assertRaises(
            Exceptions.PopulateDuplicateMetadataException,
            lambda: _Invoke(
                textwrap.dedent(
                    """\
                    <foo one="two" one=3>
                    """,
                ),
            ),
        )


# ----------------------------------------------------------------------
class AritySuite(unittest.TestCase):
    # Use unnamed declarations to test metadata

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(_Invoke("<foo ?>").items[0].arity, Arity.FromString("?"))
        self.assertEqual(_Invoke("<foo *>").items[0].arity, Arity.FromString("*"))
        self.assertEqual(_Invoke("<foo +>").items[0].arity, Arity.FromString("+"))
        self.assertEqual(_Invoke("<foo {10}>").items[0].arity, Arity(10, 10))
        self.assertEqual(_Invoke("<foo {5, 20}>").items[0].arity, Arity(5, 20))

    # ----------------------------------------------------------------------
    def test_Errors(self):
        self.assertRaises(Exceptions.PopulateInvalidArityException, lambda: _Invoke("<foo {-10}>"))
        self.assertRaises(Exceptions.PopulateInvalidArityException, lambda: _Invoke("<foo {-10,10}>"))
        self.assertRaises(Exceptions.PopulateInvalidArityException, lambda: _Invoke("<foo {10,-10}>"))
        self.assertRaises(Exceptions.PopulateInvalidMaxArityException, lambda: _Invoke("<foo {10,5}>"))


# ----------------------------------------------------------------------
class IncludeSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_UnsupportedError(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedIncludeStatementsException,
            lambda: Populate({_script_fullpath: lambda: "simple_schema_include('{}')".format(_script_name)}, 0),
        )

    # ----------------------------------------------------------------------
    def test_InvalidError(self):
        self.assertRaises(
            Exceptions.PopulateInvalidIncludeFilenameException,
            lambda: Populate({_script_fullpath: lambda: "simple_schema_include('Does not exist')"}, ParseFlag.AllFlags),
        )

    # ----------------------------------------------------------------------
    def test_Invoke(self):
        include_filename = CurrentShell.CreateTempFilename(".SimpleSchema")

        with open(include_filename, "w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    <a_string string>
                    """,
                ),
            )

        with CallOnExit(lambda: os.remove(include_filename)):
            root = _Invoke("simple_schema_include('{}')".format(include_filename))

        self.assertEqual(len(root.items), 1)

        item = root.items[0]

        self.assertEqual(item.name, "a_string")

    # ----------------------------------------------------------------------
    def test_InvokeRecursive(self):
        include_filename1 = CurrentShell.CreateTempFilename(".SimpleSchema")
        include_filename2 = CurrentShell.CreateTempFilename(".SimpleSchema")

        with open(include_filename1, "w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    simple_schema_include('{}')

                    <a_string1 string>
                    """,
                ).format(include_filename2),
            )

        with CallOnExit(lambda: os.remove(include_filename1)):
            with open(include_filename2, "w") as f:
                f.write(
                    textwrap.dedent(
                        """\
                        <a_string2 string>
                        """,
                    ),
                )

            with CallOnExit(lambda: os.remove(include_filename2)):
                root = _Invoke("simple_schema_include('{}')".format(include_filename1))

        self.assertEqual(len(root.items), 2)
        self.assertEqual(root.items[0].name, "a_string1")
        self.assertEqual(root.items[1].name, "a_string2")


# ----------------------------------------------------------------------
class ConfigSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_UnsupportedError(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedConfigStatementsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        simple_schema_config("AConfiguration"):
                            one = 'two'
                            three = '4'
                        """,
                    ),
                },
                0,
            ),
        )

    # ----------------------------------------------------------------------
    def test_Invoke(self):
        root = _Invoke(
            textwrap.dedent(
                """\
                simple_schema_config("test"):
                    one = "two"
                    three = 4
                """,
            ),
        )

        self.assertEqual(list(root.config.keys()), ["test"])
        self.assertEqual(list(root.config["test"][0].Values.keys()), ["one", "three"])
        self.assertEqual(root.config["test"][0].Values["one"].Value, "two")
        self.assertEqual(root.config["test"][0].Values["three"].Value, 4)

    # ----------------------------------------------------------------------
    def test_InvokeMultiple(self):
        root = _Invoke(
            textwrap.dedent(
                """\
                simple_schema_config("test"):
                    one = "two"
                    three = 4

                simple_schema_config("another"):
                    five = 6.0

                """,
            ),
        )

        self.assertEqual(list(root.config.keys()), ["test", "another"])

        self.assertEqual(list(root.config["test"][0].Values.keys()), ["one", "three"])
        self.assertEqual(root.config["test"][0].Values["one"].Value, "two")
        self.assertEqual(root.config["test"][0].Values["three"].Value, 4)

        self.assertEqual(list(root.config["another"][0].Values.keys()), ["five"])
        self.assertEqual(root.config["another"][0].Values["five"].Value, 6.0)


# ----------------------------------------------------------------------
class UnnamedObjSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_UnsupportedError(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedUnnamedObjectsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <>: pass
                        """,
                    ),
                },
                0,
            ),
        )

    # ----------------------------------------------------------------------
    def test_UnsupportedRootError(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedRootObjectsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <>: pass
                        """,
                    ),
                },
                ParseFlag.SupportUnnamedObjects,
            ),
        )

    # ----------------------------------------------------------------------
    def test_UnsupportedChildError(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedChildObjectsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <>:
                            <>:
                                pass
                        """,
                    ),
                },
                ParseFlag.SupportUnnamedObjects | ParseFlag.SupportRootObjects,
            ),
        )

    # ----------------------------------------------------------------------
    def test_Standard(self):
        root = _Invoke(
            textwrap.dedent(
                """\
                <>:
                    <>: pass
                    <>: pass
                """,
            ),
        )

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, None)
        self.assertEqual(len(root.items[0].items), 2)
        self.assertEqual(root.items[0].items[0].name, None)
        self.assertEqual(root.items[0].items[1].name, None)
        self.assertEqual(len(root.items[0].items[0].items), 0)
        self.assertEqual(len(root.items[0].items[1].items), 0)

    # ----------------------------------------------------------------------
    def test_Attributes(self):
        root = _Invoke("<one='two' ?>: pass")

        self.assertEqual(len(root.items), 1)

        item = root.items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.arity, Arity.FromString("?"))

    # ----------------------------------------------------------------------
    def test_Format(self):
        # ----------------------------------------------------------------------
        def Verify(root):
            self.assertEqual(len(root.items), 2)

            item = root.items[0]
            self.assertEqual(item.name, None)
            self.assertEqual(list(item.metadata.Values.keys()), ["one"])
            self.assertEqual(item.metadata.Values["one"].Value, "two")
            self.assertEqual(len(item.items), 0)

            item = root.items[1]
            self.assertEqual(item.name, None)
            self.assertEqual(list(item.metadata.Values.keys()), ["one", "three"])
            self.assertEqual(item.metadata.Values["one"].Value, "two")
            self.assertEqual(item.metadata.Values["three"].Value, "four")
            self.assertEqual(len(item.items), 0)

        # ----------------------------------------------------------------------

        # Standard
        Verify(
            _Invoke(
                textwrap.dedent(
                    """\
                    <one="two">:
                        pass

                    <one='two' three="four">:
                        pass
                    """,
                ),
            ),
        )

        # No sep
        Verify(
            _Invoke(
                textwrap.dedent(
                    """\
                    <one="two">:
                        pass
                    <one='two' three="four">:
                        pass
                    """,
                ),
            ),
        )

        # Wonky spacing
        Verify(
            _Invoke(
                textwrap.dedent(
                    """\
                    <one="two">:


                        pass

                    <one='two' three="four">:
                        pass




                    """,
                ),
            ),
        )

        # Inline
        Verify(
            _Invoke(
                textwrap.dedent(
                    """\
                    <one="two">: pass
                    <one='two' three="four">: pass
                    """,
                ),
            ),
        )

    # ----------------------------------------------------------------------
    def test_OnlyArity(self):
        content = _Invoke(
            textwrap.dedent(
                """\
                <?>: pass
                """,
            ),
        )

        self.assertEqual(len(content.items), 1)
        self.assertEqual(content.items[0].name, None)
        self.assertEqual(content.items[0].arity, Arity.FromString("?"))


# ----------------------------------------------------------------------
class NamedObjSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_UnsupportedError(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedNamedObjectsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <foo>: pass
                        """,
                    ),
                },
                0,
            ),
        )

    # ----------------------------------------------------------------------
    def test_UnsupportedRootError(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedRootObjectsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <foo>: pass
                        """,
                    ),
                },
                ParseFlag.SupportNamedObjects,
            ),
        )

    # ----------------------------------------------------------------------
    def test_UnsupportedChildError(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedChildObjectsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <foo>:
                            <bar>:
                                pass
                        """,
                    ),
                },
                ParseFlag.SupportNamedObjects | ParseFlag.SupportRootObjects,
            ),
        )

    # ----------------------------------------------------------------------
    def test_Standard(self):
        root = _Invoke(
            textwrap.dedent(
                """\
                <foo>:
                    <bar>: pass
                    <baz>: pass
                """,
            ),
        )

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "foo")
        self.assertEqual(root.items[0].references, [])
        self.assertEqual(len(root.items[0].items), 2)
        self.assertEqual(root.items[0].items[0].name, "bar")
        self.assertEqual(root.items[0].items[0].references, [])
        self.assertEqual(root.items[0].items[1].name, "baz")
        self.assertEqual(root.items[0].items[1].references, [])
        self.assertEqual(len(root.items[0].items[0].items), 0)
        self.assertEqual(len(root.items[0].items[1].items), 0)

    # ----------------------------------------------------------------------
    def test_Metadata(self):
        item = _Invoke("<foo one='two'>: pass").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.references, [])
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_Arity(self):
        item = _Invoke("<foo ?>: pass").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.references, [])
        self.assertEqual(item.metadata.Values, {})
        self.assertEqual(item.arity, Arity.FromString("?"))

    # ----------------------------------------------------------------------
    def test_MetadataAndArity(self):
        item = _Invoke("<foo one='two' ?>: pass").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.references, [])
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.arity, Arity.FromString("?"))

    # ----------------------------------------------------------------------
    def test_Format(self):
        # ----------------------------------------------------------------------
        def Verify(root):
            self.assertEqual(len(root.items), 2)

            item = root.items[0]
            self.assertEqual(item.name, "foo")
            self.assertEqual(item.references, [])
            self.assertEqual(list(item.metadata.Values.keys()), ["one"])
            self.assertEqual(item.metadata.Values["one"].Value, "two")
            self.assertEqual(len(item.items), 0)

            item = root.items[1]
            self.assertEqual(item.name, "bar")
            self.assertEqual(item.references, [])
            self.assertEqual(list(item.metadata.Values.keys()), ["one", "three"])
            self.assertEqual(item.metadata.Values["one"].Value, "two")
            self.assertEqual(item.metadata.Values["three"].Value, "four")
            self.assertEqual(len(item.items), 0)

        # ----------------------------------------------------------------------

        # Standard
        Verify(
            _Invoke(
                textwrap.dedent(
                    """\
                    <foo one="two">:
                        pass

                    <bar one='two' three="four">:
                        pass
                    """,
                ),
            ),
        )

        # No sep
        Verify(
            _Invoke(
                textwrap.dedent(
                    """\
                    <foo one="two">:
                        pass
                    <bar one='two' three="four">:
                        pass
                    """,
                ),
            ),
        )

        # Wonky spacing
        Verify(
            _Invoke(
                textwrap.dedent(
                    """\
                    <foo one="two">:


                        pass

                    <bar one='two' three="four">:
                        pass




                    """,
                ),
            ),
        )

        # Inline
        Verify(
            _Invoke(
                textwrap.dedent(
                    """\
                    <foo one="two">: pass
                    <bar one='two' three="four">: pass
                    """,
                ),
            ),
        )

    # ----------------------------------------------------------------------
    def test_Reference(self):
        root = _Invoke(
            textwrap.dedent(
                """\
                <foo bar>: pass
                <baz biz one="two">: pass
                """,
            ),
        )

        self.assertEqual(len(root.items), 2)

        item = root.items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.references, ["bar"])
        self.assertEqual(len(item.items), 0)

        item = root.items[1]

        self.assertEqual(item.name, "baz")
        self.assertEqual(item.references, ["biz"])
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")


# ----------------------------------------------------------------------
class UnnamedDeclarationSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        item = _Invoke("<string>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.references, ["string"])
        self.assertFalse(item.metadata.Values)
        self.assertFalse(item.arity)

    # ----------------------------------------------------------------------
    def test_Metadata(self):
        item = _Invoke("<string one='two'>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.references, ["string"])
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertFalse(item.arity)

    # ----------------------------------------------------------------------
    def test_Arity(self):
        item = _Invoke("<string ?>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.references, ["string"])
        self.assertEqual(item.metadata.Values, {})
        self.assertEqual(item.arity, Arity.FromString("?"))

    # ----------------------------------------------------------------------
    def test_MetadataAndArity(self):
        item = _Invoke("<string one='two' ?>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.references, ["string"])
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.arity, Arity.FromString("?"))

    # ----------------------------------------------------------------------
    def test_Variant(self):
        item = _Invoke("<(a|b|c)>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual([name for name, _ in item.references], ["a", "b", "c"])
        self.assertEqual(item.metadata.Values, {})
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_VariantGlobalMetadata(self):
        item = _Invoke("<(a|b|c) one='two'>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual([name for name, _ in item.references], ["a", "b", "c"])
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_VariantItemMetadata(self):
        item = _Invoke("<(a|b inner=2.0|c) one='two'>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual([name for name, _ in item.references], ["a", "b", "c"])
        self.assertEqual(item.references[0][1].Values, {})
        self.assertEqual(list(item.references[1][1].Values.keys()), ["inner"])
        self.assertEqual(item.references[1][1].Values["inner"].Value, 2.0)
        self.assertEqual(item.references[2][1].Values, {})
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_Unsupported(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedUnnamedDeclarationsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <string>
                        """,
                    ),
                },
                0,
            ),
        )

    # ----------------------------------------------------------------------
    def test_UnsupportedRoot(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedRootDeclarationsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <string>
                        """,
                    ),
                },
                ParseFlag.SupportUnnamedDeclarations,
            ),
        )

    # ----------------------------------------------------------------------
    def test_UnsupportedChild(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedChildDeclarationsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <object>:
                            <string>
                        """,
                    ),
                },
                ParseFlag.SupportUnnamedDeclarations | ParseFlag.SupportNamedObjects | ParseFlag.SupportRootObjects,
            ),
        )


# ----------------------------------------------------------------------
class NamedDeclarationSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        item = _Invoke("<foo string>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.references, ["string"])
        self.assertFalse(item.metadata.Values)
        self.assertFalse(item.arity)

    # ----------------------------------------------------------------------
    def test_Metadata(self):
        item = _Invoke("<foo string one='two'>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.references, ["string"])
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertFalse(item.arity)

    # ----------------------------------------------------------------------
    def test_Arity(self):
        item = _Invoke("<foo string ?>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.references, ["string"])
        self.assertEqual(item.metadata.Values, {})
        self.assertEqual(item.arity, Arity.FromString("?"))

    # ----------------------------------------------------------------------
    def test_MetadataAndArity(self):
        item = _Invoke("<foo string one='two' ?>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.references, ["string"])
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.arity, Arity.FromString("?"))

    # ----------------------------------------------------------------------
    def test_Variant(self):
        item = _Invoke("<(a|b|c)>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual([name for name, _ in item.references], ["a", "b", "c"])
        self.assertEqual(item.metadata.Values, {})
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_VariantGlobalMetadata(self):
        item = _Invoke("<foo (a|b|c) one='two'>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual([name for name, _ in item.references], ["a", "b", "c"])
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_VariantItemMetadata(self):
        item = _Invoke("<foo (a|b inner=2.0|c) one='two'>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual([name for name, _ in item.references], ["a", "b", "c"])
        self.assertEqual(item.references[0][1].Values, {})
        self.assertEqual(list(item.references[1][1].Values.keys()), ["inner"])
        self.assertEqual(item.references[1][1].Values["inner"].Value, 2.0)
        self.assertEqual(item.references[2][1].Values, {})
        self.assertEqual(list(item.metadata.Values.keys()), ["one"])
        self.assertEqual(item.metadata.Values["one"].Value, "two")
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_Unsupported(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedNamedDeclarationsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <a string>
                        """,
                    ),
                },
                0,
            ),
        )

    # ----------------------------------------------------------------------
    def test_UnsupportedRoot(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedRootDeclarationsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <a string>
                        """,
                    ),
                },
                ParseFlag.SupportNamedDeclarations,
            ),
        )

    # ----------------------------------------------------------------------
    def test_UnsupportedChild(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedChildDeclarationsException,
            lambda: Populate(
                {
                    _script_fullpath: lambda: textwrap.dedent(
                        """\
                        <object>:
                            <a string>
                        """,
                    ),
                },
                ParseFlag.SupportNamedDeclarations | ParseFlag.SupportNamedObjects | ParseFlag.SupportRootObjects,
            ),
        )


# ----------------------------------------------------------------------
class ExtensionSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Positional(self):
        content = _Invoke(
            textwrap.dedent(
                """\
                an_extension(1, 2, 3)
                """,
            ),
        )
        self.assertEqual(len(content.items), 1)
        self.assertEqual(content.items[0].name, "an_extension")
        self.assertEqual(content.items[0].positional_arguments, [1, 2, 3])
        self.assertTrue(not content.items[0].keyword_arguments)
        self.assertTrue(not content.items[0].arity)

    # ----------------------------------------------------------------------
    def test_Keywords(self):
        content = _Invoke(
            textwrap.dedent(
                """\
                an_extension(one=1, two=2, three=3)
                """,
            ),
        )
        self.assertEqual(len(content.items), 1)
        self.assertEqual(content.items[0].name, "an_extension")
        self.assertTrue(not content.items[0].positional_arguments)
        self.assertEqual(content.items[0].keyword_arguments, {"one": 1, "two": 2, "three": 3})
        self.assertTrue(not content.items[0].arity)

    # ----------------------------------------------------------------------
    def test_PositionalAndKeywords(self):
        content = _Invoke(
            textwrap.dedent(
                """\
                an_extension(1, 2, three=3, four=4)
                """,
            ),
        )
        self.assertEqual(len(content.items), 1)
        self.assertEqual(content.items[0].name, "an_extension")
        self.assertEqual(content.items[0].positional_arguments, [1, 2])
        self.assertEqual(content.items[0].keyword_arguments, {"three": 3, "four": 4})
        self.assertTrue(not content.items[0].arity)

    # ----------------------------------------------------------------------
    def test_WithArity(self):
        content = _Invoke(
            textwrap.dedent(
                """\
                an_extension(1, 2, three=3, four=4)?
                """,
            ),
        )
        self.assertEqual(len(content.items), 1)
        self.assertEqual(content.items[0].name, "an_extension")
        self.assertEqual(content.items[0].positional_arguments, [1, 2])
        self.assertEqual(content.items[0].keyword_arguments, {"three": 3, "four": 4})
        self.assertEqual(content.items[0].arity, Arity.FromString("?"))

    # ----------------------------------------------------------------------
    def test_Unsupported(self):
        self.assertRaises(
            Exceptions.PopulateUnsupportedExtensionStatementException,
            lambda: _Invoke(
                textwrap.dedent(
                    """\
                    an_extension(1, 2)
                    """,
                ),
                0,
            ),
        )

    # ----------------------------------------------------------------------
    def test_DuplicateKeyword(self):
        self.assertRaises(
            Exceptions.PopulateDuplicateKeywordArgumentException,
            lambda: _Invoke(
                textwrap.dedent(
                    """\
                    an_extension(one=1, one=2)
                    """,
                ),
            ),
        )


# ----------------------------------------------------------------------
class MiscSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Attributes(self):
        content = _Invoke(
            textwrap.dedent(
                """\
                <obj>:
                    [a string]
                """,
            ),
        )

        self.assertEqual(len(content.items), 1)
        self.assertEqual(len(content.items[0].items), 1)
        self.assertEqual(content.items[0].items[0].name, "a")
        self.assertEqual(content.items[0].items[0].ItemType, Item.ItemType.Attribute)

    # ----------------------------------------------------------------------
    def test_Definitions(self):
        content = _Invoke(
            textwrap.dedent(
                """\
                <obj>:
                    (a string)
                """,
            ),
        )

        self.assertEqual(len(content.items), 1)
        self.assertEqual(len(content.items[0].items), 1)
        self.assertEqual(content.items[0].items[0].name, "a")
        self.assertEqual(content.items[0].items[0].ItemType, Item.ItemType.Definition)

    # ----------------------------------------------------------------------
    def test_InvalidName(self):
        self.assertRaises(
            Exceptions.PopulateReservedNameException,
            lambda: _Invoke(
                textwrap.dedent(
                    """\
                    <string string>
                    """,
                ),
            ),
        )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Invoke(
    content,
    parse_flags=ParseFlag.AllFlags,
):
    return Populate({"content": lambda: content}, parse_flags)


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
