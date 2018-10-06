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

import copy
import itertools
import os
import sys

from collections import namedtuple

from enum import IntFlag, auto
import six

import CommonEnvironment
from CommonEnvironment.BitFlagEnum import BitFlagEnum, auto
from CommonEnvironment.Interface import *

from CommonEnvironmentEx.CompilerImpl.GeneratorPluginFrameworkImpl.PluginBase import PluginBase

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class ParseFlag(BitFlagEnum):
    """Flags that communicate the capabilities of a parser"""

    SupportAttributes                       = auto()
    SupportIncludeStatements                = auto()
    SupportConfigStatements                 = auto()
    SupportExtensionsStatements             = auto()
    
    SupportUnnamedDeclarations              = auto()
    SupportUnnamedObjects                   = auto()
    SupportNamedDeclarations                = auto()
    SupportNamedObjects                     = auto()

    SupportRootDeclarations                 = auto()
    SupportRootObjects                      = auto()
    SupportChildDeclarations                = auto()
    SupportChildObjects                     = auto()

    SupportCustomElements                   = auto()
    SupportAnyElements                      = auto()
    SupportReferenceElements                = auto()
    SupportSimpleObjectElements             = auto()
    SupportVariantElements                  = auto()
    
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
        
        if flags & ParseFlag.SupportSimpleObjectElements and not flags & ParseFlag.SupportAttributes:
            raise Exception("Attributes are required by SimpleObjects")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def GetExtensions():
        """Return a list of supported extension names"""

        # No extensions by default
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def BreaksReferenceChain(item):
        """\
        Return True to terminate reference chain traversal. Plugins may override
        this method to terminate reference traversal early (for example, based on
        the presence of a specific metadata item).
        """

        # Terminate traversal for collections unless "refines_arity" is set to True.
        # This allows for N-dimensional arrays.
        return item.arity and item.arity.IsCollection and ("refines_arity" not in item.metadata.Values or not item.metadata.Values["refines_arity"].Value)

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def GetRequiredMetadataItems(item):
        """Returns a list of metadata items for the provided item."""
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def GetOptionalMetadataItems(item):
        return []

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
    