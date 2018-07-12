# ----------------------------------------------------------------------
# |  
# |  Plugin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 16:28:46
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

from enum import IntFlag, auto

from CommonEnvironment.BitFlagEnum import BitFlagEnum, auto
from CommonEnvironment.Interface import *

from CommonEnvironmentEx.CompilerImpl.GeneratorPluginFrameworkImpl.PluginBase import PluginBase

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class ParseFlag(IntFlag):
    """Flags that communicate the capabilities of a parser"""

    SupportAttributes                       = auto()
    SupportIncludeStatements                = auto()
    SupportConfigStatements                 = auto()

    SupportUnnamedDeclarations              = auto()
    SupportUnnamedObjects                   = auto()
    SupportNamedDeclarations                = auto()
    SupportNamedObjects                     = auto()

    SupportRootDeclarations                 = auto()
    SupportRootObjects                      = auto()
    SupportChildDeclarations                = auto()
    SupportChildObjects                     = auto()

    SupportCustomTypes                      = auto()

    SupportAliases                          = auto()
    SupportLists                            = auto()
    SupportSimpleObjects                    = auto()
    SupportAnyElements                      = auto()
    SupportVariants                         = auto()

    # Parse behavior
    ResolveReferences                       = auto()

    LastFlagValue                           = auto()
    AllFlags                                = LastFlagValue - 1

    # Multi-bit flags
    SupportDeclarations                     = SupportUnnamedDeclarations | SupportNamedDeclarations
    SupportObjects                          = SupportUnnamedObjects | SupportNamedObjects
                
# ----------------------------------------------------------------------
class Plugin(PluginBase):
    """Abstract base class for SimpleSchema plugins"""

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    @abstractproperty
    def Flags(self):
        """Return the flags supported by this plugin"""
        raise Exception("Abstract Property")

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    def VerifyFlags(self):
        flags = self.Flags

        if flags & ParseFlag.SupportSimpleObjects and not flags & ParseFlag.SupportAttributes:
            raise Exception("Attributes are required by SimpleObjects")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetExtensions():
        """Return a list of supported extension names"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetRequiredMetadata(element_type, name, resolved_element_type):
        """Returns a list of metadata items for the provided element"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetOptionalMetadata(element_type, name, resolved_element_type):
        """Returns a list of optional metadata items for the provided element"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
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
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    # |  
    # |  Protected Methods
    # |  
    # ----------------------------------------------------------------------
    # BugBug