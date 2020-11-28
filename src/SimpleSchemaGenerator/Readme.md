# SimpleSchemaGenerator
SimpleSchemaGenerator is a tool that processes generic SimpleSchema definitions according to a specified plugin. The same SimpleSchema definition can be used with [plugins](#SimpleSchema-Plugins) that generate [JSON schema files](./Plugins/JsonSchemaPlugin.py), [serialize to and from yaml](./Plugins/PythonYamlPlugin.py) (including validation), generate ORM definitions, class implementations, and a variety of other tasks.

To begin using the SimpleSchemaGenerator, create a SimpleSchema definition based on the description [here](#SimpleSchema-Format) or using one of the [examples](#SimpleSchema-Examples).

```
python SimpleSchemaGenerator.py Generate <command line args>
```

For a description of all available command line arguments and functionality, run:

```
python SimpleSchemaGenerator.py /?
```

## Table of Contents

BugBug: TOC

## SimpleSchema Format

### BugBug: Basics
### BugBug: Definition, Attribute, Standard
### BugBug: Fundamental Elements
### BugBug: Compound Elements
### BugBUg: Simple Elements
### BugBug: Arity
### BugBug: Arity gotchas

## SimpleSchema Plugins

| Plugin Name | Description |
| ----------- | ----------- |
| [JsonSchema](./Plugins/JsonSchemaPlugin.py) | Generates a JSON Schema file (https://json-schema.org/) |
| [Pickle](./Plugins/PicklePlugin.py) | Pickles each element to a file |
| [PyDictionary](./Plugins/PyDictionaryPlugin.py) |Generates python source code that contains a dictionary with top-level enum schema elements that have corresponding friendly names |
| [PythonJson](./Plugins/PythonJsonPlugin.py) | Creates python code that is able to serialize and deserialize python objects to JSON |
| [PythonXml](./Plugins/PythonXmlPlugin.py) | Creates Python code that is able to serialize and deserialize python objects to XML |
| [PythonYaml](./Plugins/PythonYamlPlugin.py) | Creates python code that is able to serialize and deserialize python objects to YAML |
| [XsdSchema](./Plugins/XsdSchemaPlugin.py) | Generates an XSD Schema file (XML Schema Definition) |

## SimpleSchema Examples

### Hierarchical File System

```
(File string fundamental_name="name"):
    [size int min=0]

(Directory process_additional_data=true):
    [name string]
    <directories Directory key="name" *>
    <files File key="name" *>

<root Directory ?>
<roots Directory key="name" +>
```
