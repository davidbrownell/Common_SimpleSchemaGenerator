# ----------------------------------------------------------------------
# |  
# |  Item.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 14:40:07
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Item object"""

import copy
import os

from collections import OrderedDict, namedtuple

from enum import Enum
import six

import CommonEnvironment
from CommonEnvironment.Interface import Interface, abstractmethod

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..Attributes import AttributeInfo
    from ..Elements import *
    
# ----------------------------------------------------------------------
ANY_ELEMENT_NAME                            = "any"
CUSTOM_ELEMENT_NAME                         = "custom"

# ----------------------------------------------------------------------
class MetadataSource(Enum):
    Explicit = 1
    Config = 2
    Default = 3
        
# ----------------------------------------------------------------------    
MetadataValue                               = namedtuple( "MetadataValue",
                                                          [ "Value",
                                                            "MetadataSource",
                                                            "Source",
                                                            "Line",
                                                            "Column",
                                                          ],
                                                        )

# ----------------------------------------------------------------------
Metadata                                    = namedtuple( "Metadata",
                                                          [ "Values",
                                                            "Source",
                                                            "Line",
                                                            "Column",
                                                          ],
                                                        )
    
# ----------------------------------------------------------------------
class ResolvedMetadata(object):
    """Metadata values and metadata info"""

    # ----------------------------------------------------------------------
    def __init__( self,
                  values,
                  required_items,
                  optional_items,
                ):
        self.Values                         = values
        self.RequiredItems                  = required_items
        self.OptionalItems                  = optional_items

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    def Clone(self, merge_metadata_or_attributes=None):
        """Clones the current item, optionally merging it with the provided info"""

        values = copy.deepcopy(self.Values)
        required_items = copy.deepcopy(self.RequiredItems)
        optional_items = copy.deepcopy(self.OptionalItems)

        if merge_metadata_or_attributes:
            if isinstance(merge_metadata_or_attributes, ResolvedMetadata):
                merge_metadata = merge_metadata_or_attributes
            
                for k, v in six.iteritems(merge_metadata.Values):
                    if k not in values:
                        values[k] = v

                ri_names = set(md.Name for md in required_items)
                oi_names = set(md.Name for md in optional_items)

                for md in merge_metadata.RequiredItems:
                    if md.Name not in ri_names:
                        required_items.append(md)

                for md in merge_metadata.OptionalItems:
                    if md.Name not in oi_names:
                        optional_items.append(md)
            
            elif isinstance(merge_metadata_or_attributes, AttributeInfo):
                attributes = merge_metadata_or_attributes

                required_items += attributes.RequiredItems
                optional_items += attributes.OptionalItems

            else:
                assert False, merge_metadata_or_attributes

        return self.__class__( values,
                               required_items,
                               optional_items,
                             )

# ----------------------------------------------------------------------
class Item(object):
    """Temporary object that is generated by Populate and consumed by Transform"""

    # ----------------------------------------------------------------------
    # |  Public Types
    class DeclarationType(Enum):
        Object = 1
        Declaration = 2
        Extension = 3

    class ItemType(Enum):
        Standard = 1
        Attribute = 2
        Definition = 3

    # ----------------------------------------------------------------------
    def __init__( self,
                  declaration_type,
                  item_type,
                  parent,
                  source,
                  line,
                  column,
                  is_external,              # True if the item is defined in another file
                ):
        # Populated during Populate
        self.DeclarationType                = declaration_type
        self.ItemType                       = item_type
        self.Parent                         = parent
        self.Source                         = source
        self.Line                           = line
        self.Column                         = column
        self.IsExternal                     = is_external

        self.name                           = None
        self.reference                      = None
        
        self.metadata                       = None
        self.arity                          = None
        
        self.items                          = []
        self.is_converted                   = False                         # Only used for SimpleElements that were converted to CompoundElements
        self.is_augmenting_reference        = False                         # Only used for ReferenceElements that modify the referenced type
        self.positional_arguments           = []                            # Only used for extensions
        self.keyword_arguments              = OrderedDict()                 # Only used for extensions
        self.ignore                         = False                         # Only used for extensions that are not supported
        
        # Populated during Resolve
        self.referenced_by                  = []
        self.element_type                   = None
        
        self._cached_key                    = None

    # ----------------------------------------------------------------------
    @property
    def Key(self):
        if self._cached_key is None:
            names = []

            item = self
            while item:
                names.append(item.name)
                item = item.Parent

            # Don't include the root element
            names = names[:-1]
            names.reverse()

            self._cached_key = tuple(names)

        return self._cached_key
            
    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    def Enumerate(self, variant_includes_self=False):
        if self.element_type == VariantElement:
            if variant_includes_self:
                yield self

            for item in self.reference:
                yield item
        else:
            yield self

# ----------------------------------------------------------------------
class ItemVisitor(Interface):
    """Visitor for Item objects based on element_type"""

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnFundamental(item, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnCompound(item, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnSimple(item, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnAny(item, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnCustom(item, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnVariant(item, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnExtension(item, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnReference(item, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnList(item, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def Accept(cls, item, *args, **kwargs):
        """Calls the appropriate On___ method based on the item's element_type value"""

        lookup = { FundamentalElement       : cls.OnFundamental,
                   CompoundElement          : cls.OnCompound,
                   SimpleElement            : cls.OnSimple,
                   AnyElement               : cls.OnAny,
                   CustomElement            : cls.OnCustom,
                   VariantElement           : cls.OnVariant,
                   ExtensionElement         : cls.OnExtension,
                   ReferenceElement         : cls.OnReference,
                   ListElement              : cls.OnList,
                 }

        if item.element_type not in lookup:
            raise Exception("'{}' was not expected".format(item.element_type))

        return lookup[item.element_type](item, *args, **kwargs)
