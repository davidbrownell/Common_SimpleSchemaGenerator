# ----------------------------------------------------------------------
# |
# |  DotPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-11-30 16:30:57
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import html
import os
import textwrap
from textwrap import indent

import six

import CommonEnvironment
from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..Plugin import Plugin as PluginBase, ParseFlag


# ----------------------------------------------------------------------
@staticderived
class Plugin(PluginBase):

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = DerivedProperty("Dot")
    Description                             = DerivedProperty("Generates a DOT file that contains all elements (https://en.wikipedia.org/wiki/DOT_(graph_description_language))")
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
        yield "no_attributes", False

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def GenerateOutputFilenames(context):
        return [os.path.join(context["output_dir"], "{}.gv".format(context["output_name"]))]


    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def Generate(
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
        no_attributes,
    ):
        assert len(output_filenames) == 1, output_filenames
        output_filename = output_filenames[0]

        common_input_prefix = FileSystem.GetCommonPath(*input_filenames)

        with open(output_filename, "w") as f:
            f.write(
                textwrap.dedent(
                    """\
                    digraph g {
                        graph [
                            rankdir = "LR"
                        ];
                    """,
                ),
            )

            indented_stream = StreamDecorator(
                f,
                line_prefix="    ",
            )

            # ----------------------------------------------------------------------
            def Impl(element):
                if element.IsDefinitionOnly:
                    element_type = "Definition"
                    style = "dashed"
                elif getattr(element, "IsAttribute", False):
                    element_type = "Attribute"
                    style = "rounded"
                else:
                    element_type = "Standard"
                    style = None

                type_info_type = element.TypeInfo.__class__.__name__

                indented_stream.write(
                    textwrap.dedent(
                        """\
                        "{dotted}" [
                            shape = rectangle
                            {style}
                            label = <
                              <table border="0">
                                <tr>
                                  <td align="left"><b>{name}</b></td>
                                  <td align="right">{element_type}<br align="right"/>{type_info}</td>
                                </tr>
                                <hr/>
                                <tr>
                                  <td colspan="2">{source} [{line}:{column}]</td>
                                </tr>
                                <hr/>
                                <tr>
                                  <td align="left">Arity:</td>
                                  <td align="right">{arity}</td>
                                </tr>
                        """,
                    ).format(
                        dotted=element.DottedName,
                        name=element.Name,
                        style="style = {}".format(style) if style else "",
                        element_type=element_type,
                        type_info=type_info_type,
                        source=FileSystem.TrimPath(element.Source, common_input_prefix),
                        line=element.Line,
                        column=element.Column,
                        arity=element.TypeInfo.Arity.ToString() or "1",
                    ),
                )

                if type_info_type != "ClassTypeInfo":
                    indented_stream.write(
                        StringHelpers.LeftJustify(
                            textwrap.dedent(
                                """\
                                <tr>
                                  <td align="left">Constraints:</td>
                                  <td align="right">{}</td>
                                </tr>
                                """,
                            ).format(
                                html.escape(element.TypeInfo.ConstraintsDesc),
                            ),
                            8,
                            skip_first_line=False,
                        ),
                    )

                if not no_attributes:
                    table_rows = []

                    for key, metadata_value in six.iteritems(element.Metadata.Values):
                        table_rows.append(
                            textwrap.dedent(
                                """\
                                <tr>
                                  <td align="left">{}:</td>
                                  <td align="right">{}</td>
                                </tr>
                                """,
                            ).format(
                                html.escape(key),
                                html.escape(metadata_value.Value),
                            ),
                        )

                    if table_rows:
                        indented_stream.write(
                            StringHelpers.LeftJustify(
                                textwrap.dedent(
                                    """\
                                    <hr/>
                                    {}
                                    """,
                                ).format("".join(table_rows)),
                                8,
                                skip_first_line=False,
                            ),
                        )

                indented_stream.write(
                    textwrap.dedent(
                        """\
                              </table>
                            >
                        ];
                        """,
                    ),
                )

                for child in getattr(element, "Children", []):
                    Impl(child)
                    indented_stream.write('"{}":f0 -> "{}":f0\n'.format(element.DottedName, child.DottedName))

            # ----------------------------------------------------------------------

            for element in elements:
                Impl(element)

            f.write("}\n")
