# ----------------------------------------------------------------------
# |
# |  PythonXmlPlugin_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-10 13:29:23
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Integration test for PythonXmlPlugin"""

import os
import sys
import unittest

import xml.etree.ElementTree as ET

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Generated", "FileSystemTest"))
with CallOnExit(lambda: sys.path.pop(0)):
    import FileSystemTest_PythonXmlSerialization as XmlSerialization


# ----------------------------------------------------------------------
class SuiteImpl(unittest.TestCase):
    # ----------------------------------------------------------------------
    def Match(
        self,
        a,
        b,
        include_extra=False,
    ):
        diffs = []

        for this, that in zip(
            self._Enum(
                a,
                include_extra=include_extra,
            ),
            self._Enum(
                b,
                include_extra=include_extra,
            ),
        ):
            if this[0] == "_" and that[0] == "everything":
                continue

            if this != that:
                diffs.append("{} != {}".format(this, that))

        if diffs:
            self.assertFalse("\n".join(diffs))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _Enum(cls, root, include_extra):
        if root.tag == "extra" and not include_extra:
            return

        yield root.tag, root.attrib, root.text.strip() if root.text else ""

        for child in root:
            yield from cls._Enum(child, include_extra)


# ----------------------------------------------------------------------
class FileSystemSuite(SuiteImpl):
    # ----------------------------------------------------------------------
    def setUp(self):
        xml_filename = os.path.join(_script_dir, "..", "Impl", "FileSystemTest.xml")
        assert os.path.isfile(xml_filename), xml_filename

        with open(xml_filename) as f:
            xml_content = ET.fromstring(f.read())

        self._xml_filename = xml_filename
        self._xml_content = xml_content

    # ----------------------------------------------------------------------
    def test_Standard(self):
        obj = XmlSerialization.Deserialize(self._xml_filename)

        # root
        self.assertEqual(obj.root.name, "one")
        self.assertEqual(obj.root.directories[0].name, "two")
        self.assertEqual(obj.root.directories[0].directories[0].name, "three")
        self.assertEqual(obj.root.directories[0].directories[0].files[0].name, "file1")
        self.assertEqual(obj.root.directories[0].directories[0].files[0].size, 10)
        self.assertEqual(obj.root.directories[0].directories[0].files[1].name, "file2")
        self.assertEqual(obj.root.directories[0].directories[0].files[1].size, 200)
        self.assertEqual(obj.root.files[0].name, "file10")
        self.assertEqual(obj.root.files[0].size, 20)

        # roots
        self.assertEqual(obj.roots[0].name, "dir1")
        self.assertEqual(obj.roots[1].name, "dir2")

    # ----------------------------------------------------------------------
    def test_StandardAdditionalData(self):
        obj = XmlSerialization.Deserialize(
            self._xml_filename,
            process_additional_data=True,
        )

        self.assertEqual(obj.roots[1].extra[0].two, "2")
        self.assertEqual(obj.roots[1].extra[0].simple_value, "value")
        self.assertEqual(obj.roots[1].extra[1].a, "a")
        self.assertEqual(obj.roots[1].extra[1].b, "b")
        self.assertEqual(obj.roots[1].extra[1].value[0].one, "1")
        self.assertEqual(obj.roots[1].extra[1].value[0].simple_value, "text value")
        self.assertEqual(obj.roots[1].extra[1].value[1].simple_value, "another text value")

    # ----------------------------------------------------------------------
    def test_All(self):
        python_object = XmlSerialization.Deserialize(self._xml_filename)

        xml_object = XmlSerialization.Serialize(python_object)

        self.Match(
            xml_object,
            self._xml_content,
            include_extra=False,
        )

    # ----------------------------------------------------------------------
    def test_AllAdditionalData(self):
        python_object = XmlSerialization.Deserialize(
            self._xml_filename,
            process_additional_data=True,
        )

        xml_object = XmlSerialization.Serialize(
            python_object,
            process_additional_data=True,
        )

        self.Match(
            xml_object,
            self._xml_content,
            include_extra=True,
        )

    # ----------------------------------------------------------------------
    def test_Root(self):
        python_object = XmlSerialization.Deserialize_root(self._xml_filename)
        xml_object = XmlSerialization.Serialize_root(python_object)

        self.Match(
            xml_object,
            self._xml_content.findall("root")[0],
            include_extra=False,
        )

    # ----------------------------------------------------------------------
    def test_RootAdditionalData(self):
        python_object = XmlSerialization.Deserialize_root(
            self._xml_filename,
            process_additional_data=True,
        )

        xml_object = XmlSerialization.Serialize_root(
            python_object,
            process_additional_data=True,
        )

        self.Match(
            xml_object,
            self._xml_content.findall("root")[0],
            include_extra=True,
        )

    # ----------------------------------------------------------------------
    def test_Roots(self):
        python_object = XmlSerialization.Deserialize_roots(self._xml_filename)
        xml_object = XmlSerialization.Serialize_roots(python_object)

        self.Match(
            xml_object,
            self._xml_content.findall("roots")[0],
            include_extra=False,
        )

    # ----------------------------------------------------------------------
    def test_RootsAdditionalData(self):
        python_object = XmlSerialization.Deserialize_roots(
            self._xml_filename,
            process_additional_data=True,
        )

        xml_object = XmlSerialization.Serialize_roots(
            python_object,
            process_additional_data=True,
        )

        self.Match(
            xml_object,
            self._xml_content.findall("roots")[0],
            include_extra=True,
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
