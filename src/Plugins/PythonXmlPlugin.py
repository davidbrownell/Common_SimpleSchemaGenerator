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
        def GetApplyAdditionalData(cls, dest_writer):
            temp_element = cls.CreateTemporaryElement(
                "k",
                is_collection=False,
            )

            return textwrap.dedent(
                """\
                for k, v in six.iteritems(source.attrib):
                    if k.startswith("_") or k in exclude_names:
                        continue

                    {append_attribute}

                additional_data_items = {{}}

                for e in source:
                    if e.tag.startswith("_") or e.tag in exclude_names:
                        continue

                    try:
                        additional_data_items.setdefault(e.tag, []).append(cls._CreateAdditionalDataItem(e))
                    except:
                        frame_desc = e.tag

                        if e.tag in additional_data_items and additional_data_items[e.tag]:
                            frame_desc = "{{}} - Index {{}}".format(frame_desc, len(additional_data_items[e.tag]))

                        _DecorateActiveException(frame_desc)

                for k, v in six.iteritems(additional_data_items):
                    if len(v) == 1:
                        {append}
                    else:
                        {append_children}

                """,
            ).format(
                append_attribute=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(temp_element, "dest", "v"),
                    4,
                ).strip(),
                append=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(temp_element, "dest", "v[0]"),
                    8,
                ).strip(),
                append_children=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(
                        cls.CreateTemporaryElement(
                            "k",
                            is_collection=True,
                        ),
                        "dest",
                        "v",
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
                @classmethod
                def _CreateAdditionalDataItem(cls, element):
                    children = {{}}

                    for child in element:
                        try:
                            children.setdefault(child.tag, []).append(cls._CreateAdditionalDataItem(child))
                        except:
                            frame_desc = child.tag

                            if child.tag in children and children[child.tag]:
                                frame_desc = "{{}} - Index {{}}".format(frame_desc, len(children[child.tag]))

                            _DecorateActiveException(frame_desc)

                    if element.text.strip():
                        if "{text_key}" in children:
                            raise SerializeException("'{text_key}' is a child element and can't be used to store the element's text")

                        children["{text_key}"] = [element.text]

                    for k in six.iterkeys(element.attrib):
                        if k in children:
                            raise SerializeException("'{{}}' is a child element and can't be used to store an attribute with the same name".format(k))

                    result = {create}

                    for k, v in six.iteritems(children):
                        if len(v) == 1:
                            v = v[0]

                        {append}

                    return result

                """,
            ).format(
                create=StringHelpers.LeftJustify(
                    dest_writer.CreateCompoundElement(
                        cls.CreateTemporaryElement(
                            "result",
                            is_collection=False,
                        ),
                        "element.attrib",
                    ),
                    4,
                ).strip(),
                append=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(
                        cls.CreateTemporaryElement(
                            "k",
                            is_collection=False,
                        ),
                        "result",
                        "v",
                    ),
                    4,
                ).strip(),
                text_key=cls.SIMPLE_ELEMENT_FUNDAMENTAL_ATTRIBUTE_NAME,
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
                        attrib=attributes or {},
                    )

                    if text_value is not None:
                        result.text = text_value

                    return result


                # ----------------------------------------------------------------------
                def _CreateXmlCollection(element_name, items_or_none):
                    result = _CreateXmlElement(element_name)

                    for item in (items_or_none or []):
                        result.append(item)

                    return result


                # ----------------------------------------------------------------------
                def _XmlPrettyPrint(elem, level=0):
                    original = elem

                    i = "\\n" + level * "  "

                    if len(elem):
                        if not elem.text or not elem.text.strip():
                            elem.text = i + "  "
                        if not elem.tail or not elem.tail.strip():
                            elem.tail = i

                        for elem in elem:
                            _XmlPrettyPrint(elem, level + 1)

                        if not elem.tail or not elem.tail.strip():
                            elem.tail = i
                    else:
                        if level and (not elem.tail or not elem.tail.strip()):
                            elem.tail = i

                    return original

                """,
            )

    # ----------------------------------------------------------------------
    # |  Private Properties
    _SupportAttributes                      = Interface.DerivedProperty(True)
    _SupportAnyElements                     = Interface.DerivedProperty(True)
    _TypeInfoSerializationName              = Interface.DerivedProperty("StringSerialization")

    _DestinationStatementWriter             = Interface.DerivedProperty(DestinationStatementWriter)
    _SourceStatementWriter                  = Interface.DerivedProperty(SourceStatementWriter)

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.override
    def _WriteFileHeader(output_stream):
        output_stream.write(
            textwrap.dedent(
                """\
                import xml.etree.ElementTree as ET


                """,
            )
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _WriteFileFooter(output_stream):
        # Nothing to do here
        pass
