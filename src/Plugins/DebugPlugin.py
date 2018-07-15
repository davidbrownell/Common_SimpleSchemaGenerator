# ----------------------------------------------------------------------
# |  
# |  DebugPlugin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-06 16:20:47
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os
import sys

from CommonEnvironment.Interface import staticderived

from CommonEnvironmentEx.Package import ApplyRelativePackage

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with ApplyRelativePackage():
    from ..Plugin import Plugin as PluginBase, ParseFlag

# ----------------------------------------------------------------------
@staticderived
class Plugin(PluginBase):

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = "Debug"
    Description                             = "Displays diagnostic information about each element"
    Flags                                   = ParseFlag.AllFlags

    # ----------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def IsValidEnvironment():
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    def GenerateCustomSettingsAndDefaults():
        return [ ( "foo", 'BugBug' ), ]

    # ----------------------------------------------------------------------
    @staticmethod
    def GenerateOutputFilenames(context):
        # Return a single item (that will never be used), as an empty lists
        # aren't supported.
        return [ "placeholder", ]

    # ----------------------------------------------------------------------
    @staticmethod
    def Generate( simple_schema_code_generator,
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
            status_stream.write('\n\n')

        # ----------------------------------------------------------------------

        for include_index in include_indexes:
            Impl(elements[include_index])
