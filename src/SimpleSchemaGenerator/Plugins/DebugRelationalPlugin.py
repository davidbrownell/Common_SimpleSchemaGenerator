# ----------------------------------------------------------------------
# |
# |  DebugRelationalPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-02-05 15:04:00
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
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

from CommonSimpleSchemaGenerator.RelationalPluginImpl import RelationalPluginImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(RelationalPluginImpl):
    # ----------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ----------------------------------------------------------------------
    Name                                    = Interface.DerivedProperty("DebugRelational")
    Description                             = Interface.DerivedProperty("Displays information associated with objects created by the base Relational plugin class")

    # ----------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetAdditionalGeneratorItems(cls, context):
        return super(Plugin, cls).GetAdditionalGeneratorItems(context) + [RelationalPluginImpl]

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GenerateOutputFilenames(
        cls,
        context,
        all_objects=None,
    ):
        return [os.path.join(context["output_dir"], "{}.txt".format(context["output_name"]))]

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
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
    ):
        with open(output_filenames[0], "w") as f:
            f.write(cls._GenerateFileHeader())

            for obj in cls.AllObjects:
                f.write(
                    textwrap.dedent(
                        """\
                        # ----------------------------------------------------------------------
                        # ----------------------------------------------------------------------
                        # ----------------------------------------------------------------------
                        Unique Name:        {unique}
                        Singular Name:      {singular}
                        Plural Name:        {plural}

                        """,
                    ).format(
                        unique=obj.UniqueName,
                        singular=obj.SingularName,
                        plural=obj.PluralName,
                    ),
                )

                for child in obj.children:
                    f.write(
                        textwrap.dedent(
                            """\
                            # ----------------------------------------------------------------------
                            {}
                            {}
                            """,
                        ).format(
                            child.Name,
                            child.Item,
                        ),
                    )

                f.write("\n")
