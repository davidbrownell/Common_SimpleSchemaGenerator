# ----------------------------------------------------------------------
# |
# |  JsonSchemaPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-18 15:37:25
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import json
import os

from collections import OrderedDict

import six

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment import RegularExpression
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import RegularExpressionVisitor
from CommonEnvironment.TypeInfo.FundamentalTypes.Visitor import Visitor as FundamentalTypeInfoVisitor

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

with InitRelativeImports():
    from ..Plugin import Plugin as PluginBase, ParseFlag
    from ..Schema import Elements

# <parameters differ from overridden method> pylint: disable=W0221

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(PluginBase):
    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                                                    = Interface.DerivedProperty("JsonSchema")
    Description                                                             = Interface.DerivedProperty(
        "Generates a JSON Schema file (https://json-schema.org/)",
    )
    Flags                                                                   = Interface.DerivedProperty(
        # ParseFlag.SupportAttributes
        ParseFlag.SupportIncludeStatements
        # | ParseFlag.SupportConfigStatements
        # | ParseFlag.SupportExtensionsStatements
        # | ParseFlag.SupportUnnamedDeclarations
        # | ParseFlag.SupportUnnamedObjects
        | ParseFlag.SupportNamedDeclarations
        | ParseFlag.SupportNamedObjects
        | ParseFlag.SupportRootDeclarations
        | ParseFlag.SupportRootObjects
        | ParseFlag.SupportChildDeclarations
        | ParseFlag.SupportChildObjects
        # | ParseFlag.SupportCustomElements
        | ParseFlag.SupportAnyElements
        | ParseFlag.SupportReferenceElements
        | ParseFlag.SupportListElements
        # | ParseFlag.SupportSimpleObjectElements
        | ParseFlag.SupportVariantElements
        | ParseFlag.ResolveReferences,
    )

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.override
    def IsValidEnvironment():
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GenerateCustomSettingsAndDefaults():
        yield "id", None
        yield "description", None
        yield "schema_version", "http://json-schema.org/draft-07/schema#"

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GenerateOutputFilenames(cls, context):
        return ["{}.schema.json".format(context["output_name"])]

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def Generate(
        cls,
        simple_schema_generator,
        invoke_reason,
        input_filenames,
        output_filenames,
        name,
        elements,
        include_indexes,
        status_stream,
        verbose_stream,
        verbose,
        id,
        description,
        schema_version,
    ):
        assert len(output_filenames) == 1
        output_filename = output_filenames[0]
        del output_filenames

        include_map = cls._GenerateIncludeMap(elements, include_indexes)
        include_dotted_names = set(six.iterkeys(include_map))

        top_level_elements = [element for element in elements if element.Parent is None and element.DottedName in include_map]

        # ----------------------------------------------------------------------
        def CreateDefinitions():
            definitions_schema = {}

            # ----------------------------------------------------------------------
            class Visitor(Elements.ElementVisitor):
                # ----------------------------------------------------------------------
                @staticmethod
                @Interface.override
                def OnExitingElement(element):
                    definitions_schema["_{}".format(element.DottedName)] = cls._Collectionize(
                        element.TypeInfo.Arity,
                        {"$ref": "#/definitions/_{}_Item".format(element.DottedName)},
                    )

                # ----------------------------------------------------------------------
                @staticmethod
                @Interface.override
                def OnFundamental(element):
                    definitions_schema["_{}_Item".format(element.DottedName)] = _FundamentalTypeInfoVisitor.Accept(
                        element.TypeInfo,
                    )

                # ----------------------------------------------------------------------
                @staticmethod
                @Interface.override
                def OnCompound(element):
                    properties = OrderedDict()
                    required = []

                    for child in cls._EnumerateChildren(element):
                        properties[child.Name] = {"$ref": "#/definitions/_{}".format(child.Resolve().DottedName)}

                        if child.TypeInfo.Arity.Min != 0:
                            required.append(child.Name)

                    schema = {
                        "type": "object",
                        "properties": properties,
                    }

                    if required:
                        required.sort()
                        schema["required"] = required

                    definitions_schema["_{}_Item".format(element.DottedName)] = schema

                # ----------------------------------------------------------------------
                @staticmethod
                @Interface.override
                def OnSimple(element):
                    raise Exception("SimpleElements are not supported")

                # ----------------------------------------------------------------------
                @classmethod
                @Interface.override
                def OnVariant(this_cls, element):
                    any_of_options = []

                    for variation in element.Variations:
                        assert variation.TypeInfo.Arity.IsSingle

                        if not isinstance(variation, Elements.ReferenceElement):
                            assert isinstance(variation, Elements.FundamentalElement), variation
                            definitions_schema["_{}_Item".format(variation.DottedName)] = _FundamentalTypeInfoVisitor.Accept(
                                variation.TypeInfo,
                            )

                        any_of_options.append(
                            {"$ref": "#/definitions/_{}_Item".format(variation.Resolve().DottedName)},
                        )

                    definitions_schema["_{}_Item".format(element.DottedName)] = {"anyOf": any_of_options}

                # ----------------------------------------------------------------------
                @staticmethod
                @Interface.override
                def OnReference(element):
                    # References don't need to be added, as they will be resolved inline.
                    pass

                # ----------------------------------------------------------------------
                @staticmethod
                @Interface.override
                def OnList(element):
                    definitions_schema["_{}_Item".format(element.DottedName)] = {"$ref": "#/definitions/_{}".format(element.Reference.Resolve().DottedName)}

                # ----------------------------------------------------------------------
                @staticmethod
                @Interface.override
                def OnAny(element):
                    definitions_schema["_{}_Item".format(element.DottedName)] = {} # Empty schema

                # ----------------------------------------------------------------------
                @staticmethod
                @Interface.override
                def OnCustom(element):
                    raise Exception("CustomElements are not supported")

                # ----------------------------------------------------------------------
                @staticmethod
                @Interface.override
                def OnExtension(element):
                    raise Exception("ExtensionElements are not supported")

            # ----------------------------------------------------------------------

            Visitor().Accept(
                elements,
                include_dotted_names=include_dotted_names,
            )

            return definitions_schema

        # ----------------------------------------------------------------------
        def CreateElements():
            schema = {}

            for element in top_level_elements:
                if element.IsDefinitionOnly:
                    continue

                schema[element.DottedName] = {"$ref": "#/definitions/_{}".format(element.Resolve().DottedName)}

            return schema

        # ----------------------------------------------------------------------

        status_stream.write("Creating '{}'...".format(output_filename))
        with status_stream.DoneManager() as dm:
            schema = {
                "$schema": schema_version,
                "type": "object",
                "properties": CreateElements(),
                "definitions": CreateDefinitions(),
            }

            if id:
                schema["id"] = id

            if description:
                schema["description"] = description

            required = []

            for element in elements:
                if element.DottedName in include_dotted_names and not element.IsDefinitionOnly and element.TypeInfo.Arity.Min != 0:
                    required.append(element.Name)

            if required:
                required.sort()
                schema["required"] = required

            with open(output_filename, "w") as f:
                json.dump(
                    schema,
                    f,
                    indent=2,
                    separators=[", ", " : "],
                    sort_keys=True,
                )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _Collectionize(arity, schema):
        if arity.Max == 1:
            return schema

        schema = {
            "type": "array",
            "items": schema,
        }

        if arity.Min != 0:
            schema["minItems"] = arity.Min
        if arity.Max is not None:
            schema["maxItems"] = arity.Max

        return schema


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@Interface.staticderived
class _FundamentalTypeInfoVisitor(FundamentalTypeInfoVisitor):
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnBool(type_info):
        return {"type": "boolean"}

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnDateTime(type_info):
        return {
            "type": "string",
            "format": "date-time",
        }

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnDate(type_info):
        return {
            "type": "string",
            "pattern": "^{}$".format(
                RegularExpression.PythonToJavaScript(
                    RegularExpressionVisitor().Accept(type_info)[0],
                ),
            ),
        }

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnDirectory(type_info):
        return {
            "type": "string",
            "minLength": 1,
        }

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnDuration(type_info):
        return {
            "type": "string",
            "pattern": "^{}$".format(
                RegularExpression.PythonToJavaScript(
                    RegularExpressionVisitor().Accept(type_info)[0],
                ),
            ),
        }

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnEnum(type_info):
        return {"enum": type_info.Values}

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnFilename(type_info):
        return {
            "type": "string",
            "minLength": 1,
        }

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnFloat(type_info):
        result = {"type": "number"}

        for attribute, json_schema_key in [("Min", "minimum"), ("Max", "maximum")]:
            value = getattr(type_info, attribute)
            if value is not None:
                result[json_schema_key] = value

        return result

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnGuid(type_info):
        return {
            "type": "string",
            "pattern": "^{}$".format(
                RegularExpression.PythonToJavaScript(
                    RegularExpressionVisitor().Accept(type_info)[0],
                ),
            ),
        }

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnInt(type_info):
        result = {"type": "integer"}

        for attribute, json_schema_key in [("Min", "minimum"), ("Max", "maximum")]:
            value = getattr(type_info, attribute)
            if value is not None:
                result[json_schema_key] = value

        return result

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnString(type_info):
        result = {"type": "string"}

        if type_info.ValidationExpression is not None:
            validation = RegularExpression.PythonToJavaScript(type_info.ValidationExpression)

            if validation[0] != "^":
                validation = "^{}".format(validation)
            if validation[-1] != "$":
                validation = "{}$".format(validation)

            result["pattern"] = validation

        else:
            if type_info.MinLength not in [0, None]:
                result["minLength"] = type_info.MinLength
            if type_info.MaxLength:
                result["maxLength"] = type_info.MaxLength

        return result

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnTime(type_info):
        return {
            "type": "string",
            "pattern": "^{}$".format(
                RegularExpression.PythonToJavaScript(
                    RegularExpressionVisitor().Accept(type_info)[0],
                ),
            ),
        }

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnUri(type_info):
        return {
            "type": "string",
            "pattern": "^{}$".format(
                RegularExpression.PythonToJavaScript(
                    RegularExpressionVisitor().Accept(type_info)[0],
                ),
            ),
        }
