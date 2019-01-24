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
    class DestinationStatementWriter(PythonSerializationImpl.DestinationStatementWriter):
        # ----------------------------------------------------------------------
        @classmethod
        @Interface.override
        def CreateCompoundElement(cls, element, attributes_var_or_none):
            return textwrap.dedent(
                """\
                cls._CreateElement(
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
                cls._CreateElement(
                    {name},
                    attributes={attributes},
                    text_value={fundamental}, # BugBug: SHould this value be converted to a string?
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
                cls._CreateElement(
                    {name},
                    text_value={statement},
                )
                """,
            ).format(
                name=cls.GetElementStatementName(element),
                statement=fundamental_statement,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.override
        def AppendChild(child_element, parent_var_name, var_name_or_none):
            if var_name_or_none is None:
                return "BugBug: None var_name"

            return "{parent_var_name}.append({var_name})".format(
                parent_var_name=parent_var_name,
                var_name=var_name_or_none,
            )
            
        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.override
        def GetUtilityMethods(source_writer):
            return textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @staticmethod
                def _CreateElement(
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

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.override
    def _WriteFileHeader(output_stream):
        output_stream.write(
            textwrap.dedent(
                """\
                import sys
                import xml.etree.ElementTree as ET

                from collections import OrderedDict

                import six

                import CommonEnvironment
                from CommonEnvironment.TypeInfo import Arity, ValidationException
                from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
                from CommonEnvironment.TypeInfo.ClassTypeInfo import ClassTypeInfo
                from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo
                from CommonEnvironment.TypeInfo.GenericTypeInfo import GenericTypeInfo
                from CommonEnvironment.TypeInfo.ListTypeInfo import ListTypeInfo

                from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

                """,
            )
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _WriteFileFooter(output_stream):
        # Nothing to do here
        pass
