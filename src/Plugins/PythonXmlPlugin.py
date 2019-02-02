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
                return '{}.text or ""'.format(var_name)

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
        @staticmethod
        @Interface.override
        def GetFundamentalString(var_name, child_element, is_attribute):
            return "BugBug: GetFundmaentalString"

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.override
        def GetApplyAdditionalData(dest_writer):
            return textwrap.dedent(
                """\
                pass # BugBug: GetApplyAdditionalData
                """,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.override
        def GetClassUtilityMethods(dest_writer):
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
                        raise SerializeException("The attribute '{}' does not exist".format(attribute_name))

                    return value

                """)

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
        
        # BugBug # ----------------------------------------------------------------------
        # BugBug @staticmethod
        # BugBug @Interface.override
        # BugBug def GetGlobalUtilityMethods(dest_writer):
        # BugBug     return None

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
        def CreateSimpleElement(
            cls,
            element,
            attributes_var_or_none,
            fundamental_statement,
        ):
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
            
            if var_name_or_none is None:
                var_name_or_none = "_CreateXmlElement({})".format(cls.GetElementStatementName(child_element))
            
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
                    {},
                    encoding="utf-8",
                    method="xml",
                    pretty_print=pretty_print,
                ).decode("utf-8")
                """).format(var_name)

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
                        attrib=attributes,
                    )

                    if text_value is not None:
                        result.text = text_value

                    return result
                """
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
