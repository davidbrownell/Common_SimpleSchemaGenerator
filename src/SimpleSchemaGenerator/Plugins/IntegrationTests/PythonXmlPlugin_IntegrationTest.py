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
"""Integration tests for PythonXmlPlugin"""

import os
import sys
import textwrap
import unittest

import xml.etree.ElementTree as ET

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Generated", "FileSystemTest"))
with CallOnExit(lambda: sys.path.pop(0)):
    import FileSystemTest_PythonXmlSerialization as FileSystemXmlSerialization

sys.path.insert(0, os.path.join(_script_dir, "Generated", "Test"))
with CallOnExit(lambda: sys.path.pop(0)):
    import Test_PythonXmlSerialization as TestXmlSerialization


with InitRelativeImports():
    from .Impl.FileSystemTestUtils import FileSystemUtilsMixin
    from .Impl.TestUtils import TestUtilsMixin


# ----------------------------------------------------------------------
class FileSystemSuiteImpl(unittest.TestCase, FileSystemUtilsMixin):
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
class TestSuiteImpl(unittest.TestCase, TestUtilsMixin):
    pass


# ----------------------------------------------------------------------
class FileSystemSuite(FileSystemSuiteImpl):
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
        obj = FileSystemXmlSerialization.Deserialize(self._xml_filename)

        self.ValidateRoot(obj.root)
        self.ValidateRoots(obj.roots)

    # ----------------------------------------------------------------------
    def test_StandardAdditionalData(self):
        obj = FileSystemXmlSerialization.Deserialize(
            self._xml_filename,
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
    def test_All(self):
        python_object = FileSystemXmlSerialization.Deserialize(self._xml_filename)

        xml_object = FileSystemXmlSerialization.Serialize(python_object)

        self.Match(
            xml_object,
            self._xml_content,
            include_extra=False,
        )

    # ----------------------------------------------------------------------
    def test_AllAdditionalData(self):
        python_object = FileSystemXmlSerialization.Deserialize(
            self._xml_filename,
            process_additional_data=True,
        )

        xml_object = FileSystemXmlSerialization.Serialize(
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
        python_object = FileSystemXmlSerialization.Deserialize_root(self._xml_filename)
        xml_object = FileSystemXmlSerialization.Serialize_root(python_object)

        self.Match(
            xml_object,
            self._xml_content.findall("root")[0],
            include_extra=False,
        )

    # ----------------------------------------------------------------------
    def test_RootAdditionalData(self):
        python_object = FileSystemXmlSerialization.Deserialize_root(
            self._xml_filename,
            process_additional_data=True,
        )

        xml_object = FileSystemXmlSerialization.Serialize_root(
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
        python_object = FileSystemXmlSerialization.Deserialize_roots(self._xml_filename)
        xml_object = FileSystemXmlSerialization.Serialize_roots(python_object)

        self.Match(
            xml_object,
            self._xml_content.findall("roots")[0],
            include_extra=False,
        )

    # ----------------------------------------------------------------------
    def test_RootsAdditionalData(self):
        python_object = FileSystemXmlSerialization.Deserialize_roots(
            self._xml_filename,
            process_additional_data=True,
        )

        xml_object = FileSystemXmlSerialization.Serialize_roots(
            python_object,
            process_additional_data=True,
        )

        self.Match(
            xml_object,
            self._xml_content.findall("roots")[0],
            include_extra=True,
        )

    # ----------------------------------------------------------------------
    def test_AllToString(self):
        python_obj = FileSystemXmlSerialization.Deserialize(self._xml_filename)

        s = FileSystemXmlSerialization.Serialize(
            python_obj,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                <_>
                  <root name="one">
                    <directories>
                      <item name="two">
                        <directories>
                          <item name="three">
                            <files>
                              <item size="10">file1</item>
                              <item size="200">file2</item>
                            </files>
                          </item>
                        </directories>
                      </item>
                    </directories>
                    <files>
                      <item size="20">file10</item>
                    </files>
                  </root>
                  <roots>
                    <item name="dir1" />
                    <item name="dir2" />
                  </roots>
                </_>
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_AllToStringNoPrettyPrint(self):
        python_obj = FileSystemXmlSerialization.Deserialize(self._xml_filename)

        s = FileSystemXmlSerialization.Serialize(
            python_obj,
            to_string=True,
        )

        self.assertEqual(
            s,
            """<_><root name="one"><directories><item name="two"><directories><item name="three"><files><item size="10">file1</item><item size="200">file2</item></files></item></directories></item></directories><files><item size="20">file10</item></files></root><roots><item name="dir1" /><item name="dir2" /></roots></_>""",
        )

    # ----------------------------------------------------------------------
    def test_AllAdditionalDataToString(self):
        python_obj = FileSystemXmlSerialization.Deserialize(
            self._xml_filename,
            process_additional_data=True,
        )

        s = FileSystemXmlSerialization.Serialize(
            python_obj,
            process_additional_data=True,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                <_>
                  <root name="one">
                    <directories>
                      <item name="two">
                        <directories>
                          <item name="three">
                            <files>
                              <item size="10">file1</item>
                              <item size="200">file2</item>
                            </files>
                          </item>
                        </directories>
                      </item>
                    </directories>
                    <files>
                      <item size="20">file10</item>
                    </files>
                  </root>
                  <roots>
                    <item name="dir1" />
                    <item name="dir2">
                      <extra>
                        <item two="2">value</item>
                        <item a="a" b="b">
                          <value>
                            <item one="1">text value</item>
                            <item>another text value</item>
                          </value>
                        </item>
                      </extra>
                    </item>
                  </roots>
                </_>
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootToString(self):
        python_obj = FileSystemXmlSerialization.Deserialize_root(self._xml_filename)

        s = FileSystemXmlSerialization.Serialize_root(
            python_obj,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                <root name="one">
                  <directories>
                    <item name="two">
                      <directories>
                        <item name="three">
                          <files>
                            <item size="10">file1</item>
                            <item size="200">file2</item>
                          </files>
                        </item>
                      </directories>
                    </item>
                  </directories>
                  <files>
                    <item size="20">file10</item>
                  </files>
                </root>
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootAdditionalDataToString(self):
        python_obj = FileSystemXmlSerialization.Deserialize_root(
            self._xml_filename,
            process_additional_data=True,
        )

        s = FileSystemXmlSerialization.Serialize_root(
            python_obj,
            process_additional_data=True,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                <root name="one">
                  <directories>
                    <item name="two">
                      <directories>
                        <item name="three">
                          <files>
                            <item size="10">file1</item>
                            <item size="200">file2</item>
                          </files>
                        </item>
                      </directories>
                    </item>
                  </directories>
                  <files>
                    <item size="20">file10</item>
                  </files>
                </root>
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootsToString(self):
        python_obj = FileSystemXmlSerialization.Deserialize_roots(self._xml_filename)

        s = FileSystemXmlSerialization.Serialize_roots(
            python_obj,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                <roots>
                  <item name="dir1" />
                  <item name="dir2" />
                </roots>
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootsAdditionalDataToString(self):
        python_obj = FileSystemXmlSerialization.Deserialize_roots(
            self._xml_filename,
            process_additional_data=True,
        )

        s = FileSystemXmlSerialization.Serialize_roots(
            python_obj,
            process_additional_data=True,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                <roots>
                  <item name="dir1" />
                  <item name="dir2">
                    <extra>
                      <item two="2">value</item>
                      <item a="a" b="b">
                        <value>
                          <item one="1">text value</item>
                          <item>another text value</item>
                        </value>
                      </item>
                    </extra>
                  </item>
                </roots>
                """,
            ),
        )


# ----------------------------------------------------------------------
class TestSuite(TestSuiteImpl):
    # ----------------------------------------------------------------------
    def setUp(self):
        xml_filename = os.path.join(_script_dir, "..", "Impl", "Test.xml")
        assert os.path.isfile(xml_filename), xml_filename

        self._xml_filename = xml_filename

    # ----------------------------------------------------------------------
    def test_Standard(self):
        obj = TestXmlSerialization.Deserialize(self._xml_filename)

        self.ValidateTestBase(obj.test_base)
        self.ValidateTestDerived(obj.test_derived)


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
