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
        return 'cls._GetPythonAttribute({}, "{}")'.format(var_name, cls.GetElementStatementName(child_element))

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GetFundamentalString(var_name, child_element, is_attribute):
        return "BugBug: PythonSource-GetFundamentalString"

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

            for k, v in six.iteritems(source):
                if k.startswith("_") or k in exclude_names:
                    continue

                # BugBug: Handle lists

                if isinstance(v, dict):
                    child = {create_compound_element_statement}

                    cls._ApplyAdditionalData(
                        v,
                        child,
                        exclude_names=exclude_names,
                    )

                    v = child
                else:
                    v = {create_fundamental_element_statement}

                {append_statement}
            """,
        ).format(
            create_compound_element_statement=StringHelpers.LeftJustify(
                dest_writer.CreateCompoundElement(temporary_element, None),
                8,
            ).strip(),
            create_fundamental_element_statement=StringHelpers.LeftJustify(
                dest_writer.CreateFundamentalElement(temporary_element, "str(v)"),
                8,
            ).strip(),
            append_statement=StringHelpers.LeftJustify(
                dest_writer.AppendChild(
                    dest_writer.CreateTemporaryElement(
                        "k",
                        is_collection=False,
                    ),
                    "dest",
                    "v",
                ),
                4,
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
            def _GetPythonAttribute(item, attribute_name):
                if isinstance(item, dict):
                    return item.get(attribute_name, DoesNotExist)

                return getattr(item, attribute_name, DoesNotExist)
            
            """,
        )
