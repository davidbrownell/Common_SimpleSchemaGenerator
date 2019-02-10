# ----------------------------------------------------------------------
# |
# |  PythonXmlPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-20 09:46:11
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

import os
import textwrap

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment import StringHelpers

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

with InitRelativeImports():
    from .Impl.PythonSerializationImpl import PythonSerializationImpl

# ----------------------------------------------------------------------
@Interface.staticderived
@Interface.clsinit
class Plugin(PythonSerializationImpl):

    COLLECTION_ITEM_NAME                    = "item"

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                                                                       = Interface.DerivedProperty("PythonXml")
    Description                                                                                = Interface.DerivedProperty(
        "Creates Python code that is able to serialize and deserialize python objects to Xml",
    )

    # ----------------------------------------------------------------------
    # |  Methods
    @classmethod
    @Interface.override
    def GetAdditionalGeneratorItems(cls, context):
        return [_script_fullpath] + super(Plugin, cls).GetAdditionalGeneratorItems(context)

    # ----------------------------------------------------------------------
    # |  Private Types
    @Interface.staticderived
    class SourceStatementWriter(PythonSerializationImpl.SourceStatementWriter):
        ObjectTypeDesc                      = Interface.DerivedProperty("an XML object (ElementTree)")

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.override
        def ConvenienceConversions(var_name, element):
            return textwrap.dedent(
                """\
                if isinstance({var_name}, six.string_types):
                    if os.path.isfile({var_name}):
                        with open({var_name}) as f:
                            {var_name} = f.read()

                    {var_name} = ET.fromstring({var_name})

                potential_child = _GetXmlElement(
                    {var_name},
                    "{name}",
                    is_optional={is_optional},
                    is_collection={is_collection},
                )
                if potential_child is not DoesNotExist or is_root:
                    {var_name} = potential_child

                """,
            ).format(
                var_name=var_name,
                name=element.Name,
                is_optional=element.TypeInfo.Arity.Min == 0,
                is_collection=element.TypeInfo.Arity.IsCollection,
            )

        # ----------------------------------------------------------------------
        @classmethod
        @Interface.override
        def GetChild(
            cls,
            var_name,
            child_element,
            is_simple_schema_fundamental=False,
        ):
            if is_simple_schema_fundamental:
                return '{var_name}.text if {var_name}.text.strip() else ""'.format(
                    var_name=var_name,
                )

            if getattr(child_element, "IsAttribute", False):
                return textwrap.dedent(
                    """\
                    cls._GetXmlAttribute(
                        {var_name},
                        {name},
                        is_optional={is_optional},
                    )
                    """,
                ).format(
                    var_name=var_name,
                    name=cls.GetElementStatementName(child_element),
                    is_optional=child_element.TypeInfo.Arity.Min == 0,
                )

            return textwrap.dedent(
                """\
                _GetXmlElement(
                    {var_name},
                    {name},
                    is_optional={is_optional},
                    is_collection={is_collection},
                )
                """,
            ).format(
                var_name=var_name,
                name=cls.GetElementStatementName(child_element),
                is_optional=child_element.TypeInfo.Arity.Min == 0,
                is_collection=child_element.TypeInfo.Arity.IsCollection,
            )

        # ----------------------------------------------------------------------
        @classmethod
        @Interface.override
        def GetAdditionalDataChildren(cls):
            return "cls._GenerateAdditionalDataChildren(source, exclude_names)"

        # ----------------------------------------------------------------------
        @classmethod
        @Interface.override
        def CreateAdditionalDataItem(cls, dest_writer, name_var_name, source_var_name):
            temporary_element = cls.CreateTemporaryElement("{}.tag".format(source_var_name), "1")

            return textwrap.dedent(
                """\
                attributes = OrderedDict()

                for k, v in six.iteritems({source_var_name}.attrib):
                    if k.startswith("_"):
                        continue

                    attributes[k] = v

                if {source_var_name}.text and {source_var_name}.text.strip() and not {source_var_name}:
                    return {simple_element}

                result = {compound_statement}

                for child_name, child_or_children in cls._GenerateAdditionalDataChildren({source_var_name}, set()):
                    try:
                        if isinstance(child_or_children, list):
                            new_items = []

                            for index, child in enumerate(child_or_children):
                                try:
                                    new_items.append(cls._CreateAdditionalDataItem("{item_name}", child))
                                except:
                                    _DecorateActiveException("Index {{}}".format(index))

                            {append_children}
                        else:
                            new_item = cls._CreateAdditionalDataItem(child_name, child_or_children)

                            {append_child}
                    except:
                        _DecorateActiveException(child_name)

                return result

                """,
            ).format(
                source_var_name=source_var_name,
                item_name=Plugin.COLLECTION_ITEM_NAME,
                compound_statement=dest_writer.CreateCompoundElement(
                    temporary_element,
                    "attributes",
                ).strip(),
                simple_element=StringHelpers.LeftJustify(
                    dest_writer.CreateSimpleElement(
                        temporary_element,
                        "attributes",
                        "{}.text".format(source_var_name),
                    ),
                    4,
                ).strip(),
                append_children=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(
                        cls.CreateTemporaryElement("child_name", "+"),
                        "result",
                        "new_items",
                    ),
                    12,
                ).strip(),
                append_child=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(
                        cls.CreateTemporaryElement("child_name", "1"),
                        "result",
                        "new_item",
                    ),
                    8,
                ).strip(),
            )

        # ----------------------------------------------------------------------
        @classmethod
        @Interface.override
        def GetClassUtilityMethods(cls, dest_writer):
            return textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @staticmethod
                def _GetXmlAttribute(
                    element,
                    attribute_name,
                    is_optional=False,
                ):
                    value = element.attrib.get(attribute_name, DoesNotExist)
                    if value is DoesNotExist and not is_optional:
                        raise SerializeException("The attribute '{{}}' does not exist".format(attribute_name))

                    return value

                # ----------------------------------------------------------------------
                def _GenerateAdditionalDataChildren(element, exclude_names):
                    children = OrderedDict()

                    for child in element:
                        if child.tag.startswith("_") or child.tag in exclude_names:
                            continue

                        children.setdefault(child.tag, []).append(child)

                    for k, v in six.iteritems(children):
                        if len(v) == 1:
                            yield k, v[0]
                        else:
                            yield k, v

                """,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.override
        def GetGlobalUtilityMethods(dest_writer):
            return textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                def _GetXmlElement(
                    element,
                    child_name,
                    is_optional=False,
                    is_collection=False,
                ):
                    children = element.findall(child_name)
                    if not children:
                        if is_optional:
                            return DoesNotExist

                        raise SerializeException("No elements were found")
                    if len(children) != 1:
                        raise SerializeException("Multiple items were found ({{}})".format(len(children)))

                    result = children[0]

                    if is_collection:
                        result = result.findall("{collection_item_name}")

                    return result

                """,
            ).format(
                collection_item_name=Plugin.COLLECTION_ITEM_NAME,
            )

    # ----------------------------------------------------------------------
    @Interface.staticderived
    class DestinationStatementWriter(PythonSerializationImpl.DestinationStatementWriter):
        ObjectTypeDesc                      = Interface.DerivedProperty("an XML object (ElementTree)")

        # ----------------------------------------------------------------------
        @classmethod
        @Interface.override
        def CreateCompoundElement(cls, element, attributes_var_or_none):
            return textwrap.dedent(
                """\
                _CreateXmlElement(
                    {name},
                    attributes={attributes},
                )
                """,
            ).format(
                name=cls.GetElementStatementName(element),
                attributes=attributes_var_or_none or "None",
            )

        # ----------------------------------------------------------------------
        @classmethod
        @Interface.override
        def CreateSimpleElement(cls, element, attributes_var_or_none, fundamental_statement):
            return textwrap.dedent(
                """\
                _CreateXmlElement(
                    {name},
                    attributes={attributes},
                    text_value={fundamental},
                )
                """,
            ).format(
                name=cls.GetElementStatementName(element),
                attributes=attributes_var_or_none or "None",
                fundamental=fundamental_statement,
            )

        # ----------------------------------------------------------------------
        @classmethod
        @Interface.override
        def CreateFundamentalElement(cls, element, fundamental_statement):
            return textwrap.dedent(
                """\
                _CreateXmlElement(
                    {name},
                    text_value={statement},
                )
                """,
            ).format(
                name=cls.GetElementStatementName(element),
                statement=fundamental_statement,
            )

        # ----------------------------------------------------------------------
        @classmethod
        @Interface.override
        def AppendChild(cls, child_element, parent_var_name, var_name_or_none):
            if child_element.TypeInfo.Arity.IsCollection:
                return "{parent_var_name}.append(_CreateXmlCollection({element_name}, {var_name}))".format(
                    parent_var_name=parent_var_name,
                    element_name=cls.GetElementStatementName(child_element),
                    var_name=var_name_or_none,
                )
            elif var_name_or_none is None:
                var_name_or_none = "_CreateXmlElement({})".format(
                    cls.GetElementStatementName(child_element),
                )

            return "{parent_var_name}.append({var_name})".format(
                parent_var_name=parent_var_name,
                var_name=var_name_or_none,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.override
        def SerializeToString(var_name):
            return textwrap.dedent(
                """\
                ET.tostring(
                    _XmlPrettyPrint({var_name}) if pretty_print else {var_name},
                    encoding="utf-8",
                    method="xml",
                ).decode("utf-8")
                """,
            ).format(
                var_name=var_name,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.override
        def GetGlobalUtilityMethods(source_writer):
            return textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                def _CreateXmlElement(
                    element_name,
                    attributes=None,
                    text_value=None,
                ):
                    result = ET.Element(
                        element_name,
                        attrib=attributes or {{}},
                    )

                    if text_value is not None:
                        result.text = text_value

                    return result


                # ----------------------------------------------------------------------
                def _CreateXmlCollection(element_name, items_or_none):
                    result = _CreateXmlElement(element_name)

                    for item in (items_or_none or []):
                        item.tag = "{item_name}"
                        result.append(item)

                    return result


                # ----------------------------------------------------------------------
                def _XmlPrettyPrint(elem, level=0):
                    original = elem

                    i = "\\n" + level * "  "

                    if elem:
                        if not elem.text or not elem.text.strip():
                            elem.text = i + "  "
                        if not elem.tail or not elem.tail.strip():
                            elem.tail = i

                        for child in elem:
                            _XmlPrettyPrint(child, level + 1)

                        # <Using possibly undefined loop variable 'child'> pylint: disable = W0631
                        if not child.tail or not child.tail.strip():
                            child.tail = i
                    else:
                        if level and (not elem.tail or not elem.tail.strip()):
                            elem.tail = i

                    return original

                """,
            ).format(
                item_name=Plugin.COLLECTION_ITEM_NAME,
            )

    # ----------------------------------------------------------------------
    # |  Private Properties
    _SupportAttributes                      = Interface.DerivedProperty(True)
    _SupportAnyElements                     = Interface.DerivedProperty(True)
    _TypeInfoSerializationName              = Interface.DerivedProperty("StringSerialization")

    _SourceStatementWriter                  = Interface.DerivedProperty(SourceStatementWriter)
    _DestinationStatementWriter             = Interface.DerivedProperty(DestinationStatementWriter)

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.override
    def _WriteFileHeader(output_stream):
        output_stream.write(
            textwrap.dedent(
                """\
                import xml.etree.ElementTree as ET

                from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

                """,
            ),
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _WriteFileFooter(output_stream):
        # Nothing to do here
        pass
