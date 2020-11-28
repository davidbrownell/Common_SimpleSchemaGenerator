SimpleSchema
============

SimpleSchema is a [Domain Specific Language](https://en.wikipedia.org/wiki/Domain-specific_language) for data. This file describes the syntax for SimpleSchema documents and provides examples for how that syntax can be used to represent simple or complex data type definitions. These definitions can be used by different code generators to generate code that consumes, generates, or processes real data that conforms to the requirements of the data type definitions themselves.

More information about about the SimpleSchemaGenerator and code generators that operate on SimpleSchema data definitions can be found at [../Readme.md](../Readme.md).


Table of Contents
=================

- [Basic Syntax](#basic-syntax)
- [Delimiters](#delimiters)
- [Fundamental Elements](#fundamental-elements)
- [Compound Elements](#compound-elements)
- [Simple Elements](#simple-elements)
- [Collections](#collections)
- [Reference Elements](#reference-elements)
- [Miscellaneous Elements](#miscellaneous-elements)
- [Miscellaneous Statements](#miscellaneous-statements)
- [Examples](#examples)


**BugBug: Refresh this at https://ecotrust-canada.github.io/markdown-toc/**

Basic Syntax
============
[Return to Top](#SimpleSchema)

A SimpleSchema statement is comprised of these components:

```
Line 1) <name element_type attributes arity> # Standard
Line 2) [name element_type attributes arity] # Attribute
Line 3) (name element_type attributes arity) # Definition
```

Delimiters are starting and ending tokens that determine the statement's types. In these examples, the following are delimiters:

- `<` and `>` (Line 1)
- `[` and `]` (Line 2)
- `(` and `)` (Line 3) are delimiters.

Comments begin with a `#` character and extend to the end of the line. In these examples, the following are comments and are ignored by code generators:

- `# Standard` (Line 1)
- `# Attribute` (Line 2)
- `# Definition` (Line 3)

| Component    | Description                                                                                                                                                                                                         |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| delimiter    | Starting and ending token pair that indicates the statement type. See [delimiters](#delimiters) for information on statement types and how they are used by code generators.                                        |
| name         | [Optional] Name of the value.                                                                                                                                                                                       |
| element_type | Element type. For more information, see [Fundamental Elements](#fundamental-elements), [Compound Elements](#compound-elements), [Simple Elements](#simple-elements), and [Reference Elements](#reference-elements). |
| attributes   | [Optional] Attributes associated with the element type or [Collections](#collections).                                                                                                                              |
| arity        | [Optional] Information used to indicate that the statement refers to a [Collection of or optional](#collections)  values.                                                                                           |

Examples:
```
                                       # Delimiter   Name                 Element Type     Attributes  Arity
                                       # ----------  -------------------  ---------------  ----------  -----
<age int min=0>                        # Standard    age                  int              min=0

<person>:                              # Standard    person               Compound
    [first_name string]                # Attribute   first_name           string
    [last_name string]                 # Attribute   last_name            string

(positive_number number min=0.0)       # Definition  positive_number      number           min=0.0
<positive_number_ref positive_number>  # Standard    positive_number_ref  positive_number

<people person *>                      # Standard    people               person                       *
```

Attributes:
| Name | Description | Type | Default Value |
| - | - | - | - |
| `description` | Description of the element; this is often used by code generators to provide documentation in the generated code. | `string` | (None) |
| `name` | Override the name of the element when the desired name is a SimpleSchema keyword; for example, to name an element 'pass' (which is a reserved keyword): `<pass_ string name="pass">`. | `string` | (None) |

Delimiters
==========
[Return to Top](#SimpleSchema)

A statement may be a Standard, Attribute, or Definition statement. While a code generator may interpret these statement types in different ways, the following definitions generally hold true. Code generators that deviate from these definitions should explicitly call out these deviations in their documentation.

| Name       | Description                                                                                                                                                                                                                                                                         | Starting Token | Ending Token | Example                                                                  |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|--------------|--------------------------------------------------------------------------|
| Standard   | A standard statement; generated code should process these items directly.                                                                                                                                                                                                           | `<`            | `>`          | `<first_name string>`                                                    |
| Attribute  | A statement that should be interpreted as metadata associated with this corresponding element; attributes should only be used as children of [Compound Elements](#compound-elements) or [Simple Elements](#simple-elements).                                                        | `[`            | `]`          | `[metadata string]`                                                      |
| Definition | A statement that is not written directly by the code generator, but is [referenced](#reference-elements) by other statements within a SimpleSchema document. Intentional use of definitions within a schema prevent code duplication and can make it much easier to read and write. | `(`            | `)`          | `(semantic_version string validation_expression="\d+\.\d+\.\d+(-\S+)?")` |

Fundamental Elements
====================
[Return to Top](#SimpleSchema)

Fundamental elements are the basic building blocks of SimpleSchemas, representing primitive data types for schema definitions.

This collection of types is similar to those types found in [JSON](https://www.json.org/json-en.html), [XML](https://www.w3.org/XML/), [YAML](https://yaml.org/), and [SQL](https://en.wikipedia.org/wiki/SQL), but extended to allow enhanced validation capabilities leveraged by code generators. For example, the [filename](#filename) type is introduced so that code generators can generate code to verify that the file exists when executed.

+ [bool](#bool)
+ [datetime](#datetime)
+ [date](#date)
+ [directory](#directory)
+ [duration](#duration)
+ [enum](#enum)
+ [filename](#filename)
+ [guid](#guid)
+ [int](#int)
+ [number](#number)
+ [string](#string)
+ [time](#time)
+ [uri](#uri)

bool
----
A boolean type (https://en.wikipedia.org/wiki/Boolean_data_type).

Examples:
```
<value bool> # true, false
```

datetime
--------
A type that contains both a date and a time (https://en.wikipedia.org/wiki/ISO_8601).

Examples:
```
<value datetime> # 2020-11-27T15:30:29+00:00
                 # 2020-11-27T15:30:29Z
                 # 20201127T153029Z
```

date
----
A date type (https://en.wikipedia.org/wiki/ISO_8601#Dates).

Examples:
```
<value date> # 2020-11-27
             # 20201127
```

directory
---------
A filesystem directory type (https://en.wikipedia.org/wiki/Directory_(computing)).

To ensure compatibility across systems, values should use `'/'` as the directory separator.

Attributes:

| Name            | Description                                                                                           | Type      | Default Value |
|-----------------|-------------------------------------------------------------------------------------------------------|-----------|---------------|
| `ensure_exists` | Code generators should generate validation that ensure the value is valid in the current environment. | `boolean` | `true`        |

Examples:
```
<value directory> # C:/Users/dave           <-- Valid
                  # /home/dave              <-- Valid
                  # /home/invalid_username  <-- Invalid (invalid directory)

<value directory ensure_exists=false> # C:/Users/dave           <-- Valid
                                      # /home/dave              <-- Valid
                                      # /home/invalid_username  <-- Valid
```

duration
--------
The amount of elapsed time between two events, measured in hours/minutes/seconds/microseconds.

Examples:
```
<value duration> # 0:12:13      <-- 12 minutes, 13 seconds
                 # 32:01:02     <-- 32 hours, 1 minute, 2 seconds
                 # 0:01:02.03   <-- 1 minute, 2 seconds, 3 microseconds
```

enum
----
A type that defines a discrete set of valid values (https://en.wikipedia.org/wiki/Enumerated_type).

Attributes:

| Name              | Description                                                                                                    | Type           | Default Value |
|-------------------|----------------------------------------------------------------------------------------------------------------|----------------|---------------|
| `values`          | List of all valid values.                                                                                      | `List<string>` | (Required)    |
| `friendly_values` | List of human-readable values. The number of values here much match the number of values provided in `values`. | `List<string>` | None          |

Examples:
```
<value enum values=[one, two, three]> # one     <-- Valid
                                      # three   <-- Valid
                                      # One     <-- Invalid (not a valid value)

<value enum values=[one, two] friendly_values=["1", "2"]>
```

filename
--------
A filesystem filename type (https://en.wikipedia.org/wiki/Filename).

To ensure compatibility across systems, values should use `'/'` as the directory separator.

Attributes:

| Name            | Description                                                                                           | Type      | Default Value |
|-----------------|-------------------------------------------------------------------------------------------------------|-----------|---------------|
| `ensure_exists` | Code generators should generate validation that ensure the value is valid in the current environment. | `boolean` | `true`        |
| `match_any`     | Matches `filename` or `directory` items.                                                              | `boolean` | `false`       |

Examples:
```
<value filename> # C:/Users/dave/file.txt           <-- Valid
                 # /home/dave/file.txt              <-- Valid
                 # /home/dave/invalid_filename.txt  <-- Invalid (invalid filename)
                 # /home/dave                       <-- Invalid (is directory)

<value filename ensure_exists=false> # C:/Users/dave/file.txt           <-- Valid
                                     # /home/dave/file.txt              <-- Valid
                                     # /home/dave/invalid_filename.txt  <-- Valid
                                     # /home/dave                       <-- Valid

<value filename match_any=true> # C:/Users/dave/file.txt            <-- Valid
                                # /home/dave/file.txt               <-- Valid
                                # /home/dave/invalid_filename.txt   <-- Invalid (invalid filename)
                                # /home/dave                        <-- Valid
```

guid
----
A globally unique identifier type (https://en.wikipedia.org/wiki/Universally_unique_identifier).

Examples:
```
<value guid> # 123e4567-e89b-12d3-a456-426614174000
```

int
---
An integer type (https://en.wikipedia.org/wiki/Integer).

Attributes:

| Name       | Description                                               | Type           | Default Value |
|------------|-----------------------------------------------------------|----------------|---------------|
| `min`      | Minimum valid value (inclusive).                          | `int`          | None          |
| `max`      | Maximum valid value (inclusive).                          | `int`          | None          |
| `bytes`    | Number of bytes used to story values.                     | `[1, 2, 4, 8]` | None          |
| `unsigned` | `true` if values should only represent positive integers. | `boolean`      | `false`       |


Examples:
```
<value int> # 3     <-- Valid
            # -5    <-- Valid
            # 20    <-- Valid
            # -2    <-- Valid
            # 10    <-- Valid

<value int min=-2> # 3     <-- Valid
                   # -5    <-- Invalid (< -2)
                   # 20    <-- Valid
                   # -2    <-- Valid
                   # 10    <-- Valid

<value int max=10> # 3     <-- Valid
                   # -5    <-- Valid
                   # 20    <-- Invalid (> 10)
                   # -2    <-- Valid
                   # 10    <-- Valid

<value int min=-2 max=10> # 3   <-- Valid
                          # -5  <-- Invalid (< -2)
                          # 20  <-- Invalid (> 10)
                          # -2  <-- Valid
                          # 10  <-- Valid

<value int unsigned=true> # 3   <-- Valid
                          # -5  <-- Invalid (< 0)
                          # 20  <-- Valid
                          # -2  <-- Invalid (< 0)
                          # 10  <-- Valid

<value int bytes=1> # 3     <-- Valid
                    # -5    <-- Valid
                    # 200   <-- Invalid (too big to fit in signed byte (https://en.wikipedia.org/wiki/Integer_overflow))

<value int bytes=1 unsigned=true> # 3     <-- Valid
                                  # -5    <-- Invalid (< 0)
                                  # 200   <-- Valid
```

number
------
A floating point number type (https://en.wikipedia.org/wiki/Floating-point_arithmetic).

Attributes:

| Name  | Description                      | Type    | Default Value |
|-------|----------------------------------|---------|---------------|
| `min` | Minimum valid value (inclusive). | `float` | None          |
| `max` | Maximum valid value (inclusive). | `float` | None          |


Examples:
```
<value number> # 3.14   <-- Valid
               # -5.2   <-- Valid
               # 20.3   <-- Valid
               # 0.0    <-- Valid
               # 10.0   <-- Valid

<value number min=0.0> # 3.14   <-- Valid
                       # -5.2   <-- Invalid (< 0.0)
                       # 20.3   <-- Valid
                       # 0.0    <-- Valid
                       # 10.0   <-- Valid

<value number max=10.0> # 3.14  <-- Valid
                        # -5.2  <-- Valid
                        # 20.3  <-- Invalid (> 10.0)
                        # 0.0   <-- Valid
                        # 10.0  <-- Valid

<value number min=0.0 max=10.0> # 3.14  <-- Valid
                                # -5.2  <-- Invalid (< 0.0)
                                # 20.3  <-- Invalid (> 10.0)
                                # 0.0   <-- Valid
                                # 10.0  <-- Valid

```

string
------
A string type (https://en.wikipedia.org/wiki/String_(computer_science)).

Attributes:
| Name                    | Description                                                                                            | Type     | Default Value |
|-------------------------|--------------------------------------------------------------------------------------------------------|----------|---------------|
| `min_length`            | Minimum valid string length (inclusive).                                                               | `int`    | `1`           |
| `max_length`            | Maximum valid string length (inclusive).                                                               | `int`    | None          |
| `validation_expression` | [Regular expression](https://en.wikipedia.org/wiki/Regular_expression) used to validate string values. | `string` | None          |

Examples:
```
<value string> # one    <-- Valid
               # two    <-- Valid
               # three  <-- Valid
               # a      <-- Valid
               # test   <-- Valid

<value string min_length=2> # one       <-- Valid
                            # two       <-- Valid
                            # three     <-- Valid
                            # a         <-- Invalid (too short)
                            # test      <-- Valid

<value string max_length=3> # one       <-- Valid
                            # two       <-- Valid
                            # three     <-- Invalid (too long)
                            # a         <-- Valid
                            # test      <-- Invalid (too long)

<value string min_length=2 max_length=3> # one      <-- Valid
                                         # two      <-- Valid
                                         # three    <-- Invalid (too long)
                                         # a        <-- Invalid (too short)
                                         # test     <-- Invalid (too long)

<value string validation_expression="t.+"> # one    <-- Invalid (does not match the regex)
                                           # two    <-- Valid
                                           # three  <-- Valid
                                           # a      <-- Invalid (does not match the regex)
                                           # test   <-- Valid
```

time
----
A time type (https://en.wikipedia.org/wiki/ISO_8601#Times).

Examples:
```
<value time> # 15:30:29+00:00
             # 15:30:29Z
             # 153029Z
```

uri
---
A Uniform Resource Identifier (https://en.wikipedia.org/wiki/Uniform_Resource_Identifier).

Examples:
```
<value uri> # https://en.wikipedia.org
            # file:///home/dave/filename.txt
```

Compound Elements
=================
[Return to Top](#SimpleSchema)

[Fundamental Elements](#fundamental-elements) refer to single values while Compound Elements refer to a collection of values. These element types can have zero or more children and reference zero or more base Compound Elements.

They way and which children and base classes are used is dependent upon the code generator operating upon the SimpleSchema document.

Simple Example
--------------
A single element that groups multiple [Fundamental Elements](#fundamental-elements) into a logical group.

```
<person>:                       # No bases
    <first_name string>
    <middle_name string ?>
    <last_name string>

    <age int min=0>
```

Single Base
-----------
Compound Elements may be based on other Compound Elements. Some code generators will use these base relationships to aggregate child elements, while others will preserve the relationship and create polymorphic relationships. Consult the code generator documentation for more information on how these relationships are expressed in generated code.

```
<base>:
    <first_value string>

<derived1 base>:                # Single base
    <second_value int>

<derived2 base>:                # Single base
    <second_value number>
```


Multiple Bases
--------------
A Compound Element may reference multiple bases.

```
<base_a>:
    <a string>

<base_b>:
    <b string>

<derived1 (base_a, base_b)>:    # Multiple bases
    <second_value int>

<derived2 (base_a, base_b)>:    # Multiple bases
    <second_value number>
```

Empty
-----
An empty Compound Element.

```
<empty_object>:
    pass
```

Simple Elements
===============
[Return to Top](#SimpleSchema)

Simple Elements are a special type of [Compound Element](#compound-elements) - all children must be `Attribute` statement types and the element must reference a [Fundamental Element](#fundamental-elements) or another [Simple Element](#simple-elements). Some code generators cannot directly express Simple Elements, so care must be taken to only introduce these element types in SimpleSchema documents designed for these code generators or add metadata to the statement so that it can be used with other code generators.

```
# In XML, the following values can be expressed as:
#
#   <simple has_numbers="false" has_uppercase="false">string value</simple>
#   <simple has_numbers="true" has_uppercase="false">test123</simple>
#
# However, they can not be expressed in JSON, YAML, etc.
#

<simple string>:
    [has_numbers bool]
    [has_uppercase bool]

<more_complex simple>:
    [has_lowercase bool]
```

Attributes:
| Name | Description | Type | Default Value |
| - | - | - | - |
| `fundamental_name` | Name used to capture the elements fundamental value for code generators that cannot directly express Simple Elements | `string` | (None) |

The SimpleSchema in the example above, however adding `fundamental_element` gives code generators enough information to process the Simple Element as a [Compound Element](#compound-elements).

```
# In XML, the following values can be expressed as:
#
#   <simple has_numbers="false" has_uppercase="false">string value</simple>
#   <simple has_numbers="true" has_uppercase="false">test123</simple>
#
# In JSON, the following values can be expressed as:
#
#   {
#       "the_value" : "string value",
#       "has_numbers" : false,
#       "has_uppercase" : false
#   }
#   {
#       "the_value" : "test123",
#       "has_numbers" : true,
#       "has_uppercase" : false
#   }
#

<simple string fundamental_name=the_value>:
    [has_numbers bool]
    [has_uppercase bool]

<more_complex simple>:
    [has_lowercase bool]
```

Collections
===========
[Return to Top](#SimpleSchema)

Most of the examples so far have shown how to define elements that correspond to a single value. `arity` information can be used within an element's statement to indicate that the values should represent collections or an optional value.

| Arity     | Description         | Example                               |
|-----------|---------------------|---------------------------------------|
| (None)    | Single value        | `<single_value string>`               |
| ?         | Optional value      | `<optional_value string ?>`           |
| *         | Zero or more values | `<zero_or_more string *>`             |
| +         | One or more values  | `<one_or_more string +>`              |
| {N}       | N values            | `<three_values string {3}>`           |
| {min,max} | min <= N <= max     | `<three_to_five_values string {3,5}>` |

BugBug: List of lists

Reference Elements
==================
[Return to Top](#SimpleSchema)

BugBug

Miscellaneous Elements
==================
[Return to Top](#SimpleSchema)

BugBug: Variant
BugBug: List
BugBug: Any
BugBug: Custom
BugBug: Extension

Miscellaneous Statements
========================
[Return to Top](#SimpleSchema)

BugBug

Examples
========
[Return to Top](#SimpleSchema)

BugBug: Todo example
