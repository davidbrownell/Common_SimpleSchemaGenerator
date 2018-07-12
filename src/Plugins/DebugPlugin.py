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

from CommonEnvironmentEx.CompilerImpl.GeneratorPluginFrameworkImpl.PluginBase import PluginBase

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class Plugin(PluginBase):

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = "Debug"
    Description                             = "Displays diagnostic information"

    # ----------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def IsValidEnvironment():
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    def GenerateCustomSettingsAndDefaults():
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    def GenerateOutputFilenames(context):
        # Return a single item (that will never be used), as an empty lists
        # aren't supported.
        return [ "placeholder", ]

