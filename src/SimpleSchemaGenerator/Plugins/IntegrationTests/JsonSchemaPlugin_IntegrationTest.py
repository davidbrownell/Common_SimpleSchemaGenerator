# ----------------------------------------------------------------------
# |
# |  JsonSchemaPlugin_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-18 17:05:36
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Integration tests for the JsonSchema plugin"""

import json
import os
import sys
import unittest

import jsonschema

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Generated", "AllTypes"))
with CallOnExit(lambda: sys.path.pop(0)):
    import AllTypes_PythonJsonSerialization as AllTypesJson
    import AllTypes_PythonYamlSerialization as AllTypesYaml

sys.path.insert(0, os.path.join(_script_dir, "Generated", "FileSystemTest"))
with CallOnExit(lambda: sys.path.pop(0)):
    import FileSystemTest_PythonJsonSerialization as FileSystemJson
    import FileSystemTest_PythonXmlSerialization as FileSystemXml

sys.path.insert(0, os.path.join(_script_dir, "Generated", "Test"))
with CallOnExit(lambda: sys.path.pop(0)):
    import Test_PythonJsonSerialization as TestJson
    import Test_PythonXmlSerialization as TestXml


# ----------------------------------------------------------------------
class JsonSchema(unittest.TestCase):
    # ----------------------------------------------------------------------
    def setUp(self):
        # AllTypes.yaml
        all_types_filename = os.path.join(_script_dir, "..", "Impl", "AllTypes.yaml")
        assert os.path.isfile(all_types_filename), all_types_filename

        all_types_original_content = AllTypesYaml.Deserialize_types(all_types_filename)
        all_types_content = AllTypesJson.Serialize_types(
            all_types_original_content,
            to_string=True,
        )

        all_types_filename = os.path.join(_script_dir, "Generated", "AllTypes", "AllTypes.schema.json")
        assert os.path.isfile(all_types_filename), all_types_filename

        # FileSystemTest.xml
        file_system_filename = os.path.join(_script_dir, "..", "Impl", "FileSystemTest.xml")
        assert os.path.isfile(file_system_filename), file_system_filename

        file_system_original_content = FileSystemXml.Deserialize(
            file_system_filename,
            process_additional_data=True,
        )
        file_system_content = FileSystemJson.Serialize(
            file_system_original_content,
            to_string=True,
            process_additional_data=True,
        )

        file_system_filename = os.path.join(_script_dir, "Generated", "FileSystemTest", "FileSystemTest.schema.json")
        assert os.path.isfile(file_system_filename), file_system_filename

        # Test.xml
        test_filename = os.path.join(_script_dir, "..", "Impl", "Test.xml")
        assert os.path.isfile(test_filename), test_filename

        test_original_content = TestXml.Deserialize(test_filename)
        test_content = TestJson.Serialize(
            test_original_content,
            to_string=True,
        )

        test_filename = os.path.join(_script_dir, "Generated", "Test", "Test.schema.json")
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
            schema_content = json.load(f)

        instance_content = json.loads(self._all_types)

        jsonschema.validate(
            instance=instance_content,
            schema=schema_content,
            format_checker=jsonschema.FormatChecker(),
        )

        instance_content["bool_"] = "not a bool"

        self.assertRaises(
            jsonschema.exceptions.ValidationError,
            lambda: jsonschema.validate(
                instance=instance_content,
                schema=schema_content,
                format_checker=jsonschema.FormatChecker(),
            ),
        )

    # ----------------------------------------------------------------------
    def test_FileSystem(self):
        with open(self._file_system_filename) as f:
            schema_content = json.load(f)

        instance_content = json.loads(self._file_system)

        jsonschema.validate(
            instance=instance_content,
            schema=schema_content,
            format_checker=jsonschema.FormatChecker(),
        )

    # ----------------------------------------------------------------------
    def test_Test(self):
        with open(self._test_filename) as f:
            schema_content = json.load(f)

        instance_content = json.loads(self._test)

        jsonschema.validate(
            instance=instance_content,
            schema=schema_content,
            format_checker=jsonschema.FormatChecker(),
        )

        # Min value is 20 for ints
        instance_content["test_derived"]["v1"] = 0

        self.assertRaises(
            jsonschema.exceptions.ValidationError,
            lambda: jsonschema.validate(
                instance=instance_content,
                schema=schema_content,
                format_checker=jsonschema.FormatChecker(),
            ),
        )

        instance_content["test_derived"]["v1"] = 20

        # Adding a value to test_derived is not supported
        instance_content["test_derived"]["foo"] = "bar"

        self.assertRaises(
            jsonschema.exceptions.ValidationError,
            lambda: jsonschema.validate(
                instance=instance_content,
                schema=schema_content,
                format_checker=jsonschema.FormatChecker(),
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
