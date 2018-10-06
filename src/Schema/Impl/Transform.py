# ----------------------------------------------------------------------
# |  
# |  Transform.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-13 15:18:37
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Transforms Items into Element objects"""

import copy
import itertools
import os
import sys

from collections import OrderedDict

import six

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override
from CommonEnvironment.TypeInfo import Arity
from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
from CommonEnvironment.TypeInfo.ClassTypeInfo import ClassTypeInfo
from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from .Item import Item, ItemVisitor
    
    from .. import Elements
    from .. import Exceptions
    
    from ...Plugin import ParseFlag

# ----------------------------------------------------------------------
def Transform(root, plugin):
    lookup = {}

    # ----------------------------------------------------------------------
    def Create(item, use_cache=True):
        if ( not use_cache or
             item.Key not in lookup or
             (item.element_type == Elements.ExtensionElement and next(ext for ext in plugin.GetExtensions() if ext.Name == item.name).AllowDuplicates)
           ):
            # Signal that we are processing this item
            lookup[item.Key] = None

            # Create the element
            is_definition_only = item.ItemType == Item.ItemType.Definition

            element = _CreateElementVisitor().Accept( item, 
                                                      plugin, 
                                                      Create, 
                                                      is_definition_only,
                                                    )
            element._item = item

            if not use_cache:
                return element

            lookup[item.Key] = element

        assert item.Key in lookup, item.Key
        return lookup[item.Key]

    # ----------------------------------------------------------------------
    def Resolve(element, parent):
        """Depth first traversal; elements will only be traversed once."""

        # Apply changes to this element
        assert element.Parent is None, element.Parent
        element.Parent = parent

        if hasattr(element, "Reference"):
            assert element.Reference is None, element.Reference
            element.Reference = lookup[element._item.reference.Key]

        if hasattr(element, "Base") and element._item.reference:
            assert element.Base is None, element.Base
            element.Base = lookup[element._item.reference.Key]

        # Apply metadata
        element.Metadata = element._item.metadata
        element.AttributeNames = list(six.iterkeys(element._item.metadata.Values))

        for k, v in six.iteritems(element._item.metadata.Values):
            if hasattr(element, k):
                raise Exceptions.InvalidAttributeNameException( v.Source,
                                                                v.Line,
                                                                v.Column,
                                                                name=k,
                                                              )

            setattr(element, k, v.Value)

        # Traverse the children
        for child in getattr(element, "Children", []):
            Resolve(child, element)

    # ----------------------------------------------------------------------
    def ValidateMetadata(element):
        for md in itertools.chain( element._item.metadata.RequiredItems,
                                   element._item.metadata.OptionalItems,
                                 ):
            result = None

            if md.Name in element._item.metadata.Values:
                if md.ValidateFunc is not None:
                    result = md.ValidateFunc(plugin, element)
            elif md.Name not in element._item.metadata.Values:
                if md.MissingValidateFunc is not None:
                    result = md.MissingValidateFunc(plugin, element)

            if result is not None:
                raise Exceptions.InvalidAttributeException( element._item.metadata.Values[md.Name].Source,
                                                            element._item.metadata.Values[md.Name].Line,
                                                            element._item.metadata.Values[md.Name].Column,
                                                            desc=result,
                                                          )

    # ----------------------------------------------------------------------
    def Cleanup(element):
        del element._item
    
    # ----------------------------------------------------------------------
    def Impl(element, functor):
        functor(element)

        for child in getattr(element, "Children", []):
            Impl(child, functor)

    # ----------------------------------------------------------------------

    root_element = Create(root)

    Resolve(root_element, None)
    
    Impl(root_element, ValidateMetadata)
    Impl(root_element, Cleanup)

    return root_element

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@staticderived
class _CreateElementVisitor(ItemVisitor):
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnFundamental(cls, item, plugin, create_element_func, is_definition_only):
        return Elements.FundamentalElement( type_info=cls._CreateFundamentalTypeInfo(item, item.reference),
                                            is_attribute=item.ItemType == Item.ItemType.Attribute and (plugin.Flags & ParseFlag.SupportAttributes),
                                            
                                            original_name=item.original_name,
                                            name=item.name,
                                            parent=None,                    # Set later
                                            source=item.Source,
                                            line=item.Line,
                                            column=item.Column,
                                            is_definition_only=is_definition_only,
                                            is_external=item.IsExternal,
                                          )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnCompound(item, plugin, create_element_func, is_definition_only):
        return Elements.CompoundElement( arity=item.arity,
                                         children=[ create_element_func(child) for child in item.items ],
                                         base=None,                         # Set later
                                         
                                         original_name=item.original_name,
                                         name=item.name,
                                         parent=None,                       # Set later
                                         source=item.Source,
                                         line=item.Line,
                                         column=item.Column,
                                         is_definition_only=is_definition_only,
                                         is_external=item.IsExternal,
                                       )

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnSimple(cls, item, plugin, create_element_func, is_definition_only):
        return Elements.SimpleElement( fundamental_type_info=cls._CreateFundamentalTypeInfo(item, item.reference),
                                       arity=item.arity,
                                       children=[ create_element_func(child) for child in item.items ],
                                       
                                       original_name=item.original_name,
                                       name=item.name,
                                       parent=None,                         # Set later
                                       source=item.Source,
                                       line=item.Line,
                                       column=item.Column,
                                       is_definition_only=is_definition_only,
                                       is_external=item.IsExternal,
                                     )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnAny(item, plugin, create_element_func, is_definition_only):
        return Elements.AnyElement( arity=item.arity,
                                    
                                    original_name=item.original_name,
                                    name=item.name,
                                    parent=None,                            # Set later
                                    source=item.Source,
                                    line=item.Line,
                                    column=item.Column,
                                    is_definition_only=is_definition_only,
                                    is_external=item.IsExternal,
                                  )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnCustom(item, plugin, create_element_func, is_definition_only):
        return Elements.CustomElement( arity=item.arity,
            
                                       original_name=item.original_name,
                                       name=item.name,
                                       parent=None,                         # Set later
                                       source=item.Source,
                                       line=item.Line,
                                       column=item.Column,
                                       is_definition_only=is_definition_only,
                                       is_external=item.IsExternal,
                                     )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnVariant(item, plugin, create_element_func, is_definition_only):
        return Elements.VariantElement( arity=item.arity,
                                        variations=[ create_element_func(sub_item, use_cache=False) for sub_item in item.reference ],

                                        original_name=item.original_name,
                                        name=item.name,
                                        parent=None,                        # Set later
                                        source=item.Source,
                                        line=item.Line,
                                        column=item.Column,
                                        is_definition_only=is_definition_only,
                                        is_external=item.IsExternal,
                                      )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnExtension(item, plugin, create_element_func, is_definition_only):
        return Elements.ExtensionElement( arity=item.arity,
                                          positional_arguments=item.positional_arguments,
                                          keyword_arguments=item.keyword_arguments,

                                          original_name=item.original_name,
                                          name=item.name,
                                          parent=None,                      # Set later
                                          source=item.Source,
                                          line=item.Line,
                                          column=item.Column,
                                          is_definition_only=is_definition_only,
                                          is_external=item.IsExternal,
                                        )

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnReference(cls, item, plugin, create_element_func, is_definition_only):
        ref = item.reference
        while ref.element_type == Elements.ReferenceElement:
            ref = ref.reference

        if ref.element_type == Elements.FundamentalElement:
            type_info_or_arity = cls._CreateFundamentalTypeInfo(item, ref.reference)
        else:
            type_info_or_arity = item.arity
        
        return Elements.ReferenceElement( type_info_or_arity=type_info_or_arity,
                                          reference=None,                   # Set later

                                          original_name=item.original_name,
                                          name=item.name,
                                          parent=None,                      # Set later
                                          source=item.Source,
                                          line=item.Line,
                                          column=item.Column,
                                          is_definition_only=is_definition_only,
                                          is_external=item.IsExternal,
                                        )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _CreateFundamentalTypeInfo(item, fundamental_attributes_info):
        kwargs = { "arity" : item.arity,
                 }

        for md in itertools.chain( fundamental_attributes_info.RequiredItems,
                                   fundamental_attributes_info.OptionalItems,
                                 ):
            if md.Name in item.metadata.Values:
                kwargs[md.Name] = item.metadata.Values[md.Name].Value
                del item.metadata.Values[md.Name]

        type_info = fundamental_attributes_info.TypeInfoClass(**kwargs)

        return type_info
