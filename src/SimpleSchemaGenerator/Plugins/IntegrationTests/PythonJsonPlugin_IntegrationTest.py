# ----------------------------------------------------------------------
# |
# |  PythonJsonPlugin_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-11 09:22:11
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Integration tests for PythonJsonPlugin"""

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

sys.path.insert(0, os.path.join(_script_dir, "Generated", "DefaultValues"))
with CallOnExit(lambda: sys.path.pop(0)):
    import DefaultValues_PythonJsonSerialization as DefaultValuesJsonSerialization


sys.path.insert(0, os.path.join(_script_dir, "Generated", "DictionaryTest"))
with CallOnExit(lambda: sys.path.pop(0)):
    import DictionaryTest_PythonJsonSerialization as DictionaryTestJsonSerialization
    import DictionaryTest_PythonYamlSerialization as DictionaryTestYamlSerialization


sys.path.insert(0, os.path.join(_script_dir, "Generated", "FileSystemTest"))
with CallOnExit(lambda: sys.path.pop(0)):
    import FileSystemTest_PythonJsonSerialization as FileSystemJsonSerialization
    import FileSystemTest_PythonXmlSerialization as FileSystemXmlSerialization


sys.path.insert(0, os.path.join(_script_dir, "Generated", "Test"))
with CallOnExit(lambda: sys.path.pop(0)):
    import Test_PythonJsonSerialization as TestJsonSerialization
    import Test_PythonXmlSerialization as TestXmlSerialization


with InitRelativeImports():
    from .Impl.DefaultValuesUtils import DefaultValuesMixin
    from .Impl.DictionaryTestUtils import DictionaryTestMixin
    from .Impl.FileSystemTestUtils import FileSystemUtilsMixin
    from .Impl.TestUtils import TestUtilsMixin

# ----------------------------------------------------------------------
class FileSystemSuite(unittest.TestCase, FileSystemUtilsMixin):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None

        # Use the xml file as a source as it is capable of processing attributes.
        xml_filename = os.path.join(_script_dir, "..", "Impl", "FileSystemTest.xml")
        assert os.path.isfile(xml_filename), xml_filename

        xml_obj = FileSystemXmlSerialization.Deserialize(
          xml_filename,
          process_additional_data=True,
        )

        xml_obj_additional_data = FileSystemXmlSerialization.Deserialize(
            xml_filename,
            process_additional_data=True,
        )

        self._xml_obj = xml_obj
        self._xml_obj_additional_data = xml_obj_additional_data

    # ----------------------------------------------------------------------
    def test_All(self):
        serialized_obj = FileSystemJsonSerialization.Serialize(
          self._xml_obj,
          process_additional_data=True,
        )

        self.ValidateRoot(serialized_obj.root)
        self.ValidateRoots(serialized_obj.roots)

        obj = FileSystemJsonSerialization.Deserialize(
          serialized_obj,
          process_additional_data=True,
        )

        self.ValidateRoot(obj.root)
        self.ValidateRoots(obj.roots)

    # ----------------------------------------------------------------------
    def test_AllAdditionalData(self):
        serialized_obj = FileSystemJsonSerialization.Serialize(
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

        obj = FileSystemJsonSerialization.Deserialize(
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
        serialized_obj = FileSystemJsonSerialization.Serialize_root(self._xml_obj.root)

        self.ValidateRoot(serialized_obj)

        obj = FileSystemJsonSerialization.Deserialize_root(serialized_obj)

        self.ValidateRoot(obj)

    # ----------------------------------------------------------------------
    def test_RootAdditionalData(self):
        serialized_obj = FileSystemJsonSerialization.Serialize_root(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        self.ValidateRoot(
            serialized_obj,
            process_additional_data=True,
        )

        obj = FileSystemJsonSerialization.Deserialize_root(
            serialized_obj,
            process_additional_data=True,
        )

        self.ValidateRoot(
            obj,
            process_additional_data=True,
        )

    # ----------------------------------------------------------------------
    def test_Roots(self):
        serialized_obj = FileSystemJsonSerialization.Serialize_roots(
            self._xml_obj.roots,
            process_additional_data=True,
        )

        self.ValidateRoots(serialized_obj)

        obj = FileSystemJsonSerialization.Deserialize_roots(
            serialized_obj,
            process_additional_data=True,
        )

        self.ValidateRoots(obj)

    # ----------------------------------------------------------------------
    def test_RootsAdditionalData(self):
        serialized_obj = FileSystemJsonSerialization.Serialize_roots(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        self.ValidateRoots(
            serialized_obj,
            process_additional_data=True,
        )

        obj = FileSystemJsonSerialization.Deserialize_roots(
            serialized_obj,
            process_additional_data=True,
        )

        self.ValidateRoots(
            obj,
            process_additional_data=True,
        )

    # ----------------------------------------------------------------------
    def test_AllToString(self):
        python_obj = FileSystemJsonSerialization.Deserialize(
          self._xml_obj,
          process_additional_data=True,
        )

        s = FileSystemJsonSerialization.Serialize(
            python_obj,
            to_string=True,
            pretty_print=True,
            process_additional_data=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                {
                  "root" : {
                    "name" : "one",
                    "directories" : [
                      {
                        "name" : "two",
                        "directories" : [
                          {
                            "name" : "three",
                            "files" : [
                              {
                                "size" : 10,
                                "name" : "file1"
                              },
                              {
                                "size" : 200,
                                "name" : "file2"
                              }
                            ]
                          }
                        ]
                      }
                    ],
                    "files" : [
                      {
                        "size" : 20,
                        "name" : "file10"
                      }
                    ]
                  },
                  "roots" : [
                    {
                      "name" : "dir1"
                    },
                    {
                      "name" : "dir2",
                      "extra" : [
                        {
                          "two" : "2",
                          "simple_value" : "value"
                        },
                        {
                          "a" : "a",
                          "b" : "b",
                          "value" : [
                            {
                              "one" : "1",
                              "simple_value" : "text value"
                            },
                            {
                              "simple_value" : "another text value"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }""",
            ),
        )

    # ----------------------------------------------------------------------
    def test_AllToStringNoPrettyPrint(self):
        python_obj = FileSystemJsonSerialization.Deserialize(
            self._xml_obj,
            process_additional_data=True,
        )

        s = FileSystemJsonSerialization.Serialize(
            python_obj,
            to_string=True,
            process_additional_data=True,
        )

        self.assertEqual(
            s,
            """{"root": {"name": "one", "directories": [{"name": "two", "directories": [{"name": "three", "files": [{"size": 10, "name": "file1"}, {"size": 200, "name": "file2"}]}]}], "files": [{"size": 20, "name": "file10"}]}, "roots": [{"name": "dir1"}, {"name": "dir2", "extra": [{"two": "2", "simple_value": "value"}, {"a": "a", "b": "b", "value": [{"one": "1", "simple_value": "text value"}, {"simple_value": "another text value"}]}]}]}""",
        )

    # ----------------------------------------------------------------------
    def test_AllAdditionalDataToString(self):
        python_obj = FileSystemJsonSerialization.Deserialize(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        s = FileSystemJsonSerialization.Serialize(
            python_obj,
            process_additional_data=True,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                {
                  "root" : {
                    "name" : "one",
                    "directories" : [
                      {
                        "name" : "two",
                        "directories" : [
                          {
                            "name" : "three",
                            "files" : [
                              {
                                "size" : 10,
                                "name" : "file1"
                              },
                              {
                                "size" : 200,
                                "name" : "file2"
                              }
                            ]
                          }
                        ]
                      }
                    ],
                    "files" : [
                      {
                        "size" : 20,
                        "name" : "file10"
                      }
                    ]
                  },
                  "roots" : [
                    {
                      "name" : "dir1"
                    },
                    {
                      "name" : "dir2",
                      "extra" : [
                        {
                          "two" : "2",
                          "simple_value" : "value"
                        },
                        {
                          "a" : "a",
                          "b" : "b",
                          "value" : [
                            {
                              "one" : "1",
                              "simple_value" : "text value"
                            },
                            {
                              "simple_value" : "another text value"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }""",
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootToString(self):
        python_obj = FileSystemJsonSerialization.Deserialize_root(self._xml_obj)

        s = FileSystemJsonSerialization.Serialize_root(
            python_obj,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                {
                  "name" : "one",
                  "directories" : [
                    {
                      "name" : "two",
                      "directories" : [
                        {
                          "name" : "three",
                          "files" : [
                            {
                              "size" : 10,
                              "name" : "file1"
                            },
                            {
                              "size" : 200,
                              "name" : "file2"
                            }
                          ]
                        }
                      ]
                    }
                  ],
                  "files" : [
                    {
                      "size" : 20,
                      "name" : "file10"
                    }
                  ]
                }""",
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootAdditionalDataToString(self):
        python_obj = FileSystemJsonSerialization.Deserialize_root(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        s = FileSystemJsonSerialization.Serialize_root(
            python_obj,
            process_additional_data=True,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                {
                  "name" : "one",
                  "directories" : [
                    {
                      "name" : "two",
                      "directories" : [
                        {
                          "name" : "three",
                          "files" : [
                            {
                              "size" : 10,
                              "name" : "file1"
                            },
                            {
                              "size" : 200,
                              "name" : "file2"
                            }
                          ]
                        }
                      ]
                    }
                  ],
                  "files" : [
                    {
                      "size" : 20,
                      "name" : "file10"
                    }
                  ]
                }""",
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootsToString(self):
        python_obj = FileSystemJsonSerialization.Deserialize_roots(
            self._xml_obj,
            process_additional_data=True,
        )

        s = FileSystemJsonSerialization.Serialize_roots(
            python_obj,
            to_string=True,
            pretty_print=True,
            process_additional_data=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                [
                  {
                    "name" : "dir1"
                  },
                  {
                    "name" : "dir2",
                    "extra" : [
                      {
                        "two" : "2",
                        "simple_value" : "value"
                      },
                      {
                        "a" : "a",
                        "b" : "b",
                        "value" : [
                          {
                            "one" : "1",
                            "simple_value" : "text value"
                          },
                          {
                            "simple_value" : "another text value"
                          }
                        ]
                      }
                    ]
                  }
                ]""",
            ),
        )

    # ----------------------------------------------------------------------
    def test_RootsAdditionalDataToString(self):
        python_obj = FileSystemJsonSerialization.Deserialize_roots(
            self._xml_obj_additional_data,
            process_additional_data=True,
        )

        s = FileSystemJsonSerialization.Serialize_roots(
            python_obj,
            process_additional_data=True,
            to_string=True,
            pretty_print=True,
        )

        self.assertEqual(
            s,
            textwrap.dedent(
                """\
                [
                  {
                    "name" : "dir1"
                  },
                  {
                    "name" : "dir2",
                    "extra" : [
                      {
                        "two" : "2",
                        "simple_value" : "value"
                      },
                      {
                        "a" : "a",
                        "b" : "b",
                        "value" : [
                          {
                            "one" : "1",
                            "simple_value" : "text value"
                          },
                          {
                            "simple_value" : "another text value"
                          }
                        ]
                      }
                    ]
                  }
                ]""",
            ),
        )


# ----------------------------------------------------------------------
class TestSuite(unittest.TestCase, TestUtilsMixin):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None

        xml_filename = os.path.join(_script_dir, "..", "Impl", "Test.xml")
        assert os.path.isfile(xml_filename), xml_filename

        xml_obj = TestXmlSerialization.Deserialize(xml_filename)

        self._xml_obj = xml_obj

    # ----------------------------------------------------------------------
    def test_All(self):
        serialized_obj = TestJsonSerialization.Serialize(self._xml_obj)
        obj = TestJsonSerialization.Deserialize(serialized_obj)

        self.ValidateTestBase(obj.test_base)
        self.ValidateTestDerived(obj.test_derived)

    # ----------------------------------------------------------------------
    def test_Base(self):
        serialized_obj = TestJsonSerialization.Serialize_test_base(self._xml_obj)

        self.ValidateTestBase(serialized_obj)

        obj = TestJsonSerialization.Deserialize_test_base(serialized_obj)

        self.ValidateTestBase(obj)

    # ----------------------------------------------------------------------
    def test_Derived(self):
        serialized_obj = TestJsonSerialization.Serialize_test_derived(self._xml_obj)
        obj = TestJsonSerialization.Deserialize_test_derived(serialized_obj)

        self.ValidateTestDerived(obj)


# ----------------------------------------------------------------------
class DefaultValuesSuite(unittest.TestCase, DefaultValuesMixin):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None

    # ----------------------------------------------------------------------
    def test_All(self):
        json_filename = os.path.join(_script_dir, "..", "Impl", "DefaultValues.json")
        assert os.path.isfile(json_filename), json_filename

        obj = DefaultValuesJsonSerialization.Deserialize(json_filename)

        self.ValidateObject1(obj[0])
        self.ValidateObject2(obj[1])


# ----------------------------------------------------------------------
class DictionaryTestSuite(unittest.TestCase, DictionaryTestMixin):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None

        json_filename = os.path.join(_script_dir, "..", "Impl", "DictionaryTest.json")
        assert os.path.isfile(json_filename), json_filename

        self._json_filename                 = json_filename

    # ----------------------------------------------------------------------
    def test_SimpleDict(self):
        json_obj = DictionaryTestJsonSerialization.Deserialize_simple_dict(self._json_filename)
        self.ValidateSimpleDict(json_obj)

        yaml_obj = DictionaryTestYamlSerialization.Serialize_simple_dict(json_obj)
        self.ValidateSimpleDict(yaml_obj)

    # ----------------------------------------------------------------------
    def test_StandardDict(self):
        json_obj = DictionaryTestJsonSerialization.Deserialize_standard_dict(self._json_filename)
        self.ValidateStandardDict(json_obj)

        yaml_obj = DictionaryTestYamlSerialization.Serialize_standard_dict(json_obj)
        self.ValidateStandardDict(yaml_obj)

    # ----------------------------------------------------------------------
    def test_NestedDict(self):
        json_obj = DictionaryTestJsonSerialization.Deserialize_nested_dict(self._json_filename)
        self.ValidateNestedDict(json_obj)

        yaml_obj = DictionaryTestYamlSerialization.Serialize_nested_dict(json_obj)
        self.ValidateNestedDict(yaml_obj)


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
