# ----------------------------------------------------------------------
# |
# |  PythonSourceStatementWriter.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-25 16:13:01
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
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
#  ----------------------------------------------------------------------

with InitRelativeImports():
    from ..StatementWriters import SourceStatementWriter

# ----------------------------------------------------------------------
@Interface.staticderived
class PythonSourceStatementWriter(SourceStatementWriter):
    ObjectTypeDesc                          = Interface.DerivedProperty("a python object")

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def ConvenienceConversions(cls, var_name, element):
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
            name=element.Name,
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
    @classmethod
    @Interface.override
    def GetApplyAdditionalData(cls, dest_writer):
        temporary_element = dest_writer.CreateTemporaryElement(
            "k",
            is_collection=False,
        )

        return textwrap.dedent(
            """\
            if not isinstance(source, dict):
                source = source.__dict__

            additional_data_items = {{}}

            for k, v in six.iteritems(source):
                if k.startswith("_") or k in exclude_names:
                    continue

                try:
                    additional_data_items.setdefault(k, []).append(cls._CreateAdditionalDataItem(k, v))
                except:
                    frame_desc = k

                    if k in additional_data_items and additional_data_items[k]:
                        frame_desc = "{{}} - Index {{}}".format(frame_desc, len(additional_data_items[k]))

                    _DecorateActiveException(frame_desc)

            for k, v in six.iteritems(additional_data_items):
                if len(v) == 1:
                    {append}
                else:
                    {append_children}
            """,
        ).format(
            append=StringHelpers.LeftJustify(
                dest_writer.AppendChild(
                    cls.CreateTemporaryElement(
                        "k",
                        is_collection=False,
                    ),
                    "dest",
                    "v[0]",
                ),
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
        temp_element = cls.CreateTemporaryElement(
            "key",
            is_collection=False,
        )

        result_temp_element = cls.CreateTemporaryElement(
            "result",
            is_collection=False,
        )

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
                    item = item.__dict__

                value = item.get(attribute_name, DoesNotExist)
                if value is DoesNotExist and not is_optional:
                    raise SerializeException("No items were found")

                return value
            
            # ----------------------------------------------------------------------
            @classmethod
            def _CreateAdditionalDataItem(cls, key, element):
                if isinstance(element, six.string_types):
                    return {create_string_element}

                if isinstance(element, list):
                    result = {create_list_element}

                    for item_index, item in enumerate(element):
                        try:
                            {append_list_item}
                        except:
                            _DecorateActiveException("Index {{}}".format(key, item_index))

                    return result

                if not isinstance(element, dict):
                    element = element.__dict__

                if "{text_key}" in element:
                    attributes = {{}}
                    fundamental_value = None

                    for k, v in six.iteritems(element):
                        if k == "{text_key}":
                            fundamental_value = v
                        else:
                            if not isinstance(v, six.string_types):
                                raise SerializeException("SimpleElement attributes must by string values ({{}}: {{}})".format(k, v))

                            attributes[k] = v

                    return {create_simple_element}

                result = {create_compound_element}

                for k, v in six.iteritems(element):
                    try:
                        {append_standard_item}
                    except:
                        _DecorateActiveException(key)

                return result

            """,
        ).format(
            create_string_element=StringHelpers.LeftJustify(
                dest_writer.CreateSimpleElement(temp_element, None, "element"),
                8,
            ).strip(),
            create_list_element=StringHelpers.LeftJustify(
                dest_writer.CreateCompoundElement(temp_element, None),
                8,
            ).strip(),
            create_simple_element=StringHelpers.LeftJustify(
                dest_writer.CreateSimpleElement(
                    temp_element,
                    "attributes",
                    "fundamental_value",
                ),
                8,
            ).strip(),
            append_list_item=StringHelpers.LeftJustify(
                dest_writer.AppendChild(
                    result_temp_element,
                    "result",
                    'cls._CreateAdditionalDataItem("item", item)',
                ),
                16,
            ).strip(),
            append_standard_item=StringHelpers.LeftJustify(
                dest_writer.AppendChild(
                    result_temp_element,
                    "result",
                    "cls._CreateAdditionalDataItem(k, v)",
                ),
                8,
            ).strip(),
            create_compound_element=StringHelpers.LeftJustify(
                dest_writer.CreateCompoundElement(
                    temp_element,
                    None,
                ),
                4,
            ).strip(),
            text_key=cls.SIMPLE_ELEMENT_FUNDAMENTAL_ATTRIBUTE_NAME,
        )
