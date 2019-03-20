# ----------------------------------------------------------------------
# |
# |  PythonDictionaryPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-06 16:20:47
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os
import textwrap

import six

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment import StringHelpers
from CommonEnvironment.TypeInfo.FundamentalTypes.EnumTypeInfo import EnumTypeInfo

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..Plugin import Plugin as PluginBase, ParseFlag
    from ..Schema import Elements

# ----------------------------------------------------------------------
@staticderived
class Plugin(PluginBase):

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = DerivedProperty("PyDictionary")
    Description                             = DerivedProperty(
        "Generates python source code that contains a dictionary with top-level enum schema elements that have corresponding friendly names",
    )
    Flags                                   = DerivedProperty(ParseFlag.AllFlags)

    # ----------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    @override
    def IsValidEnvironment():
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def GenerateCustomSettingsAndDefaults():
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def GenerateOutputFilenames(context):
        return ["{}_dict.py".format(context["output_name"])]

    # ----------------------------------------------------------------------
    @classmethod
    @override
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
        **custom_settings
    ):
        assert len(output_filenames) == 1, output_filenames
        output_filename = output_filenames[0]
        del output_filenames

        status_stream.write("Creating '{}'...".format(output_filename))
        with status_stream.DoneManager() as this_dm:
            with open(output_filename, "w") as f:
                f.write(
                    textwrap.dedent(
                        """\
                        {}
                        from collections import OrderedDict

                        """,
                    ).format(
                        cls._GenerateFileHeader(
                            prefix="# ",
                        ),
                    ),
                )

                nonlocals = CommonEnvironment.Nonlocals(
                    wrote_value=False,
                )

                # ----------------------------------------------------------------------
                def OnCompoundVisitingChildren(element, *args, **kwargs):   # <Unused argument> pylint: disable = W0613
                                                                            # Don't visit children
                    return False

                # ----------------------------------------------------------------------
                def OnSimpleVisitingChildren(element, *args, **kwargs):     # <Unused argument> pylint: disable = W0613
                                                                            # Don't visit children
                    return False

                # ----------------------------------------------------------------------
                def OnFundamental(element, *args, **kwargs):                # <Unused argument> pylint: disable = W0613
                    if not isinstance(element.TypeInfo, EnumTypeInfo):
                        return

                    if not element.TypeInfo.FriendlyValues:
                        return

                    name = element.Name
                    reversed_name = "{}_reversed".format(name)

                    prefix = "{} = OrderedDict".format(name)
                    reversed_prefix = "{} = OrderedDict".format(reversed_name)

                    f.write(
                        textwrap.dedent(
                            """\
                            {prefix}{assignments}

                            {name}_max_key_length = len(max({name}.keys(), len))
                            {name}_max_value_length = len(max({name}.values(), len))

                            {reversed_prefix}{reversed_assignments}

                            {reversed_name}_max_key_length = len(max({reversed_name}.keys(), len))
                            {reversed_name}_max_value_length = len(max({reversed_name}.values(), len))

                            """,
                        ).format(
                            prefix=prefix,
                            assignments=StringHelpers.LeftJustify(
                                "([ {}\n ])".format(
                                    "\n   ".join(
                                        ['( "{}", "{}" ),'.format(v, fv) for v, fv in six.moves.zip(element.TypeInfo.Values, element.TypeInfo.FriendlyValues)],
                                    ),
                                ),
                                len(prefix),
                            ),
                            name=name,
                            reversed_prefix=reversed_prefix,
                            reversed_assignments=StringHelpers.LeftJustify(
                                "([ {}\n ])".format(
                                    "\n   ".join(
                                        ['( "{}", "{}" ),'.format(fv, v) for v, fv in six.moves.zip(element.TypeInfo.Values, element.TypeInfo.FriendlyValues)],
                                    ),
                                ),
                                len(reversed_prefix),
                            ),
                            reversed_name=reversed_name,
                        ),
                    )

                    nonlocals.wrote_value = True

                # ----------------------------------------------------------------------

                simple_element_visitor = Elements.CreateElementVisitor(
                    on_fundamental_func=OnFundamental,
                    on_compound_visiting_children_func=OnCompoundVisitingChildren,
                    on_simple_visiting_children_func=OnSimpleVisitingChildren,
                )

                for include_index in include_indexes:
                    element = elements[include_index]

                    simple_element_visitor.Accept(element)

                if not nonlocals.wrote_value:
                    f.write("# No enum values with friendly names were found.\n")
