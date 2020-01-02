# ----------------------------------------------------------------------
# |
# |  Resolve.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-12 12:50:27
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-20.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Functionality that resolves references information associated with Items"""

import itertools
import os
import sys

from collections import OrderedDict, namedtuple

import six

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override
from CommonEnvironment.TypeInfo import Arity, ValidationException
from CommonEnvironment.TypeInfo.FundamentalTypes.BoolTypeInfo import BoolTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from .Item import Item, MetadataSource, MetadataValue, Metadata, ResolvedMetadata, ItemVisitor

    from .. import Attributes
    from .. import Elements
    from .. import Exceptions

    from ...Plugin import ParseFlag

# ----------------------------------------------------------------------
def Resolve(root, plugin):
    # ----------------------------------------------------------------------
    def Impl(item, functor):
        functor(item)

        for child in item.items:
            Impl(child, functor)

    # ----------------------------------------------------------------------

    config_metadata = root.config.get(plugin.Name, [{}])

    # Flatten the config metadata
    if len(config_metadata) > 1:
        dest_metadata = config_metadata[0]
        for metadata in config_metadata[1:]:
            for k, v in six.iteritems(metadata):
                if k not in dest_metadata:
                    dest_metadata[k] = v

    assert config_metadata
    config_metadata = config_metadata[0]

    reference_states = {}

    Impl(root, _ResolveReference)
    Impl(root, _ResolveName)
    Impl(root, lambda item: _ResolveElementType(plugin, reference_states, item))
    Impl(root, _ResolveArity)
    Impl(root, lambda item: _ResolveMetadata(plugin, config_metadata, item))
    Impl(root, lambda item: _ResolveReferenceType(reference_states, item))
    Impl(root, _ResolveMetadataDefaults)

    return root


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
_ReferenceState                             = namedtuple("ReferenceState", ["HasArity", "MetadataKeys"])

# ----------------------------------------------------------------------
def _ResolveReference(item):
    """Convert string names into Items"""

    if not item.references:
        return

    # ----------------------------------------------------------------------
    def Impl(ref):
        assert isinstance(ref, six.string_types), ref

        if ref in Attributes.FUNDAMENTAL_ATTRIBUTE_INFO_MAP:
            return Attributes.FUNDAMENTAL_ATTRIBUTE_INFO_MAP[ref]
        elif ref == "any":
            return Attributes.ANY_ATTRIBUTE_INFO
        elif ref == "custom":
            return Attributes.CUSTOM_ATTRIBUTE_INFO

        name_parts = ref.split(".")

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
            i = i.Parent

        raise Exceptions.ResolveInvalidReferenceException(
            item.Source,
            item.Line,
            item.Column,
            name=ref,
        )

    # ----------------------------------------------------------------------

    new_reference_items = []

    for ref_index, ref in enumerate(item.references):
        if item.multi_reference_type == Item.MultiReferenceType.Variant:
            ref, ref_metadata = ref

            new_item = Item(Item.DeclarationType.Declaration, Item.ItemType.Standard, item, item.Source, item.Line, item.Column, item.IsExternal)

            new_item.name = str(ref_index)
            new_item.references = [Impl(ref)]
            new_item.metadata = ref_metadata

            new_reference_items.append(new_item)
        else:
            new_reference_items.append(Impl(ref))

    item.references = new_reference_items


# ----------------------------------------------------------------------
def _ResolveName(item):
    """Apply custom name info if provided by metadata"""

    # ----------------------------------------------------------------------
    def IsValidName(value):
        return bool(value)

    # ----------------------------------------------------------------------

    if Attributes.UNIVERSAL_NAME_OVERRIDE_ATTRIBUTE_NAME in item.metadata.Values:
        metadata_value = item.metadata.Values[Attributes.UNIVERSAL_NAME_OVERRIDE_ATTRIBUTE_NAME]
        if not IsValidName(metadata_value.Value):
            raise Exceptions.ResolveInvalidCustomNameException(
                metadata_value.Source,
                metadata_value.Line,
                metadata_value.Column,
                name=metadata_value.Value,
            )

        item.name = metadata_value.Value
        del item.metadata.Values[Attributes.UNIVERSAL_NAME_OVERRIDE_ATTRIBUTE_NAME]


# ----------------------------------------------------------------------
def _ResolveElementType(plugin, reference_states, item):
    """Assign an element type for the item"""

    if item.multi_reference_type == Item.MultiReferenceType.Variant:
        item.element_type = Elements.VariantElement
        items = item.references
    else:
        items = [item]

    for item in items:
        if item.DeclarationType == Item.DeclarationType.Extension:
            element_type = Elements.ExtensionElement

        elif item.DeclarationType == Item.DeclarationType.Object:
            # If here, we are looking at a Compound or a Simple object. A Simple
            # object is one that ultimately references a fundamental type.

            # ----------------------------------------------------------------------
            def IsSimple():
                search_queue = list(item.references)
                searched = set()

                while search_queue:
                    ref = search_queue.pop(0)
                    if ref in searched:
                        continue

                    searched.add(ref)

                    if isinstance(ref, Attributes.FundamentalAttributeInfo):
                        return True

                    if ref.element_type == Elements.SimpleElement:
                        return True

                    search_queue += ref.references

                return False

            # ----------------------------------------------------------------------

            if IsSimple():
                element_type = Elements.SimpleElement
                found_fundamental_element = False

                reference_index = 0
                while reference_index < len(item.references):
                    reference = item.references[reference_index]

                    if not isinstance(reference, Attributes.FundamentalAttributeInfo):
                        reference_index += 1

                        continue

                    if found_fundamental_element:
                        raise Exceptions.ResolveMultipleSimpleFundamentalElementsException(item.Source, item.Line, item.Column)

                    found_fundamental_element = True

                    # Split the item into a parent/child relationship for later processing

                    # Extract all the metadata values that belong to the fundamental item
                    simple_object_metadata_names = set()

                    for attributes in [
                        Attributes.UNIVERSAL_ATTRIBUTE_INFO,
                        Attributes.SIMPLE_ATTRIBUTE_INFO,
                        Attributes.COLLECTION_ATTRIBUTE_INFO,
                        Attributes.OPTIONAL_ATTRIBUTE_INFO,
                    ]:
                        for md in itertools.chain(attributes.RequiredItems, attributes.OptionalItems):
                            simple_object_metadata_names.add(md.Name)

                    fundamental_metadata = OrderedDict()

                    metadata_keys = list(item.metadata.Values.keys())
                    for metadata_key in metadata_keys:
                        if metadata_key not in simple_object_metadata_names:
                            fundamental_metadata[metadata_key] = item.metadata.Values.pop(metadata_key)

                    # Create the new item
                    fundamental_item = Item(Item.DeclarationType.Declaration, Item.ItemType.Attribute, item, item.Source, item.Line, item.Column, item.IsExternal)

                    fundamental_item.name = None
                    fundamental_item.references = [reference]

                    fundamental_item.metadata = Metadata(fundamental_metadata, item.Source, item.Line, item.Column)

                    # Apply the change
                    del item.references[reference_index]
                    item.items.insert(0, fundamental_item)

            else:
                element_type = Elements.CompoundElement

        elif item.DeclarationType == Item.DeclarationType.Declaration:
            assert len(item.references) == 1, (item.references, item)
            reference = item.references[0]

            if isinstance(reference, Item):

                # ----------------------------------------------------------------------
                def IsList():
                    # This item is a list if it meets the following conditions:
                    #
                    #   1) An arity was explicitly provided
                    #   2) The arity is a collection
                    #   3) The referenced item (or one of its descendants) has an arity
                    #   4) The referenced item's arity (or one of its descendants) is a collection.
                    #   5) 'refines_arity' is not provided or set to False

                    # 1 and 2
                    if item.arity is None or not item.arity.IsCollection:
                        return False

                    # 3 and 4
                    ref = reference
                    while ref.element_type == Elements.ReferenceElement and ref.arity is None:
                        assert len(ref.references) == 1, ref.references
                        ref = ref.references[0]

                    if ref.arity is None or not ref.arity.IsCollection:
                        return False

                    # 5
                    if Attributes.COLLECTION_REFINES_ARITY_ATTRIBUTE_NAME in item.metadata.Values:
                        refines_arity = item.metadata.Values[Attributes.COLLECTION_REFINES_ARITY_ATTRIBUTE_NAME].Value
                        del item.metadata.Values[Attributes.COLLECTION_REFINES_ARITY_ATTRIBUTE_NAME]

                        try:
                            refines_arity = StringSerialization.DeserializeItem(BoolTypeInfo(), refines_arity)
                        except ValidationException as ex:
                            raise Exceptions.InvalidAttributeException(
                                item.Source,
                                item.Line,
                                item.Column,
                                desc="'{}' is not valid: {}".fromat(Attributes.COLLECTION_REFINES_ARITY_ATTRIBUTE_NAME, str(ex)),
                            )

                        if refines_arity:
                            return False

                    return True

                # ----------------------------------------------------------------------

                if IsList():
                    element_type = Elements.ListElement
                else:
                    element_type = Elements.ReferenceElement

                    # This reference may be a simple reference or an item that augments
                    # another. Unfortunately, we don't have the context here to differentiate
                    # between the two, so capture state information that can be used later
                    # when we do have the necessary context.
                    reference_states[item] = _ReferenceState(item.arity is not None, list(six.iterkeys(item.metadata.Values)))

            elif isinstance(reference, Attributes.FundamentalAttributeInfo):
                element_type = Elements.FundamentalElement
            elif reference == Attributes.ANY_ATTRIBUTE_INFO:
                element_type = Elements.AnyElement
            elif reference == Attributes.CUSTOM_ATTRIBUTE_INFO:
                element_type = Elements.CustomElement
            else:
                assert False, reference

        else:
            assert False, item.DeclarationType

        item.element_type = element_type


# ----------------------------------------------------------------------
def _ResolveArity(item):
    for sub_item in item.Enumerate(
        variant_includes_self=True,
    ):
        if sub_item.arity is not None:
            continue

        if sub_item.element_type == Elements.ReferenceElement:
            assert len(sub_item.references) == 1, sub_item.references

            _ResolveArity(sub_item.references[0])
            sub_item.arity = sub_item.references[0].arity
        else:
            sub_item.arity = Arity(1, 1)


# ----------------------------------------------------------------------
def _ResolveMetadata(plugin, config_values, item):
    if isinstance(item.metadata, ResolvedMetadata):
        return

    metadata = item.metadata.Values

    # Augment the data with configuration values
    for k, v in six.iteritems(config_values):
        if k not in metadata:
            metadata[k] = v

    # Get the metadata info
    metadata_info = _MetadataInfoVisitor.Accept(item)

    item.metadata = ResolvedMetadata(
        metadata,
        Attributes.UNIVERSAL_ATTRIBUTE_INFO.RequiredItems + metadata_info.RequiredItems + plugin.GetRequiredMetadataItems(item),
        Attributes.UNIVERSAL_ATTRIBUTE_INFO.OptionalItems + metadata_info.OptionalItems + plugin.GetOptionalMetadataItems(item),
    )

    if item.arity.IsOptional:
        item.metadata = item.metadata.Clone(Attributes.OPTIONAL_ATTRIBUTE_INFO)
    elif item.arity.IsCollection:
        item.metadata = item.metadata.Clone(Attributes.COLLECTION_ATTRIBUTE_INFO)

    for item in item.Enumerate():
        _ResolveMetadata(plugin, config_values, item)

        # Squash metadata for SimpleElememt types
        if item.element_type == Elements.SimpleElement:
            # A SimpleElement will either reference other SimpleElement(s) or
            # contain a child that references a FundamentalElement, but never both.
            if item.references:
                for ref in item.references:
                    if isinstance(ref, Item):
                        _ResolveMetadata(plugin, config_values, ref)
                        item.metadata = item.metadata.Clone(ref.metadata)

            else:
                assert item.items
                assert item.items[0].name is None, item.items[0]

                _ResolveMetadata(plugin, config_values, item.items[0])
                item.metadata = item.metadata.Clone(item.items[0].metadata)

        # Squash metadata for ReferenceElement types
        if item.element_type == Elements.ReferenceElement:
            assert len(item.references) == 1, item.references

            _ResolveMetadata(plugin, config_values, item.references[0])

            item.metadata = item.metadata.Clone(item.references[0].metadata)


# ----------------------------------------------------------------------
def _ResolveReferenceType(reference_states, item):
    # ----------------------------------------------------------------------
    def IsAugmenting(item):
        state = reference_states.pop(item)

        if state.HasArity:
            return True

        for attribute in itertools.chain(item.metadata.RequiredItems, item.metadata.OptionalItems):
            if attribute.IsMetadata:
                continue

            if attribute.Name in state.MetadataKeys:
                return True

        return False

    # ----------------------------------------------------------------------

    for item in item.Enumerate():
        if item.element_type != Elements.ReferenceElement:
            continue

        if item not in reference_states:
            continue

        item.is_augmenting_reference = IsAugmenting(item)


# ----------------------------------------------------------------------
def _ResolveMetadataDefaults(item):
    for item in item.Enumerate():
        for attribute in itertools.chain(item.metadata.RequiredItems, item.metadata.OptionalItems):
            if attribute.Name not in item.metadata.Values and attribute.DefaultValue != Attributes.Attribute.DoesNotExist:
                if callable(attribute.DefaultValue):
                    value = attribute.DefaultValue(item)
                else:
                    value = attribute.DefaultValue

                item.metadata.Values[attribute.Name] = MetadataValue(value, MetadataSource.Default, item.Source, item.Line, item.Column)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@staticderived
class _MetadataInfoVisitor(ItemVisitor):
    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnFundamental(item, *args, **kwargs):
        assert len(item.references) == 1 and isinstance(item.references[0], Attributes.FundamentalAttributeInfo), item.references
        return item.references[0]

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
        assert len(item.references) == 1 and isinstance(item.references[0], Attributes.AttributeInfo), item.references
        return item.references[0]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnCustom(item, *args, **kwargs):
        assert len(item.references) == 1 and isinstance(item.references[0], Attributes.AttributeInfo), item.references[0]
        return item.references[0]

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

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnList(item, *args, **kwargs):
        return Attributes.LIST_ATTRIBUTE_INFO
