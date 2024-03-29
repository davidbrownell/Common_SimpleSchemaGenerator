# ----------------------------------------------------------------------
# |
# |  PythonSourceStatementWriter.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-25 16:13:01
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the PythonSourceStatementWriter object"""

import os
import textwrap

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment import StringHelpers

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..StatementWriters import SourceStatementWriter
    from .PythonStatementWriterMixin import PythonStatementWriterMixin

# ----------------------------------------------------------------------
@Interface.staticderived
class PythonSourceStatementWriter(SourceStatementWriter):
    ObjectTypeDesc                          = Interface.DerivedProperty("a python object")

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def ConvenienceConversions(cls, var_name, element_or_none):
        if element_or_none is None:
            return ""

        return textwrap.dedent(
            """\
            if not isinstance({var_name}, list):
                if isinstance({var_name}, dict) and "{name}" in {var_name}:
                    {var_name} = {var_name}["{name}"]
                elif not isinstance({var_name}, dict) and hasattr({var_name}, "{name}"):
                    {var_name} = getattr({var_name}, "{name}")
                elif is_root:
                    {var_name} = DoesNotExist
            """,
        ).format(
            var_name=var_name,
            name=element_or_none.Name,
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
            is_optional = False
        else:
            is_optional = child_element.TypeInfo.Arity.Min == 0

        return textwrap.dedent(
            """\
            cls._GetPythonAttribute(
                {var_name},
                {name},
                is_optional={is_optional},
            )
            """,
        ).format(
            var_name=var_name,
            name=cls.GetElementStatementName(child_element),
            is_optional=is_optional,
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GetFundamental(var_name, child_element):
        return var_name

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GetAdditionalDataChildren():
        return '[(k, v) for k, v in six.iteritems(source if isinstance(source, dict) else getattr(source, "__dict__", {})) if not k.startswith("_") and k not in exclude_names]'

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def CreateAdditionalDataItem(cls, dest_writer, name_var_name, source_var_name):
        temporary_element = cls.CreateTemporaryElement(name_var_name, "1")
        temporary_children_element = cls.CreateTemporaryElement("k", "+")

        return textwrap.dedent(
            """\
            # The following types should be returned directly without additional conversion
            if isinstance({source_var_name}, (int, float, str, bool)):
                return {source_var_name}

            assert not isinstance({source_var_name}, list), {source_var_name}

            if not isinstance({source_var_name}, dict):
                {source_var_name} = {source_var_name}.__dict__

            source_attribute_names = {source_var_name}.get("{attribute_names}", set())

            attributes = OrderedDict()
            items = OrderedDict()

            for k, v in six.iteritems(source):
                if k.startswith("_"):
                    continue

                if k in source_attribute_names:
                    attributes[k] = v
                else:
                    items[k] = v

            if len(items) == 1 and next(six.iterkeys(items)) == {source_var_name}.get("{fundamental_name}", None):
                return {simple_statement}

            result = {compound_statement}

            for k, v in six.iteritems(items):
                try:
                    if isinstance(v, list):
                        new_items = []

                        for index, child in enumerate(v):
                            try:
                                new_items.append(cls._CreateAdditionalDataItem("item", child))
                            except:
                                _DecorateActiveException("Index {{}}".format(index))

                        {append_children}
                    else:
                        new_item = cls._CreateAdditionalDataItem(k, v)

                        {append_child}
                except:
                    _DecorateActiveException(k)

            return result

            """,
        ).format(
            source_var_name=source_var_name,
            attribute_names=cls.ATTRIBUTES_ATTRIBUTE_NAME,
            fundamental_name=cls.SIMPLE_ELEMENT_FUNDAMENTAL_ATTRIBUTE_NAME,
            simple_statement=StringHelpers.LeftJustify(
                dest_writer.CreateSimpleElement(
                    temporary_element,
                    "attributes",
                    '{}[{}["{}"]]'.format(source_var_name, source_var_name, cls.SIMPLE_ELEMENT_FUNDAMENTAL_ATTRIBUTE_NAME),
                ),
                4,
            ).strip(),
            compound_statement=dest_writer.CreateCompoundElement(temporary_element, "attributes").strip(),
            append_children=StringHelpers.LeftJustify(
                dest_writer.AppendChild(temporary_children_element, "result", dest_writer.CreateCollection(temporary_children_element, "new_items")),
                12,
            ).strip(),
            append_child=StringHelpers.LeftJustify(dest_writer.AppendChild(cls.CreateTemporaryElement("k", "1"), "result", "new_item"), 8).strip(),
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetGlobalUtilityMethods(cls, dest_writer):
        return PythonStatementWriterMixin.GetGlobalUtilityMethods(cls.ATTRIBUTES_ATTRIBUTE_NAME)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetClassUtilityMethods(cls, dest_writer):
        return textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            @staticmethod
            def _GetPythonAttribute(
                item,
                attribute_name,
                is_optional=False,
            ):
                if not isinstance(item, dict):
                    if hasattr(item, "__dict__"):
                        item = item.__dict__
                    else:
                        item = {}

                value = item.get(attribute_name, DoesNotExist)
                if value is DoesNotExist and not is_optional:
                    raise SerializeException("No items were found")

                return value

            """,
        )
