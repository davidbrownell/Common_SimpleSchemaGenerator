# ----------------------------------------------------------------------
# |  
# |  Populate_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-10 15:52:28
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for Populate.py"""

import os
import sys
import textwrap
import unittest

from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.TypeInfo import Arity

from CommonEnvironmentEx.Package import ApplyRelativePackage

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with ApplyRelativePackage():
    # TODO from .. import Populate
    from ..Populate import *
    from ...Exceptions import *
    from ....Plugin import ParseFlag

# ----------------------------------------------------------------------
class StringSuite(unittest.TestCase):
    # The include statement is s simple way to test string
    
    # ----------------------------------------------------------------------
    def test_Quote(self):
        Populate( { _script_fullpath : lambda: 'simple_schema_include("{}")'.format(_script_name), },
                  ParseFlag.AllFlags,
                )

    # ----------------------------------------------------------------------
    def test_SingleQuote(self):    
        Populate( { _script_fullpath : lambda: "simple_schema_include('{}')".format(_script_name), },
                  ParseFlag.AllFlags,
                )

# ----------------------------------------------------------------------
class EnhancedStringSuite(unittest.TestCase):
    pass # BugBug: Neext extension to test

# ----------------------------------------------------------------------
class StringListSuite(unittest.TestCase):
    pass # BugBug: Need metadata to test

# ----------------------------------------------------------------------
class ArgSuite(unittest.TestCase):
    pass # BugBug

# ----------------------------------------------------------------------
class ArgListSuite(unittest.TestCase):
    pass # BugBug: Need extension to test

# ----------------------------------------------------------------------
class MetadataSuite(unittest.TestCase):
    # Use unnamed declarations to test metadata

    # ----------------------------------------------------------------------
    def test_None(self):
        item = _Invoke("<foo>").items[0]

        self.assertEqual(item.metadata, {})

    # ----------------------------------------------------------------------
    def test_Single(self):
        item = _Invoke("<foo one='two'>").items[0]

        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")

    # ----------------------------------------------------------------------
    def test_Multiple(self):
        item = _Invoke("<foo one='two' three=4>").items[0]

        self.assertEqual(list(item.metadata.keys()), [ "one", "three", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.metadata["three"].Value, 4)

    # ----------------------------------------------------------------------
    def test_FunkySpacing(self):
        item = _Invoke(textwrap.dedent(
                        """\
                        <foo     one='two'  three   =4   
                            five=    6.5>
                        """)).items[0]

        self.assertEqual(list(item.metadata.keys()), [ "one", "three", "five", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.metadata["three"].Value, 4)
        self.assertEqual(item.metadata["five"].Value, 6.5)

# ----------------------------------------------------------------------
class AritySuite(unittest.TestCase):
    # Use unnamed declarations to test metadata

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(_Invoke("<foo ?>").items[0].arity, Arity.FromString('?'))
        self.assertEqual(_Invoke("<foo *>").items[0].arity, Arity.FromString('*'))
        self.assertEqual(_Invoke("<foo +>").items[0].arity, Arity.FromString('+'))
        self.assertEqual(_Invoke("<foo {10}>").items[0].arity, Arity(10, None))
        self.assertEqual(_Invoke("<foo {5, 20}>").items[0].arity, Arity(5, 20))

    # ----------------------------------------------------------------------
    def test_Errors(self):
        self.assertRaises(PopulateInvalidArityException, lambda: _Invoke("<foo {-10}>"))
        self.assertRaises(PopulateInvalidArityException, lambda: _Invoke("<foo {10,-10}>"))
        self.assertRaises(PopulateInvalidMaxArityException, lambda: _Invoke("<foo {10,5}>"))

# ----------------------------------------------------------------------
class IncludeSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_UnsupportedError(self):
        self.assertRaises(PopulateUnsupportedIncludeStatementsException, lambda: Populate( { _script_fullpath : lambda: "simple_schema_include('{}')".format(_script_name), },
                                                                                           0,
                                                                                         ))

    # ----------------------------------------------------------------------
    def test_InvalidError(self):
        self.assertRaises(PopulateInvalidIncludeFilenameException, lambda: Populate( { _script_fullpath : lambda: "simple_schema_include('Does not exist')", },
                                                                                     ParseFlag.AllFlags,
                                                                                   ))

    # ----------------------------------------------------------------------
    def test_Invoke(self):
        include_filename = CurrentShell.CreateTempFilename(".SimpleSchema")

        with open(include_filename, 'w') as f:
            f.write(textwrap.dedent(
                """\
                <a_string string>
                """))

        with CallOnExit(lambda: os.remove(include_filename)):
            root = _Invoke("simple_schema_include('{}')".format(include_filename))

        self.assertEqual(len(root.items), 1)
        
        item = root.items[0]

        self.assertEqual(item.name, "a_string")
        
    # ----------------------------------------------------------------------
    def test_InvokeRecursive(self):
        include_filename1 = CurrentShell.CreateTempFilename(".SimpleSchema")
        include_filename2 = CurrentShell.CreateTempFilename(".SimpleSchema")

        with open(include_filename1, 'w') as f:
            f.write(textwrap.dedent(
                """\
                simple_schema_include('{}')

                <a_string1 string>
                """).format(include_filename2))

        with CallOnExit(lambda: os.remove(include_filename1)):
            with open(include_filename2, 'w') as f:
                f.write(textwrap.dedent(
                    """\
                    <a_string2 string>
                    """))

            with CallOnExit(lambda: os.remove(include_filename2)):
                root = _Invoke("simple_schema_include('{}')".format(include_filename1))

        self.assertEqual(len(root.items), 2)
        self.assertEqual(root.items[0].name, "a_string1")
        self.assertEqual(root.items[1].name, "a_string2")
        
# ----------------------------------------------------------------------
class ConfigSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_UnsupportedError(self):
        self.assertRaises(PopulateUnsupportedConfigStatementsException, lambda: Populate( { _script_fullpath : lambda: textwrap.dedent(
                                                                                                                            """\
                                                                                                                            simple_schema_config("AConfiguration"):
                                                                                                                                one = 'two' 
                                                                                                                                three = '4'
                                                                                                                            """), },
                                                                                          0,
                                                                                        ))

    # ----------------------------------------------------------------------
    def test_DuplicateError(self):
        self.assertRaises(PopulateDuplicateConfigException, lambda: _Invoke(textwrap.dedent(
                                                                                """\
                                                                                simple_schema_config("test"):
                                                                                    one = "two"

                                                                                simple_schema_config("test"):
                                                                                    three = 4
                                                                                """)))

    # ----------------------------------------------------------------------
    def test_Invoke(self):
        root = _Invoke(textwrap.dedent(
                    """\
                    simple_schema_config("test"):
                        one = "two"
                        three = 4
                    """))

        self.assertEqual(list(root.config.keys()), [ "test", ])
        self.assertEqual(list(root.config["test"].Values.keys()), [ "one", "three", ])
        self.assertEqual(root.config["test"].Values["one"].Value, "two")
        self.assertEqual(root.config["test"].Values["three"].Value, 4)
        
    # ----------------------------------------------------------------------
    def test_InvokeMultiple(self):
        root = _Invoke(textwrap.dedent(
                    """\
                    simple_schema_config("test"):
                        one = "two"
                        three = 4

                    simple_schema_config("another"):
                        five = 6.0

                    """))

        self.assertEqual(list(root.config.keys()), [ "test", "another", ])

        self.assertEqual(list(root.config["test"].Values.keys()), [ "one", "three", ])
        self.assertEqual(root.config["test"].Values["one"].Value, "two")
        self.assertEqual(root.config["test"].Values["three"].Value, 4)

        self.assertEqual(list(root.config["another"].Values.keys()), [ "five", ])
        self.assertEqual(root.config["another"].Values["five"].Value, 6.0)

# ----------------------------------------------------------------------
class UnnamedObjSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_UnsupportedError(self):
        self.assertRaises(PopulateUnsupportedUnnamedObjectsException, lambda: Populate( { _script_fullpath: lambda: textwrap.dedent(
                                                                                                                        """\
                                                                                                                        <>: pass
                                                                                                                        """), },
                                                                                        0,
                                                                                      ))

    # ----------------------------------------------------------------------
    def test_UnsupportedRootError(self):
        self.assertRaises(PopulateUnsupportedRootObjectsException, lambda: Populate( { _script_fullpath: lambda: textwrap.dedent(
                                                                                                                        """\
                                                                                                                        <>: pass
                                                                                                                        """), },
                                                                                     ParseFlag.SupportUnnamedObjects,
                                                                                   ))

    # ----------------------------------------------------------------------
    def test_UnsupportedChildError(self):
        self.assertRaises(PopulateUnsupportedChildObjectsException, lambda: Populate( { _script_fullpath: lambda: textwrap.dedent(
                                                                                                                        """\
                                                                                                                        <>:
                                                                                                                            <>: 
                                                                                                                                pass
                                                                                                                        """), },
                                                                                      ParseFlag.SupportUnnamedObjects | ParseFlag.SupportRootObjects,
                                                                                    ))

    # ----------------------------------------------------------------------
    def test_Standard(self):
        root = _Invoke(textwrap.dedent(
                    """\
                    <>:
                        <>: pass
                        <>: pass
                    """))

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
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.arity, Arity.FromString('?'))

    # ----------------------------------------------------------------------
    def test_Format(self):
        # ----------------------------------------------------------------------
        def Verify(root):
            self.assertEqual(len(root.items), 2)

            item = root.items[0]
            self.assertEqual(item.name, None)
            self.assertEqual(list(item.metadata.keys()), [ "one", ])
            self.assertEqual(item.metadata["one"].Value, "two")
            self.assertEqual(len(item.items), 0)

            item = root.items[1]
            self.assertEqual(item.name, None)
            self.assertEqual(list(item.metadata.keys()), [ "one", "three", ])
            self.assertEqual(item.metadata["one"].Value, "two")
            self.assertEqual(item.metadata["three"].Value, "four")
            self.assertEqual(len(item.items), 0)

        # ----------------------------------------------------------------------

        # Standard
        Verify(_Invoke(textwrap.dedent(
                    """\
                    <one="two">: 
                        pass
        
                    <one='two' three="four">: 
                        pass
                    """)))
        
        # No sep
        Verify(_Invoke(textwrap.dedent(
                    """\
                    <one="two">: 
                        pass
                    <one='two' three="four">: 
                        pass
                    """)))
        
        # Wonky spacing
        Verify(_Invoke(textwrap.dedent(
                    """\
                    <one="two">: 


                        pass
        
                    <one='two' three="four">: 
                        pass




                    """)))

        # Inline
        Verify(_Invoke(textwrap.dedent(
                    """\
                    <one="two">: pass
                    <one='two' three="four">: pass
                    """)))
            
# ----------------------------------------------------------------------
class NamedObjSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_UnsupportedError(self):
        self.assertRaises(PopulateUnsupportedNamedObjectsException, lambda: Populate( { _script_fullpath: lambda: textwrap.dedent(
                                                                                                                      """\
                                                                                                                      <foo>: pass
                                                                                                                      """), },
                                                                                      0,
                                                                                    ))

    # ----------------------------------------------------------------------
    def test_UnsupportedRootError(self):
        self.assertRaises(PopulateUnsupportedRootObjectsException, lambda: Populate( { _script_fullpath: lambda: textwrap.dedent(
                                                                                                                        """\
                                                                                                                        <foo>: pass
                                                                                                                        """), },
                                                                                     ParseFlag.SupportNamedObjects,
                                                                                   ))

    # ----------------------------------------------------------------------
    def test_UnsupportedChildError(self):
        self.assertRaises(PopulateUnsupportedChildObjectsException, lambda: Populate( { _script_fullpath: lambda: textwrap.dedent(
                                                                                                                        """\
                                                                                                                        <foo>:
                                                                                                                            <bar>: 
                                                                                                                                pass
                                                                                                                        """), },
                                                                                      ParseFlag.SupportNamedObjects | ParseFlag.SupportRootObjects,
                                                                                    ))

    # ----------------------------------------------------------------------
    def test_Standard(self):
        root = _Invoke(textwrap.dedent(
                    """\
                    <foo>:
                        <bar>: pass
                        <baz>: pass
                    """))

        self.assertEqual(len(root.items), 1)
        self.assertEqual(root.items[0].name, "foo")
        self.assertEqual(root.items[0].reference, None)
        self.assertEqual(len(root.items[0].items), 2)
        self.assertEqual(root.items[0].items[0].name, "bar")
        self.assertEqual(root.items[0].items[0].reference, None)
        self.assertEqual(root.items[0].items[1].name, "baz")
        self.assertEqual(root.items[0].items[1].reference, None)
        self.assertEqual(len(root.items[0].items[0].items), 0)
        self.assertEqual(len(root.items[0].items[1].items), 0)

    # ----------------------------------------------------------------------
    def test_Metadata(self):
        item = _Invoke("<foo one='two'>: pass").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.reference, None)
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_Arity(self):
        item = _Invoke("<foo ?>: pass").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.reference, None)
        self.assertEqual(item.metadata, {})
        self.assertEqual(item.arity, Arity.FromString('?'))

    # ----------------------------------------------------------------------
    def test_MetadataAndArity(self):
        item = _Invoke("<foo one='two' ?>: pass").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.reference, None)
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.arity, Arity.FromString('?'))

    # ----------------------------------------------------------------------
    def test_Format(self):
        # ----------------------------------------------------------------------
        def Verify(root):
            self.assertEqual(len(root.items), 2)

            item = root.items[0]
            self.assertEqual(item.name, "foo")
            self.assertEqual(item.reference, None)
            self.assertEqual(list(item.metadata.keys()), [ "one", ])
            self.assertEqual(item.metadata["one"].Value, "two")
            self.assertEqual(len(item.items), 0)

            item = root.items[1]
            self.assertEqual(item.name, "bar")
            self.assertEqual(item.reference, None)
            self.assertEqual(list(item.metadata.keys()), [ "one", "three", ])
            self.assertEqual(item.metadata["one"].Value, "two")
            self.assertEqual(item.metadata["three"].Value, "four")
            self.assertEqual(len(item.items), 0)

        # ----------------------------------------------------------------------

        # Standard
        Verify(_Invoke(textwrap.dedent(
                    """\
                    <foo one="two">: 
                        pass
        
                    <bar one='two' three="four">: 
                        pass
                    """)))
        
        # No sep
        Verify(_Invoke(textwrap.dedent(
                    """\
                    <foo one="two">: 
                        pass
                    <bar one='two' three="four">: 
                        pass
                    """)))
        
        # Wonky spacing
        Verify(_Invoke(textwrap.dedent(
                    """\
                    <foo one="two">: 


                        pass
        
                    <bar one='two' three="four">: 
                        pass




                    """)))

        # Inline
        Verify(_Invoke(textwrap.dedent(
                    """\
                    <foo one="two">: pass
                    <bar one='two' three="four">: pass
                    """)))
    
    # ----------------------------------------------------------------------
    def test_Reference(self):
        root = _Invoke(textwrap.dedent(
                    """\
                    <foo bar>: pass
                    <baz biz one="two">: pass
                    """))

        self.assertEqual(len(root.items), 2)

        item = root.items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.reference, "bar")
        self.assertEqual(len(item.items), 0)

        item = root.items[1]

        self.assertEqual(item.name, "baz")
        self.assertEqual(item.reference, "biz")
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")

# ----------------------------------------------------------------------
class UnnamedDeclarationSuite(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_Standard(self):
        item = _Invoke("<string>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.reference, "string")
        self.assertFalse(item.metadata)
        self.assertFalse(item.arity)

    # ----------------------------------------------------------------------
    def test_Metadata(self):
        item = _Invoke("<string one='two'>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.reference, "string")
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertFalse(item.arity)

    # ----------------------------------------------------------------------
    def test_Arity(self):
        item = _Invoke("<string ?>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.reference, "string")
        self.assertEqual(item.metadata, {})
        self.assertEqual(item.arity, Arity.FromString('?'))

    # ----------------------------------------------------------------------
    def test_MetadataAndArity(self):
        item = _Invoke("<string one='two' ?>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.reference, "string")
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.arity, Arity.FromString('?'))

    # ----------------------------------------------------------------------
    def test_Variant(self):
        item = _Invoke("<(a|b|c)>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.reference, [ ( "a", [] ), ( "b", [] ), ( "c", [] ), ])
        self.assertEqual(item.metadata, {})
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_VariantGlobalMetadata(self):
        item = _Invoke("<(a|b|c) one='two'>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.reference, [ ( "a", [] ), ( "b", [] ), ( "c", [] ), ])
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_VariantItemMetadata(self):
        item = _Invoke("<(a|b inner=2.0|c) one='two'>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual([ name for name, _ in item.reference ], [ "a", "b", "c", ])
        self.assertEqual(item.reference[0], ( "a", [] ))
        self.assertEqual(len(item.reference[1][1]), 1)
        self.assertEqual(item.reference[1][1][0][1].Value, 2.0)
        self.assertEqual(item.reference[2], ( "c", [] ))
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.arity, None)

# ----------------------------------------------------------------------
class NamedDelcarationSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        item = _Invoke("<foo string>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.reference, "string")
        self.assertFalse(item.metadata)
        self.assertFalse(item.arity)

    # ----------------------------------------------------------------------
    def test_Metadata(self):
        item = _Invoke("<foo string one='two'>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.reference, "string")
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertFalse(item.arity)

    # ----------------------------------------------------------------------
    def test_Arity(self):
        item = _Invoke("<foo string ?>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.reference, "string")
        self.assertEqual(item.metadata, {})
        self.assertEqual(item.arity, Arity.FromString('?'))

    # ----------------------------------------------------------------------
    def test_MetadataAndArity(self):
        item = _Invoke("<foo string one='two' ?>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.reference, "string")
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.arity, Arity.FromString('?'))

    # ----------------------------------------------------------------------
    def test_Variant(self):
        item = _Invoke("<(a|b|c)>").items[0]

        self.assertEqual(item.name, None)
        self.assertEqual(item.reference, [ ( "a", [] ), ( "b", [] ), ( "c", [] ), ])
        self.assertEqual(item.metadata, {})
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_VariantGlobalMetadata(self):
        item = _Invoke("<foo (a|b|c) one='two'>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual(item.reference, [ ( "a", [] ), ( "b", [] ), ( "c", [] ), ])
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.arity, None)

    # ----------------------------------------------------------------------
    def test_VariantItemMetadata(self):
        item = _Invoke("<foo (a|b inner=2.0|c) one='two'>").items[0]

        self.assertEqual(item.name, "foo")
        self.assertEqual([ name for name, _ in item.reference ], [ "a", "b", "c", ])
        self.assertEqual(item.reference[0], ( "a", [] ))
        self.assertEqual(len(item.reference[1][1]), 1)
        self.assertEqual(item.reference[1][1][0][1].Value, 2.0)
        self.assertEqual(item.reference[2], ( "c", [] ))
        self.assertEqual(list(item.metadata.keys()), [ "one", ])
        self.assertEqual(item.metadata["one"].Value, "two")
        self.assertEqual(item.arity, None)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Invoke(content, parse_flags=ParseFlag.AllFlags):
    return Populate( { "content": lambda: content, },
                     parse_flags,
                   )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass