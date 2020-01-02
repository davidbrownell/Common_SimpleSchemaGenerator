# ----------------------------------------------------------------------
# |
# |  Build.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-10 13:07:54
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Builds functionality necessary for Integration test execution"""

import os
import sys

import CommonEnvironment
from CommonEnvironment import BuildImpl
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


@CommandLine.EntryPoint
@CommandLine.Constraints(
    output_stream=None,
)
def Build(
    force=False,
    output_stream=sys.stdout,
    verbose=False,
):
    """Builds components used for Integration tests"""

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        command_line_template = '{script} Generate {{plugin}} {{schema}} "{{output_dir}}" /input="{{input_filename}}" /output_data_filename_prefix={{plugin}} /filter_unsupported_attributes{force}{verbose}'.format(
            script=CurrentShell.CreateScriptName("SimpleSchemaGenerator"),
            force=" /force" if force else "",
            verbose=" /verbose" if verbose else "",
        )

        schema_names = [
            "AllowAdditionalChildren.SimpleSchema",
            ("AllTypes.SimpleSchema", " /include=types"),
            "FileSystemTest.SimpleSchema",
            "Test.SimpleSchema",
            "DefaultValues.SimpleSchema",
        ]

        plugin_names = [
            "PythonJson",
            "PythonXml",
            "PythonYaml",
            "JsonSchema",
            "XsdSchema",
        ]

        for schema_name_index, schema_name in enumerate(schema_names):
            schema_flags = ""

            if isinstance(schema_name, tuple):
                schema_name, schema_flags = schema_name

            dm.stream.write("Processing '{}' ({} of {})...".format(schema_name, schema_name_index + 1, len(schema_names)))
            with dm.stream.DoneManager(
                suffix="\n",
            ) as schema_dm:
                schema_basename = os.path.splitext(schema_name)[0]

                output_dir = os.path.join(_script_dir, "Generated", schema_basename)

                schema_name = os.path.join(_script_dir, "..", "Impl", schema_name)
                assert os.path.isfile(schema_name), schema_name

                for plugin_index, plugin_name in enumerate(plugin_names):
                    schema_dm.stream.write("Plugin '{}' ({} of {})...".format(plugin_name, plugin_index + 1, len(plugin_names)))
                    with schema_dm.stream.DoneManager(
                        suffix="\n" if verbose else None,
                    ) as plugin_dm:
                        command_line = command_line_template.format(
                            plugin=plugin_name,
                            schema=schema_basename,
                            output_dir=output_dir,
                            input_filename=schema_name,
                        )

                        if plugin_name.endswith("Schema"):
                            command_line += schema_flags

                        plugin_dm.result, output = Process.Execute(command_line)
                        if plugin_dm.result != 0 or verbose:
                            plugin_dm.stream.write(output)

        return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    output_stream=None,
)
def Clean(
    output_stream=sys.stdout,
):
    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        output_dir = os.path.join(_script_dir, "Generated")

        if not os.path.isdir(output_dir):
            dm.stream.write("The output directory does not exist.\n")
        else:
            dm.stream.write("Removing '{}'...".format(output_dir))
            with dm.stream.DoneManager():
                FileSystem.RemoveTree(output_dir)

        return dm.result


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            BuildImpl.Main(
                BuildImpl.Configuration(
                    name="SimpleSchemaGenerator_Grammar_Build",
                    requires_output_dir=False,
                    priority=1,
                ),
            ),
        )
    except KeyboardInterrupt:
        pass
