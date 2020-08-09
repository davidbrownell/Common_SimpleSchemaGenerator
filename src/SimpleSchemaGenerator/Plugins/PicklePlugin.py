# ----------------------------------------------------------------------
# |
# |  PicklePlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-07-24 15:08:32
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
import pickle
import sys

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..Plugin import Plugin as PluginBase, ParseFlag, Extension

# ----------------------------------------------------------------------
@staticderived
class Plugin(PluginBase):

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = DerivedProperty("Pickle")
    Description                             = DerivedProperty("Pickles each element to a file")
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
        # Return a single item (that will never be used), as an empty lists
        # aren't supported.
        return ["{}.{}".format(context["output_name"], ext) for ext in ["pickle", "path"]]

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
        **custom_settings
    ):
        assert len(output_filenames) == 2, output_filenames

        # Pickle
        status_stream.write("Creating '{}'...".format(output_filenames[0]))
        with status_stream.DoneManager() as status_dm:
            with open(output_filenames[0], "wb") as f:
                pickle.dump(elements, f)

        # Path
        status_stream.write("Creating '{}'...".format(output_filenames[1]))
        with status_stream.DoneManager() as status_dm:
            generator_path = os.path.dirname(simple_schema_generator.OriginalModuleFilename)
            assert os.path.isdir(generator_path), generator_path

            generator_path = os.path.dirname(generator_path)

            with open(output_filenames[1], "w") as f:
                f.write(generator_path)
