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

from CommonEnvironment.BitFlagEnum import BitFlagEnum, auto
from CommonEnvironment.Interface import *

from CommonEnvironmentEx.CompilerImpl.GeneratorPluginFrameworkImpl.PluginBase import PluginBase

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class ParseFlag(BigFlagEnum):
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

    SupportCustomElements                   = auto()
    SupportAnyElements                      = auto()
    SupportAliasElements                    = auto()
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

        if flags & ParseFlag.SupportSimpleObjects and not flags & ParseFlag.SupportAttributes:
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
        the presense of a specific metadata item).
        """

        # Terminate traversal for collections; this allows N-dimentation tensors.
        return item.arity and item.arity.IsCollection and ("refines_arity" not in item.metadata.Values or not item.metadata.Values["refines_arity"].Value)

    # BugBug # ----------------------------------------------------------------------
    # BugBug @staticmethod
    # BugBug @extensionmethod
    # BugBug def ResolveReferenceArity(item):
    # BugBug     """\
    # BugBug     Returns the arity for the provided reference item. Custom plugins may
    # BugBug     override this method to influence how references are resolved (for example,
    # BugBug     a plugin may not want to fully traverse a reference chain if one of those 
    # BugBug     references contains a special metadata value).
    # BugBug     """
    # BugBug 
    # BugBug     # Use the default behavior - walk the reference chain and return the first
    # BugBug     # valid arity encountered.
    # BugBug     return item.ResolveReferenceArity()
    # BugBug 
    # BugBug # ----------------------------------------------------------------------
    # BugBug @staticmethod
    # BugBug @extensionmethod
    # BugBug def ResolveReferenceMetadataInfo( item, 
    # BugBug                                   initial_metadata_info=None,
    # BugBug                                 ):
    # BugBug     """\
    # BugBug     Returns metadata for the provided reference item. Custom plugins may
    # BugBug     override this method to influence how references are resolved (for example,
    # BugBug     a plugin may not want to fuly traverse a reference chain if one of those
    # BugBug     references contains a special metadata value).
    # BugBug 
    # BugBug     Returns .Impl.Item.Item.ResolvedMetadata
    # BugBug     """
    # BugBug 
    # BugBug     # Use the default behavior - walk the reference chain and merge all metadata
    # BugBug     # encountered.
    # BugBug     return item.ResolveReferenceMetadata(initial_metadata_info)

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
    # BugBug