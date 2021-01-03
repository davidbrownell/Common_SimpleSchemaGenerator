# ----------------------------------------------------------------------
# |
# |  XsdSchemaPlugin_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-22 20:29:04
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-21
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit tests for XsdSchema.py"""

import os
import sys
import textwrap
import unittest

from lxml import etree
from six.moves import StringIO

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import StringHelpers

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Generated", "AllTypes"))
with CallOnExit(lambda: sys.path.pop(0)):
    import AllTypes_PythonXmlSerialization as AllTypesXml
    import AllTypes_PythonYamlSerialization as AllTypesYaml

sys.path.insert(0, os.path.join(_script_dir, "Generated", "FileSystemTest"))
with CallOnExit(lambda: sys.path.pop(0)):
    import FileSystemTest_PythonXmlSerialization as FileSystemXml

sys.path.insert(0, os.path.join(_script_dir, "Generated", "Test"))
with CallOnExit(lambda: sys.path.pop(0)):
    import Test_PythonXmlSerialization as TestXml


# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class XsdSchema(unittest.TestCase):
    # ----------------------------------------------------------------------
    def setUp(self):
        # AllTypes.yaml
        all_types_filename = os.path.join(_script_dir, "..", "Impl", "AllTypes.yaml")
        assert os.path.isfile(all_types_filename), all_types_filename

        all_types_original_content = AllTypesYaml.Deserialize_types(all_types_filename)
        all_types_content = AllTypesXml.Serialize_types(
            all_types_original_content,
            to_string=True,
        )

        all_types_filename = os.path.join(_script_dir, "Generated", "AllTypes", "AllTypes.xsd")
        assert os.path.isfile(all_types_filename), all_types_filename

        # FileSystemTest.xml
        file_system_filename = os.path.join(_script_dir, "..", "Impl", "FileSystemTest.xml")
        assert os.path.isfile(file_system_filename), file_system_filename

        with open(file_system_filename) as f:
            file_system_content = f.read()

        file_system_filename = os.path.join(_script_dir, "Generated", "FileSystemTest", "FileSystemTest.xsd")
        assert os.path.isfile(file_system_filename), file_system_filename

        # Test.xml
        test_filename = os.path.join(_script_dir, "..", "Impl", "Test.xml")
        assert os.path.isfile(test_filename), test_filename

        with open(test_filename) as f:
            test_content = f.read()

        test_filename = os.path.join(_script_dir, "Generated", "Test", "Test.xsd")
        assert os.path.isfile(test_filename), test_filename

        self._all_types = all_types_content
        self._all_types_filename = all_types_filename

        self._file_system = file_system_content
        self._file_system_filename = file_system_filename

        self._test = test_content
        self._test_filename = test_filename

    # ----------------------------------------------------------------------
    def test_AllTypes(self):
        with open(self._all_types_filename) as f:
            schema_content = f.read()

        schema_doc = etree.parse(StringIO(schema_content))
        schema = etree.XMLSchema(schema_doc)

        xml_content = self._all_types

        schema.assertValid(etree.parse(StringIO(xml_content)))

        xml_content = xml_content.replace("<bool_><item>true</item>", "<bool_><item>not a bool</item>")

        self.assertRaises(etree.DocumentInvalid, lambda: schema.assertValid(etree.parse(StringIO(xml_content))))

    # ----------------------------------------------------------------------
    def test_FileSystem(self):
        with open(self._file_system_filename) as f:
            schema_content = f.read()

        schema_doc = etree.parse(StringIO(schema_content))
        schema = etree.XMLSchema(schema_doc)

        xml_content = self._file_system.replace("everything", "FileSystemTest")

        # Remove the extra content, as it can't be properly parsed by
        # the xsd schema (this is a limitation of XSD (see "Unique Particle
        # Attribution")).
        xml_content = xml_content.replace("<extra>", "<!--<extra>")
        xml_content = xml_content.replace("</extra>", "</extra>-->")

        schema.assertValid(etree.parse(StringIO(xml_content)))

    # ----------------------------------------------------------------------
    def test_Test(self):
        with open(self._test_filename) as f:
            schema_content = f.read()

        schema_doc = etree.parse(StringIO(schema_content))
        schema = etree.XMLSchema(schema_doc)

        xml_content = self._test.replace("root", "Test")

        schema.assertValid(etree.parse(StringIO(xml_content)))


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
