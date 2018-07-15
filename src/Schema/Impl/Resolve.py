# ----------------------------------------------------------------------
# |  
# |  Resolve.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-12 12:50:27
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Functionality that resolves references information assocaited with Items"""

import itertools
import os
import sys

from collections import OrderedDict

import six
import inflect as inflect_mod

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.Interface import staticderived
from CommonEnvironment.TypeInfo import Arity

from CommonEnvironmentEx.Package import ApplyRelativePackage

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with ApplyRelativePackage():
    from .Item import *
    from ..Elements import *
    from ..Exceptions import *
    from ..Metadata import *

# ----------------------------------------------------------------------
inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
def Resolve(root, plugin):
    # ----------------------------------------------------------------------
    def Impl(item, functor):
        functor(item)

        for child in item.items:
            functor(child)

    # ----------------------------------------------------------------------

    config_metadata = root.config.get(plugin.Name, [ {}, ])

    # Flatten the config metadata
    if len(config_metadata) > 1:
        dest_metadata = config_metadata[0]
        for metadata in config_metadata[1:]:
            for k, v in six.iteritems(metadata):
                if k not in dest_metadata:
                    dest_metadata[k] = v

    config_metadata = config_metadata[0]
    
    Impl(root, _ResolveReference)
    Impl(root, _ResolveElementType)
    Impl(root, lambda item: _ResolveArity(plugin, item))
    Impl(root, _ResolveName)
    Impl(root, lambda item: _ResolveMetadata_NonArity(plugin, config_metadata, item))
    Impl(root, _ResolveMetadata_Arity)
    Impl(root, _ResolveMetadata_Defaults)

    return root

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ResolveReference(item):
    """Convert string names into Items"""

    if item.reference is None:
        return

    # ----------------------------------------------------------------------
    def Impl(ref):
        assert isinstance(ref, six.string_types), ref
    
        if ref in FUNDAMENTAL_TYPE_INFO_MAP or ref in [ ANY_ELEMENT_NAME,
                                                        CUSTOM_ELEMENT_NAME,
                                                      ]:
            return ref
    
        name_parts = ref.split('.')
    
        i = item
        while i:
            query = i
    
            for name_part in name_parts:
                query = next((qi for qi in query.items if qi.name == name_part), None)
                if query is None:
                    break
    
            if query:
                query.referenced_by.append(item)
                return query
    
            # Try again at a higher level
            i = i .Parent
    
        raise ResolveInvalidReferenceException( item.Source,
                                                item.Line,
                                                item.Column,
                                                name=ref,
                                             )
    
    # ----------------------------------------------------------------------
    
    if isinstance(item.reference, list):
        new_items = []

        for var, var_metadata in item.reference:
            new_item = Item( Item.DeclarationType.Declaration,
                             Item.ItemType.Standard,
                             item,
                             item.Source,
                             item.Line,
                             item.Column,
                             item.IsExternal,
                           )

            new_item.reference = Impl(var)
            new_item.metadata = var_metadata
            new_item.arity = Arity(1)

            items.append(new_item)

        item.reference = new_items
    else:
        item.reference = Impl(item.reference)

# ----------------------------------------------------------------------
def _ResolveElementType(item):
    """Assign an element type for the item"""

    if isinstance(item.reference, list):
        item.element_type = VariantElement
        items = item.reference
    else:
        items = [ item, ]

    for item in items:
        if item.DeclarationType == Item.DeclarationType.Extension:
            element_type = ExtensionElement

        elif item.DeclarationType == Item.DeclarationType.Object:
            # If here, we are looking at a Compound or a Simple object. A Simple
            # object is one that ultimately references a fundamental type.

            # ----------------------------------------------------------------------
            def IsSimple():
                ref = item.reference
                while isinstance(ref, Item):
                    ref = ref.reference

                return isinstance(ref, FundamentalTypeInfo)

            # ----------------------------------------------------------------------

            element_type = SimpleElement if IsSimple() else CompoundElement

        elif item.DeclarationType == Item.DeclarationType.Declaration:
            assert item.reference is not None

            if isinstance(item.reference, Item):
                element_type = ReferenceElement
            
            elif isinstance(item.reference, six.string_types):
                if item.reference in FUNDAMENTAL_TYPE_INFO_MAP:
                    element_type = FundamentalElement
                    item.reference = FUNDAMENTAL_TYPE_INFO_MAP[item.reference]

                elif item.reference == ANY_ELEMENT_NAME:
                    element_type = AnyElement
                    item.reference = ANY_METADATA_INFO

                elif item.reference == CUSTOM_ELEMENT_NAME:
                    element_type = CustomElement
                    item.reference = CUSTOM_METADATA_INFO

                else:
                    assert False, item.reference

            else:
                assert False, item.reference

        else:
            assert False, item.DeclarationType

        item.element_type = element_type

# ----------------------------------------------------------------------
def _ResolveArity(plugin, item):
    if item.arity is not None:
        return

    if item.element_type == ReferenceElement and not plugin.BreakReferenceChain(item):
        _ResolveArity(plugin, item.reference)
        item.arity = item.reference.arity
    else:
        item.arity = Arity(1)

        if item.element_type == VariantElement:
            for var_item in item.reference:
                assert var_item.arity is None, var_item.arity
                var_item.arity = item.arity

# ----------------------------------------------------------------------
def _ResolveName(item):
    """Apply custom name info if provided by metadata"""

    # ----------------------------------------------------------------------
    def IsValidName(value):
        return bool(value)

    # ----------------------------------------------------------------------
    
    if NAME_OVERRIDE_METADATA_NAME in item.metadata.Values:
        metadata_value = item.metadata.Values[NAME_OVERRIDE_METADATA_NAME]
        if not IsValidName(metadata_value.Value):
            raise ResolveInvalidCustomNameException( metadata_value.Source,
                                                     metadata_value.Line,
                                                     metadata_value.Column,
                                                     name=metadata_value.Value,
                                                   )

        item.name = metadata_value.Value
        del item.metadata.Values[NAME_OVERRIDE_METADATA_NAME]

    item.original_name = item.name

    if item.arity.IsCollection:
        if PLURAL_METADATA_NAME in item.metadata.Values:
            metadata_value = item.metadata.Values[PLURAL_METADATA_NAME]
            if not IsValidName(metadata_value.Value):
                raise ResolveInvalidCustomNameException( metadata_value.Source,
                                                         metadata_value.Line,
                                                         metadata_value.Column,
                                                         name=metadata_value.Value,
                                                       )

            item.name = metadata_value.Value
            del item.metadata.Values[PLURAL_METADATA_NAME]

        else:
            item.name = inflect.plural(item.name)

# BugBug: Move functionality to validate
# BugBug # ----------------------------------------------------------------------
# BugBug def _ValidateVariant(item):
# BugBug     """Ensure that variants are constructed as expected"""
# BugBug 
# BugBug     if item.element_type != VariantElement:
# BugBug         return
# BugBug 
# BugBug     for var_item in item.reference:
# BugBug         while True:
# BugBug             if not var_item.Arity.IsSingle:
# BugBug                 raise ResolveInvalidVariantReferenceArityException( item.Source,
# BugBug                                                                     item.Line,
# BugBug                                                                     item.Column,
# BugBug                                                                     ref_source=var_item.Source,
# BugBug                                                                     ref_line=var_item.Line,
# BugBug                                                                     ref_column=var_item.Column,
# BugBug                                                                   )
# BugBug 
# BugBug             if var_item.element_type in [ FundamentalElement,
# BugBug                                           VariantElement,
# BugBug                                         ]:
# BugBug                 break
# BugBug 
# BugBug             if var_item.element_type == ReferenceElement:
# BugBug                 var_item = var_item.reference
# BugBug             else:
# BugBug                 raise ResolveInvalidVariantReferenceTypeException( item.Source,
# BugBug                                                                    item.Line,
# BugBug                                                                    item.Column,
# BugBug                                                                    ref_source=var_item.Source,
# BugBug                                                                    ref_line=var_item.Line,
# BugBug                                                                    ref_column=var_item.Column,
# BugBug                                                                  )

# ----------------------------------------------------------------------
def _ResolveMetadata_NonArity(plugin, config_values, item):
    if isinstance(item.metadata, ResolvedMetadata):
        return

    metadata = item.metadata.Values
    
    # Augment the data with configuration values
    for k, v in six.iteritems(config_values):
        if k not in metadata:
            metadata[k] = v

    # Get the metadata info

    # ----------------------------------------------------------------------
    @staticderived
    class MetadataInfoVisitor(ItemVisitor):
        # ----------------------------------------------------------------------
        @staticmethod
        def OnFundamental(item):
            return item.reference

        # ----------------------------------------------------------------------
        @staticmethod
        def OnCompound(item):
            return COMPOUND_METADATA_INFO

        # ----------------------------------------------------------------------
        @staticmethod
        def OnSimple(item):
            return SIMPLE_METADATA_INFO

        # ----------------------------------------------------------------------
        @staticmethod
        def OnAny(item):
            return item.reference

        # ----------------------------------------------------------------------
        @staticmethod
        def OnCustom(item):
            return item.reference

        # ----------------------------------------------------------------------
        @staticmethod
        def OnVariant(item):
            return VARIANT_METADATA_INFO

        # ----------------------------------------------------------------------
        @staticmethod
        def OnList(item):
            return LIST_METADATA_INFO

        # ----------------------------------------------------------------------
        @staticmethod
        def OnExtension(item):
            return EXTENSION_METADATA_INFO

        # ----------------------------------------------------------------------
        @staticmethod
        def OnReference(item):
            return REFERENCE_METADATA_INFO
        
    # ----------------------------------------------------------------------

    metadata_info = MetadataInfoVisitor.Accept(item)

    item.metadata = ResolvedMetadata( metadata,
                                      UNIVERSAL_METADATA_INFO.RequiredMetadataItems + metadata_info.RequiredMetadataItems,
                                      UNIVERSAL_METADATA_INFO.OptionalMetadataItems + metadata_info.OptionalMetadataItems,
                                    )

    for item in item.Enumerate():
        if item.element_type == ReferenceElement and not plugin.BreaksReferenceChain(item):
            _ResolveMetadata_NonArity(plugin, config_values, item.reference)

            item.metadata = item.metadata.Clone(item.reference.metadata)

# ----------------------------------------------------------------------
def _ResolveMetadata_Arity(item):
    for item in item.Enumerate():
        if item.arity.IsOptional:
            item.metadata.Clone(ResolvedMetadata( {},
                                                  OPTIONAL_METADATA_INFO.RequiredMetadataItems,
                                                  OPTIONAL_METADATA_INFO.OptionalMetadataItems,
                                                ))
        elif item.arity.IsCollection:
            item.metadata.Clone(ResolvedMetadata( {},
                                                  COLLECTION_METADATA_INFO.RequiredMetadataItems,
                                                  COLLECTION_METADATA_INFO.OptionalMetadataItems,
                                                ))

# ----------------------------------------------------------------------
def _ResolveMetadata_Defaults(item):
    for item in item.Enumerate():
        for md in itertools.chain( item.metadata.RequiredMetadataItems,
                                   item.metadata.OptionalMetadataItems,
                                 ):
            if md.Name not in item.metadata.Values and md.DefaultValueFunc:
                item.metadata.Values[md.Name] = Item.MetadataValue( md.DefaultValueFunc(item),
                                                                    Item.MetadataSource.Default,
                                                                    item.Source,
                                                                    item.Line,
                                                                    item.Column
                                                                  )