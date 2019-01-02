# ----------------------------------------------------------------------
# |  
# |  Plugin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 16:28:46
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os

from collections import OrderedDict

from enum import Enum, auto

import CommonEnvironment
from CommonEnvironment.BitFlagEnum import BitFlagEnum
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.Interface import abstractproperty, abstractmethod, extensionmethod

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
    SupportListElements                     = auto()
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
class Extension(object):
    """
    Defines a value that can be specified in a SimpleSchema file that invokes custom processing by the Plugin.
    Extensions are written as functions with the SimpleSchema file and can include keyword and
    positional arguments.
    """

    # ----------------------------------------------------------------------
    def __init__( self, 
                  name, 
                  allow_duplicates=False,
                ):
        self.Name                           = name
        self.AllowDuplicates                = allow_duplicates

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

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
    def GetRequiredMetadataItems(item):
        """Returns a list of required metadata items for the provided item."""
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def GetOptionalMetadataItems(item):
        """Returns a list of optional metadata items for the provided item."""
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def GetExtensions():
        """Return a list of supported extension names"""
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
    class IncludeMapType(Enum):
        """Indicates why an element was part of an include map"""
        Standard                            = auto()    # The element was explicitly included
        Referenced                          = auto()    # The element was included because something that referenced it was included
        Parent                              = auto()    # The element was included because it is an ancestor of an element that was explicitly included

    class IncludeMapValue(object):
        
        # ----------------------------------------------------------------------
        def __init__(self, element, include_map_type):
            self.Element                    = element
            self.Type                       = include_map_type

        # ----------------------------------------------------------------------
        def __repr__(self):
            return CommonEnvironment.ObjectReprImpl(self)

    @classmethod
    def _GenerateIncludeMap(cls, elements, include_indexes):
        """
        Returns a map that contains all elements that have been explicitly included and
        the elements that it relies upon.

            { "<dotted type name>" : <include_map_value>, ... }
        """

        include_map = OrderedDict()
        stack = []

        # ----------------------------------------------------------------------
        def Impl(element, include_map_type):
            # Prevent infinite recursion when operating on structures that have
            # loops
            if element in stack:
                return

            dn = element.DottedName

            include_map_value = include_map.get(dn, None)
            if include_map_value is not None and include_map_value.Type == cls.IncludeMapType.Standard:
                return

            include_map[dn] = cls.IncludeMapValue(element, include_map_type)

            # Ensure that all ancestors are included
            parent = element.Parent
            while parent:
                pdn = parent.DottedName
                if pdn in include_map:
                    break

                include_map[pdn] = cls.IncludeMapValue(parent, cls.IncludeMapType.Parent)
                parent = parent.Parent

            # Ensure that all children are included
            stack.append(element)
            with CallOnExit(lambda: stack.pop()):
                for potential_item_name in [ "Children", "Base", "Derived", "Reference", ]:
                    potential_items = getattr(element, potential_item_name, None)
                    if potential_items is None:
                        continue

                    if not isinstance(potential_items, list):
                        potential_items = [ potential_items, ]

                    for item in potential_items:
                        Impl(item, cls.IncludeMapType.Referenced)

        # ----------------------------------------------------------------------

        for element in [ elements[include_index] for include_index in include_indexes ]:
            Impl(element, cls.IncludeMapType.Standard)

        return include_map
