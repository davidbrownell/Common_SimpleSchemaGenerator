# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-25 16:07:00
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the StatementWriter, SourceStatementWriter, and DestinationStatementWriter objects"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from CommonEnvironment.TypeInfo.FundamentalTypes.StringTypeInfo import StringTypeInfo

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

with InitRelativeImports():
    from ....Schema import Attributes
    from ....Schema import Elements


# ----------------------------------------------------------------------
class StatementWriter(Interface.Interface):
    """Contains helper methods used by all StatementWriter objects."""

    SIMPLE_ELEMENT_FUNDAMENTAL_ATTRIBUTE_NAME           = "text_value__"

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def ObjectTypeDesc(self):
        """String description of the writer's object type used in docstrings"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    def GetElementStatementName(element):
        """\
        Returns a value that can be used within a statement
        to represent the name of an element.
        """

        if callable(element.Name):
            return element.Name()

        return '"{}"'.format(element.Name)

    # ----------------------------------------------------------------------
    @staticmethod
    def CreateTemporaryElement(
        name,
        is_collection,
        is_attribute=None,
    ):
        result = Elements.Element(
            StringTypeInfo(
                arity="*" if is_collection else "1",
            ),
            lambda: name,
            parent=None,
            source=None,
            line=None,
            column=None,
            is_definition_only=None,
            is_external=None,
        )

        if is_attribute is not None:
            result.IsAttribute = is_attribute

        return result


# ----------------------------------------------------------------------
class SourceStatementWriter(StatementWriter):
    """\
    Interface for components that are able to write python statements used when
    reading objects.
    """

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def ConvenienceConversions(var_name, element):
        """\
        Statements that convert from an input type to the source; used to create
        better experiences for callers. The generated code should return 
        `DoesNotExist` if the element was not found in the variable.

        Optional vars:
            is_root
        """
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def GetChild(
        var_name,
        child_element,
        is_simple_schema_fundamental=False,
    ):
        """\
        Gets the child_element from a variable. Implementing classes
        should account for attributes, collections, optional values, 
        and standard children in their implementations.
        """
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def GetApplyAdditionalData(dest_writer):
        """Creates the statements for the _ApplyAdditionalData method"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def GetClassUtilityMethods(dest_writer):
        """Returns any statements that should be written as class methods"""
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def GetGlobalUtilityMethods(dest_writer):
        """Returns any statements that should be written as global methods"""
        return None


# ----------------------------------------------------------------------
class DestinationStatementWriter(StatementWriter):
    """\
    Interface for components that are able to write python statements used when
    writing objects.
    """

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def CreateCompoundElement(element, attributes_var_or_none):
        """Creates a CompoundElement"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def CreateSimpleElement(element, attributes_var_or_none, fundamental_statement):
        """Creates a SimpleElement"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def CreateFundamentalElement(element, fundamental_statement):
        """Create a FundamentalElement"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def AppendChild(child_element, parent_var_name, var_name_or_none):
        """Appends a child to an existing CompoundElement"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def SerializeToString(var_name):
        """Returns a statement that converts the given var to a string"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def GetClassUtilityMethods(source_writer):
        """Returns any statements that should be written as class methods"""
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def GetGlobalUtilityMethods(source_writer):
        """Returns any statements that should be written as global methods"""
        return None
