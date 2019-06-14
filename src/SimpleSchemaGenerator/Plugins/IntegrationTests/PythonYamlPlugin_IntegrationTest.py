# ----------------------------------------------------------------------
# |
# |  PythonYamlPlugin_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-11 09:22:11
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Integration tests for PythonYamlPlugin"""

import os
import re
import sys
import textwrap
import unittest
import uuid

import rtyaml

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Generated", "AllTypes"))
with CallOnExit(lambda: sys.path.pop(0)):
    import AllTypes_PythonYamlSerialization as AllTypesYaml

sys.path.insert(0, os.path.join(_script_dir, "Generated", "FileSystemTest"))
with CallOnExit(lambda: sys.path.pop(0)):
    import FileSystemTest_PythonYamlSerialization as FileSystemYaml
    import FileSystemTest_PythonXmlSerialization as FileSystemXml

sys.path.insert(0, os.path.join(_script_dir, "Generated", "Test"))
with CallOnExit(lambda: sys.path.pop(0)):
    import Test_PythonYamlSerialization as TestYaml
    import Test_PythonXmlSerialization as TestXml


with InitRelativeImports():
    from .Impl.AllTypesUtils import AllTypesUtilsMixin
    from .Impl.FileSystemTestUtils import FileSystemUtilsMixin
    from .Impl.TestUtils import TestUtilsMixin


# ----------------------------------------------------------------------
class AllTypesSuite(unittest.TestCase, AllTypesUtilsMixin):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None

        yaml_filename = os.path.join(_script_dir, "..", "Impl", "AllTypes.yaml")
        assert os.path.isfile(yaml_filename), yaml_filename

        with open(yaml_filename) as f:
            yaml_content = rtyaml.load(f)

        self._yaml_filename = yaml_filename
        self._yaml_content = yaml_content

    # ----------------------------------------------------------------------
    def test_Standard(self):
        obj = AllTypesYaml.Deserialize_types(self._yaml_filename)

        self.ValidateTypes(obj)

    # ----------------------------------------------------------------------
    def test_StandardList(self):
        obj = AllTypesYaml.Deserialize_standard_list(
            textwrap.dedent(
                """\
                - one
                - two
                - three
                """,
            ),
        )

        self.assertEqual(obj, ["one", "two", "three"])

        # Errors
        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"An item was expected",
            lambda: AllTypesYaml.Deserialize_standard_list(""),
        )

    # ----------------------------------------------------------------------
    def test_OptionalList(self):
        self.assertEqual(
            AllTypesYaml.Deserialize_optional_list(
                textwrap.dedent(
                    """\
                    - one
                    - two
                    """,
                ),
            ),
            ["one", "two"],
        )

        self.assertEqual(AllTypesYaml.Deserialize_optional_list(""), [])

    # ----------------------------------------------------------------------
    def test_FixedList(self):
        self.assertEqual(
            AllTypesYaml.Deserialize_fixed_list(
                textwrap.dedent(
                    """\
                    - a
                    - b
                    - c
                    """,
                ),
            ),
            ["a", "b", "c"],
        )

        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"At least 3 items were expected \(2 found\)",
            lambda: AllTypesYaml.Deserialize_fixed_list(
                textwrap.dedent(
                    """\
                    - a
                    - b
                    """,
                ),
            ),
        )

        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"At most 3 items were expected \(4 found\)",
            lambda: AllTypesYaml.Deserialize_fixed_list(
                textwrap.dedent(
                    """\
                    - a
                    - b
                    - c
                    - d
                    """,
                ),
            ),
        )

    # ----------------------------------------------------------------------
    def test_Optional(self):
        self.assertEqual(AllTypesYaml.Deserialize_optional("test"), "test")
        self.assertEqual(AllTypesYaml.Deserialize_optional(""), AllTypesYaml.DoesNotExist)

    # ----------------------------------------------------------------------
    def test_Constraints(self):
        # directory_

        # Create a temp dir
        temp_dirname = os.path.join(os.getcwd(), str(uuid.uuid4()).replace("-", ""))
        assert not os.path.exists(temp_dirname), temp_dirname

        os.mkdir(temp_dirname)
        with CallOnExit(lambda: FileSystem.RemoveTree(temp_dirname)):
            self.assertEqual(
                AllTypesYaml.Deserialize_directory_(os.path.basename(temp_dirname)).lower(),
                temp_dirname.lower(),
            )

        # ----------------------------------------------------------------------
        def CaseInsensitiveException(ExceptionType, regex, func):
            try:
                func()
                self.assertFalse(True)
            except ExceptionType as ex:
                self.assertEqual(regex.lower(), str(ex).lower())

        # ----------------------------------------------------------------------

        CaseInsensitiveException(
            AllTypesYaml.DeserializeException,
            "'{}' is not a valid directory".format(os.path.join(os.getcwd(), "Does Not Exist")),
            lambda: AllTypesYaml.Deserialize_directory_("Does Not Exist"),
        )

        # filename_

        # Create a temp filename
        temp_filename = os.path.join(os.getcwd(), str(uuid.uuid4()).replace("-", ""))
        assert not os.path.exists(temp_filename), temp_filename

        with open(temp_filename, "w") as f:
            f.write("Temp file")

        with CallOnExit(lambda: FileSystem.RemoveFile(temp_filename)):
            self.assertEqual(
                AllTypesYaml.Deserialize_filename_('"{}"'.format(os.path.basename(temp_filename))).lower(),
                temp_filename.lower(),
            )

        CaseInsensitiveException(
            AllTypesYaml.DeserializeException,
            "'{}' is not a valid file".format(os.path.join(os.getcwd(), "Does Not Exist")),
            lambda: AllTypesYaml.Deserialize_filename_("Does Not Exist"),
        )

        # filename_any_
        temp_dirname = os.path.join(os.getcwd(), str(uuid.uuid4()).replace("-", ""))
        assert not os.path.exists(temp_dirname), temp_dirname

        os.mkdir(temp_dirname)
        with CallOnExit(lambda: FileSystem.RemoveTree(temp_dirname)):
            self.assertEqual(
                AllTypesYaml.Deserialize_filename_any_(
                    '"{}"'.format(os.path.basename(temp_dirname)),
                ).lower(),
                temp_dirname.lower(),
            )

        temp_filename = os.path.join(os.getcwd(), str(uuid.uuid4()).replace("-", ""))
        assert not os.path.exists(temp_filename), temp_filename

        with open(temp_filename, "w") as f:
            f.write("Temp file")

        with CallOnExit(lambda: FileSystem.RemoveFile(temp_filename)):
            self.assertEqual(
                AllTypesYaml.Deserialize_filename_any_(
                    '"{}"'.format(os.path.basename(temp_filename)),
                ).lower(),
                temp_filename.lower(),
            )

        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            re.escape(
                "'{}' is not a valid file or directory".format(
                    os.path.join(os.getcwd(), "Does Not Exist"),
                ),
            ),
            lambda: AllTypesYaml.Deserialize_filename_any_("Does Not Exist"),
        )

        # number_
        self.assertEqual(AllTypesYaml.Deserialize_number_("2"), 2)
        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"-30 is not >= -20.0",
            lambda: AllTypesYaml.Deserialize_number_("-30"),
        )
        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"40 is not <= 20.0",
            lambda: AllTypesYaml.Deserialize_number_("40"),
        )

        # int_
        self.assertEqual(AllTypesYaml.Deserialize_int_("10"), 10)
        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"-30 is not >= -20",
            lambda: AllTypesYaml.Deserialize_int_("-30"),
        )
        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"40 is not <= 20",
            lambda: AllTypesYaml.Deserialize_int_("40"),
        )

        # string_
        self.assertEqual(AllTypesYaml.Deserialize_string_("abc"), "abc")
        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"'a' is not a valid 'String' string - Value must have at least 2 characters, not have more than 4 characters",
            lambda: AllTypesYaml.Deserialize_string_("a"),
        )
        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"'abcde' is not a valid 'String' string - Value must have at least 2 characters, not have more than 4 characters",
            lambda: AllTypesYaml.Deserialize_string_("abcde"),
        )

        # string_regex_
        self.assertEqual(AllTypesYaml.Deserialize_string_regex_("bit"), "bit")
        self.assertEqual(AllTypesYaml.Deserialize_string_regex_("but"), "but")
        self.assertEqual(AllTypesYaml.Deserialize_string_regex_("bat"), "bat")
        self.assertRaisesRegex(
            AllTypesYaml.DeserializeException,
            r"'abc' is not a valid 'String' string - Value must match the regular expression 'b.t'",
            lambda: AllTypesYaml.Deserialize_string_regex_("abc"),
        )


# ----------------------------------------------------------------------
class FileSystemSuite(unittest.TestCase, FileSystemUtilsMixin):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None

        # Use the xml file as a source as it is capable of processing attributes.
        xml_filename = os.path.join(_script_dir, "..", "Impl", "FileSystemTest.xml")
        assert os.path.isfile(xml_filename), xml_filename

        xml_obj = FileSystemXml.Deserialize(xml_filename)

        xml_obj_additional_data = FileSystemXml.Deserialize(
            xml_filename,
            process_additional_data=True,
        )

        self._xml_obj = xml_obj
        self._xml_obj_additional_data = xml_obj_additional_data

    # ----------------------------------------------------------------------
    def test_All(self):
        serialized_obj = FileSystemYaml.Serialize(self._xml_obj)

        self.ValidateRoot(serialized_obj.root)
        self.ValidateRoots(serialized_obj.roots)

        obj = FileSystemYaml.Deserialize(serialized_obj)

        self.ValidateRoot(obj.root)
        self.ValidateRoots(obj.roots)

    # ----------------------------------------------------------------------
    def test_AllAdditionalData(self):
        serialized_obj = FileSystemYaml.Serialize(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        self.ValidateRoot(
            serialized_obj.root,
            process_additional_data=True,
        )

        self.ValidateRoots(
            serialized_obj.roots,
            process_additional_data=True,
        )

        obj = FileSystemYaml.Deserialize(
            serialized_obj,
            process_additional_data=True,
        )

        self.ValidateRoot(
            obj.root,
            process_additional_data=True,
        )

        self.ValidateRoots(
            obj.roots,
            process_additional_data=True,
        )

    # ----------------------------------------------------------------------
    def test_Root(self):
        serialized_obj = FileSystemYaml.Serialize_root(self._xml_obj.root)

        self.ValidateRoot(serialized_obj)

        obj = FileSystemYaml.Deserialize_root(serialized_obj)

        self.ValidateRoot(obj)

    # ----------------------------------------------------------------------
    def test_RootAdditionalData(self):
        serialized_obj = FileSystemYaml.Serialize_root(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        self.ValidateRoot(
            serialized_obj,
            process_additional_data=True,
        )

        obj = FileSystemYaml.Deserialize_root(
            serialized_obj,
            process_additional_data=True,
        )

        self.ValidateRoot(
            obj,
            process_additional_data=True,
        )

    # ----------------------------------------------------------------------
    def test_Roots(self):
        serialized_obj = FileSystemYaml.Serialize_roots(self._xml_obj.roots)

        self.ValidateRoots(serialized_obj)

        obj = FileSystemYaml.Deserialize_roots(serialized_obj)

        self.ValidateRoots(obj)

    # ----------------------------------------------------------------------
    def test_RootsAdditionalData(self):
        serialized_obj = FileSystemYaml.Serialize_roots(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        self.ValidateRoots(
            serialized_obj,
            process_additional_data=True,
        )

        obj = FileSystemYaml.Deserialize_roots(
            serialized_obj,
            process_additional_data=True,
        )

        self.ValidateRoots(
            obj,
            process_additional_data=True,
        )

    # ----------------------------------------------------------------------
    def test_AllToString(self):
        python_obj = FileSystemYaml.Deserialize(self._xml_obj)

        s = FileSystemYaml.Serialize(
            python_obj,
            to_string=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                root:
                  directories:
                  - directories:
                    - files:
                      - name: file1
                        size: 10
                      - name: file2
                        size: 200
                      name: three
                    name: two
                  files:
                  - name: file10
                    size: 20
                  name: one
                roots:
                - name: dir1
                - name: dir2
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_AllAdditionalDataToString(self):
        python_obj = FileSystemYaml.Deserialize(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        s = FileSystemYaml.Serialize(
            python_obj,
            process_additional_data=True,
            to_string=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                root:
                  directories:
                  - directories:
                    - files:
                      - name: file1
                        size: 10
                      - name: file2
                        size: 200
                      name: three
                    name: two
                  files:
                  - name: file10
                    size: 20
                  name: one
                roots:
                - name: dir1
                - extra:
                  - simple_value: value
                    two: '2'
                  - a: a
                    b: b
                    value:
                    - one: '1'
                      simple_value: text value
                    - simple_value: another text value
                  name: dir2
                  """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootToString(self):
        python_obj = FileSystemYaml.Deserialize_root(self._xml_obj)

        s = FileSystemYaml.Serialize_root(
            python_obj,
            to_string=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                directories:
                - directories:
                  - files:
                    - name: file1
                      size: 10
                    - name: file2
                      size: 200
                    name: three
                  name: two
                files:
                - name: file10
                  size: 20
                name: one
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootAdditionalDataToString(self):
        python_obj = FileSystemYaml.Deserialize_root(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        s = FileSystemYaml.Serialize_root(
            python_obj,
            process_additional_data=True,
            to_string=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                directories:
                - directories:
                  - files:
                    - name: file1
                      size: 10
                    - name: file2
                      size: 200
                    name: three
                  name: two
                files:
                - name: file10
                  size: 20
                name: one
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootsToString(self):
        python_obj = FileSystemYaml.Deserialize_roots(self._xml_obj)

        s = FileSystemYaml.Serialize_roots(
            python_obj,
            to_string=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                - name: dir1
                - name: dir2
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootsAdditionalDataToString(self):
        python_obj = FileSystemYaml.Deserialize_roots(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        s = FileSystemYaml.Serialize_roots(
            python_obj,
            process_additional_data=True,
            to_string=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                - name: dir1
                - extra:
                  - simple_value: value
                    two: '2'
                  - a: a
                    b: b
                    value:
                    - one: '1'
                      simple_value: text value
                    - simple_value: another text value
                  name: dir2
                """,
            ),
        )


# ----------------------------------------------------------------------
class TestSuite(unittest.TestCase, TestUtilsMixin):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None

        xml_filename = os.path.join(_script_dir, "..", "Impl", "Test.xml")
        assert os.path.isfile(xml_filename), xml_filename

        xml_obj = TestXml.Deserialize(xml_filename)

        self._xml_obj = xml_obj

    # ----------------------------------------------------------------------
    def test_All(self):
        serialized_obj = TestYaml.Serialize(self._xml_obj)
        obj = TestYaml.Deserialize(serialized_obj)

        self.ValidateTestBase(obj.test_base)
        self.ValidateTestDerived(obj.test_derived)

    # ----------------------------------------------------------------------
    def test_Base(self):
        serialized_obj = TestYaml.Serialize_test_base(self._xml_obj)

        self.ValidateTestBase(serialized_obj)

        obj = TestYaml.Deserialize_test_base(serialized_obj)

        self.ValidateTestBase(obj)

    # ----------------------------------------------------------------------
    def test_Derived(self):
        serialized_obj = TestYaml.Serialize_test_derived(self._xml_obj)
        obj = TestYaml.Deserialize_test_derived(serialized_obj)

        self.ValidateTestDerived(obj)


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
