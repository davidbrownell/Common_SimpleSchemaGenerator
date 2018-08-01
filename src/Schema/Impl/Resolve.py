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
"""Functionality that resolves references information associated with Items"""

import itertools
import os
import sys

import six
import inflect as inflect_mod

from CommonEnvironment.Interface import staticderived, override
from CommonEnvironment.TypeInfo import Arity

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from .Item import Item, MetadataValue, MetadataSource, ResolvedMetadata, ItemVisitor
    from .. import Attributes
    from .. import Elements
    from .. import Exceptions

# ----------------------------------------------------------------------
inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
def Resolve(root, plugin):
    # ----------------------------------------------------------------------
    def Impl(item, functor):
        functor(item)

        for child in item.items:
            Impl(child, functor)

    # ----------------------------------------------------------------------

    config_metadata = root.config.get(plugin.Name, [ {}, ])

    # Flatten the config metadata
    if len(config_metadata) > 1:
        dest_metadata = config_metadata[0]
        for metadata in config_metadata[1:]:
            for k, v in six.iteritems(metadata):
                if k not in dest_metadata:
                    dest_metadata[k] = v

    assert config_metadata
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
    
        if ref in Attributes.FUNDAMENTAL_ATTRIBUTE_INFO_MAP or ref in [ "any", "custom", ]:
            return ref
    
        name_parts = ref.split('.')
    
        i = item
        while i:
            query = i
    
            for name_part in name_parts:
                # The second clause in the statement below prevents self references. This
                # can help in situations such as:
                #
                #   (foo string)
                #
                #   <obj>:
                #       <foo foo> # Foo should not reference itself
                #
                query = next((qi for qi in query.items if qi.name == name_part and qi != item), None)
                if query is None:
                    break
    
            if query:
                query.referenced_by.append(item)
                return query
    
            # Try again at a higher level
            i = i .Parent
    
        raise Exceptions.ResolveInvalidReferenceException( item.Source,
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
            
            new_items.append(new_item)
        
        item.reference = new_items
    else:
        item.reference = Impl(item.reference)

# ----------------------------------------------------------------------
def _ResolveElementType(item):
    """Assign an element type for the item"""

    if isinstance(item.reference, list):
        item.element_type = Elements.VariantElement
        items = item.reference
    else:
        items = [ item, ]

    for item in items:
        if item.DeclarationType == Item.DeclarationType.Extension:
            element_type = Elements.ExtensionElement

        elif item.DeclarationType == Item.DeclarationType.Object:
            # If here, we are looking at a Compound or a Simple object. A Simple
            # object is one that ultimately references a fundamental type.

            # ----------------------------------------------------------------------
            def IsSimple():
                ref = item.reference
                while isinstance(ref, Item):
                    ref = ref.reference

                return isinstance(ref, Attributes.FundamentalAttributeInfo)

            # ----------------------------------------------------------------------

            element_type = Elements.SimpleElement if IsSimple() else Elements.CompoundElement

        elif item.DeclarationType == Item.DeclarationType.Declaration:
            assert item.reference is not None

            if isinstance(item.reference, Item):
                element_type = Elements.ReferenceElement
            
            elif isinstance(item.reference, six.string_types):
                if item.reference in Attributes.FUNDAMENTAL_ATTRIBUTE_INFO_MAP:
                    element_type = Elements.FundamentalElement
                    item.reference = Attributes.FUNDAMENTAL_ATTRIBUTE_INFO_MAP[item.reference]

                elif item.reference == "any":
                    element_type = Elements.AnyElement
                    item.reference = Attributes.ANY_ATTRIBUTE_INFO

                elif item.reference == "custom":
                    element_type = Elements.CustomElement
                    item.reference = Attributes.CUSTOM_ATTRIBUTE_INFO

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

    if item.element_type == Elements.ReferenceElement and not plugin.BreaksReferenceChain(item):
        _ResolveArity(plugin, item.reference)
        item.arity = item.reference.arity
    else:
        item.arity = Arity(1, 1)

        if item.element_type == Elements.VariantElement:
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
    
    if Attributes.NAME_OVERRIDE_ATTRIBUTE_NAME in item.metadata.Values:
        metadata_value = item.metadata.Values[Attributes.NAME_OVERRIDE_ATTRIBUTE_NAME]
        if not IsValidName(metadata_value.Value):
            raise Exceptions.ResolveInvalidCustomNameException( metadata_value.Source,
                                                                metadata_value.Line,
                                                                metadata_value.Column,
                                                                name=metadata_value.Value,
                                                              )

        item.name = metadata_value.Value
        del item.metadata.Values[Attributes.NAME_OVERRIDE_ATTRIBUTE_NAME]

    item.original_name = item.name

    if item.arity.IsCollection:
        if Attributes.PLURAL_ATTRIBUTE_NAME in item.metadata.Values:
            metadata_value = item.metadata.Values[Attributes.PLURAL_ATTRIBUTE_NAME]
            if not IsValidName(metadata_value.Value):
                raise Exceptions.ResolveInvalidCustomNameException( metadata_value.Source,
                                                                    metadata_value.Line,
                                                                    metadata_value.Column,
                                                                    name=metadata_value.Value,
                                                                  )

            item.name = metadata_value.Value
            del item.metadata.Values[Attributes.PLURAL_ATTRIBUTE_NAME]

        else:
            item.name = inflect.plural(item.name)

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
    metadata_info = _MetadataInfoVisitor.Accept(item)

    item.metadata = ResolvedMetadata( metadata,
                                      Attributes.UNIVERSAL_ATTRIBUTE_INFO.RequiredItems + metadata_info.RequiredItems,
                                      Attributes.UNIVERSAL_ATTRIBUTE_INFO.OptionalItems + metadata_info.OptionalItems,
                                    )

    for item in item.Enumerate():
        _ResolveMetadata_NonArity(plugin, config_values, item)

        if item.element_type == Elements.ReferenceElement and not plugin.BreaksReferenceChain(item):
            _ResolveMetadata_NonArity(plugin, config_values, item.reference)

            item.metadata = item.metadata.Clone(item.reference.metadata)

# ----------------------------------------------------------------------
def _ResolveMetadata_Arity(item):
    for item in item.Enumerate():
        if item.arity.IsOptional:
            item.metadata = item.metadata.Clone(ResolvedMetadata( {},
                                                                  Attributes.OPTIONAL_ATTRIBUTE_INFO.RequiredItems,
                                                                  Attributes.OPTIONAL_ATTRIBUTE_INFO.OptionalItems,
                                                                ))
        elif item.arity.IsCollection:
            item.metadata = item.metadata.Clone(ResolvedMetadata( {},
                                                                  Attributes.COLLECTION_ATTRIBUTE_INFO.RequiredItems,
                                                                  Attributes.COLLECTION_ATTRIBUTE_INFO.OptionalItems,
                                                                ))

# ----------------------------------------------------------------------
def _ResolveMetadata_Defaults(item):
    for item in item.Enumerate():
        for md in itertools.chain( item.metadata.RequiredItems,
                                   item.metadata.OptionalItems,
                                 ):
            if md.Name not in item.metadata.Values and md.DefaultValue != Attributes.Attribute.DoesNotExist:
                if callable(md.DefaultValue):
                    value = md.DefaultValue(item)
                else:
                    value = md.DefaultValue

                item.metadata.Values[md.Name] = MetadataValue( value,
                                                               MetadataSource.Default,
                                                               item.Source,
                                                               item.Line,
                                                               item.Column
                                                             )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@staticderived
class _MetadataInfoVisitor(ItemVisitor):
    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnFundamental(item, *args, **kwargs):
        assert isinstance(item.reference, Attributes.FundamentalAttributeInfo), item.reference
        return item.reference

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnCompound(item, *args, **kwargs):
        return Attributes.COMPOUND_ATTRIBUTE_INFO

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnSimple(item, *args, **kwargs):
        return Attributes.SIMPLE_ATTRIBUTE_INFO

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnAny(item, *args, **kwargs):
        assert isinstance(item.reference, Attributes.AttributeInfo), item.reference
        return item.reference

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnCustom(item, *args, **kwargs):
        assert isinstance(item.reference, Attributes.AttributeInfo), item.reference
        return item.reference

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnVariant(item, *args, **kwargs):
        return Attributes.VARIANT_ATTRIBUTE_INFO

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnExtension(item, *args, **kwargs):
        return Attributes.EXTENSION_ATTRIBUTE_INFO

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnReference(item, *args, **kwargs):
        return Attributes.REFERENCE_ATTRIBUTE_INFO
