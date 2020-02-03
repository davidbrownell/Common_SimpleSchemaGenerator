# ----------------------------------------------------------------------
# |
# |  ProcessAdditionalData_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-26 19:03:41
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Integration test for ProcessAdditionalData"""

import json
import os
import sys
import unittest

import jsonschema
from lxml import etree
from six.moves import StringIO

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "Generated", "ProcessAdditionalData"))
with CallOnExit(lambda: sys.path.pop(0)):
    import ProcessAdditionalData_PythonJsonSerialization as JsonSerialization
    import ProcessAdditionalData_PythonXmlSerialization as XmlSerialization

# ----------------------------------------------------------------------
class ProcessAdditionalData(unittest.TestCase):
    # ----------------------------------------------------------------------
    def setUp(self):
        process_additional_data_filename = os.path.join(_script_dir, "..", "Impl", "ProcessAdditionalData.json")
        assert os.path.isfile(process_additional_data_filename), process_additional_data_filename

        json_schema = os.path.join(_script_dir, "Generated", "ProcessAdditionalData", "ProcessAdditionalData.schema.json")
        assert os.path.isfile(json_schema), json_schema

        xsd_schema = os.path.join(_script_dir, "Generated", "ProcessAdditionalData", "ProcessAdditionalData.xsd")
        assert os.path.isfile(xsd_schema), xsd_schema

        self._process_additional_data_filename = process_additional_data_filename
        self._json_schema = json_schema
        self._xsd_schema = xsd_schema

    # ----------------------------------------------------------------------
    def test_JsonSchema(self):
        with open(self._json_schema) as f:
            schema_content = json.load(f)

        content = JsonSerialization.Deserialize(self._process_additional_data_filename)

        json_content = json.loads(
            JsonSerialization.Serialize(
                content,
                to_string=True,
                pretty_print=True,
            ),
        )

        jsonschema.validate(
            instance=json_content,
            schema=schema_content,
            format_checker=jsonschema.FormatChecker(),
        )

        json_content["one"]["extra"] = 1

        jsonschema.validate(
            instance=json_content,
            schema=schema_content,
            format_checker=jsonschema.FormatChecker(),
        )

        json_content["two"]["extra"] = 1

        self.assertRaises(
            jsonschema.exceptions.ValidationError,
            lambda: jsonschema.validate(
                instance=json_content,
                schema=schema_content,
                format_checker=jsonschema.FormatChecker(),
            ),
        )

    # ----------------------------------------------------------------------
    def test_XsdSchema(self):
        with open(self._xsd_schema) as f:
            schema_doc = etree.parse(StringIO(f.read()))

        schema = etree.XMLSchema(schema_doc)

        content = JsonSerialization.Deserialize(self._process_additional_data_filename)

        xml_content = XmlSerialization.Serialize(
            content,
            to_string=True,
        )

        schema.assertValid(etree.parse(StringIO(xml_content)))

        xml_content = xml_content.replace("</a></one>", "</a><extra>2</extra></one>")

        schema.assertValid(etree.parse(StringIO(xml_content)))

        xml_content = xml_content.replace("</a></two>", "</a><extra>2</extra></two>")

        self.assertRaises(etree.DocumentInvalid, lambda: schema.assertValid(etree.parse(StringIO(xml_content))))


    # ----------------------------------------------------------------------
    def test_JsonSerialization(self):
        self.assertRaises(
            JsonSerialization.SerializeException,
            lambda: JsonSerialization.Serialize(
                {
                    "root" : {
                        "one" : {
                            "a": "string one",
                            "additional_child": "another string one",
                        },
                        "two": {
                            "a": "string two",
                            "additional_child" : "another string two",
                        },
                    },
                },
            ),
        )

        # No exception if processing additional data
        JsonSerialization.Serialize(
            {
                "root" : {
                    "one" : {
                        "a": "string one",
                        "additional_child": "another string one",
                    },
                    "two": {
                        "a": "string two",
                        "additional_child" : "another string two",
                    },
                },
            },
            process_additional_data=True,
        )

    # ----------------------------------------------------------------------
    def test_JsonDeserialize(self):
        self.assertRaises(
            JsonSerialization.DeserializeException,
            lambda: JsonSerialization.Deserialize(
                {
                    "root" : {
                        "one" : {
                            "a": "string one",
                            "additional_child": "another string one",
                        },
                        "two": {
                            "a": "string two",
                            "additional_child" : "another string two",
                        },
                    },
                },
            ),
        )

        JsonSerialization.Deserialize(
            {
                "root" : {
                    "one" : {
                        "a": "string one",
                        "additional_child": "another string one",
                    },
                    "two": {
                        "a": "string two",
                        "additional_child" : "another string two",
                    },
                },
            },
            process_additional_data=True,
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
