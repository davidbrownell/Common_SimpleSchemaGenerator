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
import sys
import textwrap
import unittest

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Generated", "FileSystemTest"))
with CallOnExit(lambda: sys.path.pop(0)):
    import FileSystemTest_PythonYamlSerialization as YamlSerialization
    import FileSystemTest_PythonXmlSerialization as XmlSerialization


with InitRelativeImports():
    from .Impl.FileSystemTestUtils import FileSystemUtilsMixin


# ----------------------------------------------------------------------
class FileSystemSuite(unittest.TestCase, FileSystemUtilsMixin):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None

        # Use the xml file as a source as it is capable of processing attributes.
        xml_filename = os.path.join(_script_dir, "..", "Impl", "FileSystemTest.xml")
        assert os.path.isfile(xml_filename), xml_filename

        xml_obj = XmlSerialization.Deserialize(xml_filename)

        xml_obj_additional_data = XmlSerialization.Deserialize(
            xml_filename,
            process_additional_data=True,
        )

        self._xml_obj = xml_obj
        self._xml_obj_additional_data = xml_obj_additional_data

    # ----------------------------------------------------------------------
    def test_All(self):
        serialized_obj = YamlSerialization.Serialize(self._xml_obj)

        self.ValidateRoot(serialized_obj.root)
        self.ValidateRoots(serialized_obj.roots)

        obj = YamlSerialization.Deserialize(serialized_obj)

        self.ValidateRoot(obj.root)
        self.ValidateRoots(obj.roots)

    # ----------------------------------------------------------------------
    def test_AllAdditionalData(self):
        serialized_obj = YamlSerialization.Serialize(
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

        obj = YamlSerialization.Deserialize(
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
        serialized_obj = YamlSerialization.Serialize_root(self._xml_obj.root)

        self.ValidateRoot(serialized_obj)

        obj = YamlSerialization.Deserialize_root(serialized_obj)

        self.ValidateRoot(obj)

    # ----------------------------------------------------------------------
    def test_RootAdditionalData(self):
        serialized_obj = YamlSerialization.Serialize_root(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        self.ValidateRoot(
            serialized_obj,
            process_additional_data=True,
        )

        obj = YamlSerialization.Deserialize_root(
            serialized_obj,
            process_additional_data=True,
        )

        self.ValidateRoot(
            obj,
            process_additional_data=True,
        )

    # ----------------------------------------------------------------------
    def test_Roots(self):
        serialized_obj = YamlSerialization.Serialize_roots(self._xml_obj.roots)

        self.ValidateRoots(serialized_obj)

        obj = YamlSerialization.Deserialize_roots(serialized_obj)

        self.ValidateRoots(obj)

    # ----------------------------------------------------------------------
    def test_RootsAdditionalData(self):
        serialized_obj = YamlSerialization.Serialize_roots(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        self.ValidateRoots(
            serialized_obj,
            process_additional_data=True,
        )

        obj = YamlSerialization.Deserialize_roots(
            serialized_obj,
            process_additional_data=True,
        )

        self.ValidateRoots(
            obj,
            process_additional_data=True,
        )

    # ----------------------------------------------------------------------
    def test_AllToString(self):
        python_obj = YamlSerialization.Deserialize(self._xml_obj)

        s = YamlSerialization.Serialize(
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
        python_obj = YamlSerialization.Deserialize(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        s = YamlSerialization.Serialize(
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
        python_obj = YamlSerialization.Deserialize_root(self._xml_obj)

        s = YamlSerialization.Serialize_root(
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
        python_obj = YamlSerialization.Deserialize_root(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        s = YamlSerialization.Serialize_root(
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
        python_obj = YamlSerialization.Deserialize_roots(self._xml_obj)

        s = YamlSerialization.Serialize_roots(
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
        python_obj = YamlSerialization.Deserialize_roots(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        s = YamlSerialization.Serialize_roots(
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
