# ----------------------------------------------------------------------
# |
# |  DebugPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-06 16:20:47
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty

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
    Name                                    = DerivedProperty("Debug")
    Description                             = DerivedProperty("Displays diagnostic information about each element")
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
        return ["placeholder"]

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
        # ----------------------------------------------------------------------
        def Impl(element):
            status_stream.write(str(element))
            status_stream.write("\n\n")

        # ----------------------------------------------------------------------

        for include_index in include_indexes:
            Impl(elements[include_index])
