# ----------------------------------------------------------------------
# |
# |  Transform.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-13 15:18:37
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Transforms Items into Element objects"""

import copy
import itertools
import os

from collections import OrderedDict

import six

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo, Arity
from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
from CommonEnvironment.TypeInfo.ClassTypeInfo import ClassTypeInfo
from CommonEnvironment.TypeInfo.GenericTypeInfo import GenericTypeInfo
from CommonEnvironment.TypeInfo.ListTypeInfo import ListTypeInfo

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from .Item import Item, ItemVisitor

    from .. import Attributes
    from .. import Elements
    from .. import Exceptions

    from ...Plugin import ParseFlag

# ----------------------------------------------------------------------
# <Access to a protected member> pylint: disable = W0212

# ----------------------------------------------------------------------
def Transform(root, plugin):
    elements = {}

    # When an element is created, we may not have all the information necessary
    # to fully create it (as will be the case with circular references). Methods
    # can be added to this queue to execute after all of the elements are created;
    # at this time the context is available and anything that couldn't be created
    # before can be created at this time.
    delayed_instruction_queue = []

    extensions_allowing_duplicate_names = {ext.Name for ext in plugin.GetExtensions() if ext.AllowDuplicates}

    apply_type_info_visitor = _ApplyTypeInfoVisitor()
    create_element_visitor = _CreateElementVisitor()

    # ----------------------------------------------------------------------
    def ApplyTypeInfo(item, metadata_item, element):
        return apply_type_info_visitor.Accept(
            item,
            metadata_item,
            element,
            elements,
            delayed_instruction_queue,      # Item to use when creating the type info  # Item to use when providing metadata about the type info
        )

    # ----------------------------------------------------------------------
    def CreateElement(item):
        if item.ignore:
            return False

        allow_duplicates = item.element_type == Elements.ExtensionElement and item.name in extensions_allowing_duplicate_names

        if item.Key in elements and not allow_duplicates:
            return elements[item.Key]

        # Single that we are in the process of creating this element
        if allow_duplicates:
            elements.setdefault(item.Key, []).append(None)
        else:
            elements[item.Key] = None

        element = create_element_visitor.Accept(
            item,                                                           # Item to use when creating the element
            item,                                                           # Item to use when providing metadata about the element
            plugin,
            elements,
            delayed_instruction_queue,
            ApplyTypeInfo,
            CreateElement,
            is_definition_only=item.ItemType == Item.ItemType.Definition,
        )

        element._item = item

        if allow_duplicates:
            elements[item.Key][-1] = element
        else:
            elements[item.Key] = element

        return element

    # ----------------------------------------------------------------------
    def ValidateAndApplyMetadata(element):
        # Note that we are applying before validating to provide
        # a more consistent validation experience for the metadata
        # items. Should validation fail, and exception will be raised
        # and the element will be invalidated anyway.

        # Apply
        for k, v in six.iteritems(element._item.metadata.Values):
            if hasattr(element, k):
                raise Exceptions.InvalidAttributeNameException(
                    v.Source,
                    v.Line,
                    v.Column,
                    name=k,
                )

            setattr(element, k, v.Value)

        # Validate
        for md in itertools.chain(element._item.metadata.RequiredItems, element._item.metadata.OptionalItems):
            result = None

            if md.Name in element._item.metadata.Values:
                if md.ValidateFunc is not None:
                    result = md.ValidateFunc(plugin, element)
            else:
                if md.MissingValidateFunc is not None:
                    result = md.MissingValidateFunc(plugin, element)

            if result is not None:
                if md.Name in element._item.metadata.Values:
                    location_source = element._item.metadata.Values[md.Name]
                else:
                    location_source = element

                raise Exceptions.InvalidAttributeException(
                    location_source.Source,
                    location_source.Line,
                    location_source.Column,
                    desc=result,
                )

        # Commit
        element.Metadata = element._item.metadata
        element.AttributeNames = list(six.iterkeys(element._item.metadata.Values))

    # ----------------------------------------------------------------------
    def ResolveSimpleTypeInfo(element):
        if not isinstance(element, (Elements.SimpleElement, Elements.CompoundElement)):
            return

        if isinstance(element, Elements.CompoundElement) and not hasattr(element, "FundamentalAttributeName"):
            return

        for reference in element._item.references:
            assert reference.Key in elements, reference.Key
            ref_element = elements[reference.Key]
            assert ref_element

            for k, v in six.iteritems(ref_element.TypeInfo.Items):
                if k in element.TypeInfo.Items:
                    assert id(element.TypeInfo.Items[k]) == id(v), k
                    continue

                element.TypeInfo.Items[k] = v

    # ----------------------------------------------------------------------
    def ResolveSimpleFundamentalName(element):
        if not isinstance(element, (Elements.SimpleElement, Elements.CompoundElement)):
            return

        if isinstance(element, Elements.CompoundElement) and not hasattr(element, "FundamentalAttributeName"):
            return

        # Remove the None child
        child_index = 0
        while child_index < len(element.Children):
            child = element.Children[child_index]

            if child.Name is None:
                del element.Children[child_index]
                continue

            child_index += 1

        # Update the element to reflect the fundamental attribute name. Note that
        # this needs to be done after all of the elements have been created so that
        # each SimpleElement sees the value to be set as None (rather than the resolved
        # value).

        if element.FundamentalAttributeName:
            if None in element.TypeInfo.Items:
                element.TypeInfo.Items[element.FundamentalAttributeName] = element.TypeInfo.Items.pop(None)

    # ----------------------------------------------------------------------
    def CreateVariantTypeInfoList(element):
        if isinstance(element, Elements.ReferenceElement):
            return CreateVariantTypeInfoList(element.Reference)

        if isinstance(element, Elements.VariantElement):
            result = []

            for variation in element.Variations:
                result += CreateVariantTypeInfoList(variation)

            return result

        return [element.TypeInfo]

    # ----------------------------------------------------------------------
    def ResolveVariantTypeInfo(element):
        if not isinstance(element, Elements.VariantElement):
            return

        element.TypeInfo.ElementTypeInfos = CreateVariantTypeInfoList(element)

    # ----------------------------------------------------------------------
    def Cleanup(element):
        del element._item

    # ----------------------------------------------------------------------
    def Impl(
        element,
        functor,
        visited=None,
    ):
        if visited is None:
            visited = set()

        if element in visited:
            return

        visited.add(element)

        functor(element)

        for child in getattr(element, "Children", []):
            Impl(
                child,
                functor,
                visited=visited,
            )

    # ----------------------------------------------------------------------

    root_element = CreateElement(root)
    assert root_element

    while delayed_instruction_queue:
        instruction = delayed_instruction_queue.pop(0)
        instruction()

    Impl(root_element, ValidateAndApplyMetadata)
    Impl(root_element, ResolveSimpleTypeInfo)
    Impl(root_element, ResolveSimpleFundamentalName)
    Impl(root_element, ResolveVariantTypeInfo)
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
    def OnFundamental(
        cls,
        item,
        metadata_item,
        plugin,
        elements,
        delayed_instruction_queue,
        apply_type_info_func,
        create_element_func,                # <Unused argument> pylint: disable = W0613
        is_definition_only,
    ):                                      # <Parameters differ from overridden...> pylint: disable = W0221
        element = Elements.FundamentalElement(
            is_attribute=metadata_item.ItemType == Item.ItemType.Attribute and (plugin.Flags & ParseFlag.SupportAttributes) != 0,
            type_info=None,                             # Set below
            name=metadata_item.name,
            parent=None,                                # Set below
            source=metadata_item.Source,
            line=metadata_item.Line,
            column=metadata_item.Column,
            is_definition_only=is_definition_only,
            is_external=metadata_item.IsExternal,
        )

        # Parent
        cls._ApplyParent(element, metadata_item, elements, delayed_instruction_queue)

        # TypeInfo
        apply_type_info_func(item, metadata_item, element)

        return element

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnCompound(
        cls,
        item,
        metadata_item,
        plugin,                             # <Unused argument> pylint: disable = W0613
        elements,
        delayed_instruction_queue,
        apply_type_info_func,
        create_element_func,
        is_definition_only,
    ):                                      # <Parameters differ from overridden...> pylint: disable = W0221
        element = Elements.CompoundElement(
            children=cls._CreateChildElements(item, item.items, elements, delayed_instruction_queue, create_element_func),
            bases=[],                                   # Set below
            derived=[],                                 # Set below
            type_info=None,                             # Set below
            name=metadata_item.name,
            parent=None,                                # Set below
            source=metadata_item.Source,
            line=metadata_item.Line,
            column=metadata_item.Column,
            is_definition_only=is_definition_only,
            is_external=metadata_item.IsExternal,
        )

        # Parent
        cls._ApplyParent(element, metadata_item, elements, delayed_instruction_queue)

        # Apply the bases
        if item.references:
            element.Bases = [None] * len(item.references)

            # ----------------------------------------------------------------------
            def ApplyBase(ref_index, ref):
                assert ref.Key in elements, ref.Key
                base_element = elements[ref.Key]
                assert base_element

                element.Bases[ref_index] = base_element
                element.Bases[ref_index].Derived.append(element)

            # ----------------------------------------------------------------------

            for ref_index, ref in enumerate(item.references):
                if elements.get(ref.Key, None) is None:
                    delayed_instruction_queue.append(
                        lambda ref_index=ref_index, ref=ref: ApplyBase(ref_index, ref),
                    )
                else:
                    ApplyBase(ref_index, ref)

        # TypeInfo
        apply_type_info_func(item, metadata_item, element)

        return element

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnSimple(
        cls,
        item,
        metadata_item,
        plugin,                             # <Unused argument> pylint: disable = W0613
        elements,
        delayed_instruction_queue,
        apply_type_info_func,
        create_element_func,
        is_definition_only,
    ):                                      # <Parameters differ from overridden...> pylint: disable = W0221
        fundamental_attribute_name = metadata_item.metadata.Values.get(Attributes.SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME, None)
        if fundamental_attribute_name is not None:
            fundamental_attribute_name = fundamental_attribute_name.Value

        if plugin.Flags & ParseFlag.SupportSimpleObjectElements:
            element = Elements.SimpleElement(
                fundamental_attribute_name=fundamental_attribute_name,
                attributes=cls._CreateChildElements(item, item.items, elements, delayed_instruction_queue, create_element_func),
                type_info=None,                         # Set below
                name=metadata_item.name,
                parent=None,                            # Set below
                source=metadata_item.Source,
                line=metadata_item.Line,
                column=metadata_item.Column,
                is_definition_only=is_definition_only,
                is_external=metadata_item.IsExternal,
            )
        else:
            # Treat this object as a CompoundElement
            element = Elements.CompoundElement(
                children=cls._CreateChildElements(item, item.items, elements, delayed_instruction_queue, create_element_func),
                bases=[],
                derived=[],
                type_info=None,                                             # Set below
                name=metadata_item.name,
                parent=None,                                                # Set below
                source=metadata_item.Source,
                line=metadata_item.Line,
                column=metadata_item.Column,
                is_definition_only=is_definition_only,
                is_external=metadata_item.IsExternal,
            )
            element.FundamentalAttributeName = fundamental_attribute_name

        # Parent                                                                           # Parent
        cls._ApplyParent(element, metadata_item, elements, delayed_instruction_queue)

        # Apply the bases
        if item.references:
            # ----------------------------------------------------------------------
            def ApplyBase(ref):
                assert ref.Key in elements, ref.key
                base_element = elements[ref.Key]
                assert base_element

                for child in base_element.Children:
                    new_child = copy.deepcopy(child)
                    new_child.Parent = element

                    element.Children.append(new_child)

            # ----------------------------------------------------------------------

            for ref in item.references:
                if elements.get(ref.Key, None) is None:
                    delayed_instruction_queue.append(
                        lambda ref=ref: ApplyBase(ref),
                    )
                else:
                    ApplyBase(ref)

        apply_type_info_func(item, metadata_item, element)

        return element

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnVariant(
        cls,
        item,
        metadata_item,
        plugin,                             # <Unused argument> pylint: disable = W0613
        elements,
        delayed_instruction_queue,
        apply_type_info_func,
        create_element_func,
        is_definition_only,
    ):                                      # <Parameters differ from overridden...> pylint: disable = W0221
        element = Elements.VariantElement(
            variations=cls._CreateChildElements(item, item.references, elements, delayed_instruction_queue, create_element_func),
            is_attribute=metadata_item.ItemType == Item.ItemType.Attribute and (plugin.Flags & ParseFlag.SupportAttributes) != 0,
            type_info=None,                             # Set below
            name=metadata_item.name,
            parent=None,                                # Set below
            source=metadata_item.Source,
            line=metadata_item.Line,
            column=metadata_item.Column,
            is_definition_only=is_definition_only,
            is_external=metadata_item.IsExternal,
        )

        # Parent
        cls._ApplyParent(element, metadata_item, elements, delayed_instruction_queue)

        # TypeInfo
        apply_type_info_func(item, metadata_item, element)

        return element

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnReference(
        cls,
        item,
        metadata_item,
        plugin,                             # <Unused argument> pylint: disable = W0613
        elements,
        delayed_instruction_queue,
        apply_type_info_func,
        create_element_func,
        is_definition_only,
    ):                                      # <Parameters differ from overridden...> pylint: disable = W0221
        if (
            metadata_item.is_augmenting_reference
            and not (plugin.Flags & ParseFlag.MaintainAugmentingReferences)
        ):
            assert len(item.references) == 1, item.references

            return cls.Accept(item.references[0], metadata_item, plugin, elements, delayed_instruction_queue, apply_type_info_func, create_element_func, is_definition_only)

        element = Elements.ReferenceElement(
            reference=None,                             # Set below
            type_info=None,                             # Set below
            name=metadata_item.name,
            parent=None,                                # Set below
            source=metadata_item.Source,
            line=metadata_item.Line,
            column=metadata_item.Column,
            is_definition_only=is_definition_only,
            is_external=metadata_item.IsExternal,
        )

        # Parent
        cls._ApplyParent(element, metadata_item, elements, delayed_instruction_queue)

        # Reference
        cls._ApplyReference(element, item, elements, delayed_instruction_queue, create_element_func)

        # TypeInfo
        apply_type_info_func(item, metadata_item, element)

        return element

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnList(
        cls,
        item,
        metadata_item,
        plugin,                             # <Unused argument> pylint: disable = W0613
        elements,
        delayed_instruction_queue,
        apply_type_info_func,
        create_element_func,
        is_definition_only,
    ):                                      # <Parameters differ from overridden...> pylint: disable = W0221
        element = Elements.ListElement(
            reference=None,                             # Set below
            type_info=None,                             # Set below
            name=metadata_item.name,
            parent=None,                                # Set below
            source=metadata_item.Source,
            line=metadata_item.Line,
            column=metadata_item.Column,
            is_definition_only=is_definition_only,
            is_external=metadata_item.IsExternal,
        )

        # Parent
        cls._ApplyParent(element, metadata_item, elements, delayed_instruction_queue)

        # Reference
        cls._ApplyReference(element, item, elements, delayed_instruction_queue, create_element_func)

        # TypeInfo
        apply_type_info_func(item, metadata_item, element)

        return element

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnAny(
        cls,
        item,
        metadata_item,
        plugin,                             # <Unused argument> pylint: disable = W0613
        elements,
        delayed_instruction_queue,
        apply_type_info_func,
        create_element_func,                # <Unused argument> pylint: disable = W0613
        is_definition_only,
    ):                                      # <Parameters differ from overridden...> pylint: disable = W0221
        element = Elements.AnyElement(
            type_info=None,                             # Set below
            name=metadata_item.name,
            parent=None,                                # Set below
            source=metadata_item.Source,
            line=metadata_item.Line,
            column=metadata_item.Column,
            is_definition_only=is_definition_only,
            is_external=metadata_item.IsExternal,
        )

        # Parent
        cls._ApplyParent(element, metadata_item, elements, delayed_instruction_queue)

        # TypeInfo
        apply_type_info_func(item, metadata_item, element)

        return element

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnCustom(
        cls,
        item,
        metadata_item,
        plugin,                             # <Unused argument> pylint: disable = W0613
        elements,
        delayed_instruction_queue,
        apply_type_info_func,
        create_element_func,                # <Unused argument> pylint: disable = W0613
        is_definition_only,
    ):                                      # <Parameters differ from overridden...> pylint: disable = W0221
        element = Elements.CustomElement(
            type_info=None,                             # Set below
            name=metadata_item.name,
            parent=None,                                # Set below
            source=metadata_item.Source,
            line=metadata_item.Line,
            column=metadata_item.Column,
            is_definition_only=is_definition_only,
            is_external=metadata_item.IsExternal,
        )

        # Parent
        cls._ApplyParent(element, metadata_item, elements, delayed_instruction_queue)

        # TypeInfo
        apply_type_info_func(item, metadata_item, element)

        return element

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnExtension(
        cls,
        item,
        metadata_item,
        plugin,                             # <Unused argument> pylint: disable = W0613
        elements,
        delayed_instruction_queue,
        apply_type_info_func,
        create_element_func,                # <Unused argument> pylint: disable = W0613
        is_definition_only,
    ):                                      # <Parameters differ from overridden...> pylint: disable = W0221
        element = Elements.ExtensionElement(
            positional_arguments=item.positional_arguments,
            keyword_arguments=item.keyword_arguments,
            type_info=None,                             # Set below
            name=metadata_item.name,
            parent=None,                                # Set below
            source=metadata_item.Source,
            line=metadata_item.Line,
            column=metadata_item.Column,
            is_definition_only=is_definition_only,
            is_external=metadata_item.IsExternal,
        )

        # Parent
        cls._ApplyParent(element, metadata_item, elements, delayed_instruction_queue)

        # TypeInfo
        apply_type_info_func(item, metadata_item, element)

        return element

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _ApplyParent(element, item, elements, delayed_instruction_queue):
        if item.Parent is None:
            return

        parent_element = elements.get(item.Parent.Key, None)

        if parent_element is None:
            # ----------------------------------------------------------------------
            def ApplyParent():
                assert item.Parent.Key in elements, item.Parent.Key
                element.Parent = elements[item.Parent.Key]

            # ----------------------------------------------------------------------

            delayed_instruction_queue.append(ApplyParent)
        else:
            element.Parent = parent_element

    # ----------------------------------------------------------------------
    @classmethod
    def _CreateChildElements(cls, item, child_items, elements, delayed_instruction_queue, create_element_func):
        child_elements = []

        for child_item in child_items:
            # The element will be placed in the elements map
            if create_element_func(child_item) == False:
                continue

            child_elements.append(None)                 # This placeholder will be replaced in ApplyChild
            child_index = len(child_elements) - 1

            # ----------------------------------------------------------------------
            def ApplyChild(
                child_item=child_item,
                child_index=child_index,
            ):
                assert child_item.Key in elements, child_item.Key
                child_element = elements[child_item.Key]
                if isinstance(child_element, list):
                    # This can only happen with ExtensionElements that allow duplicates.
                    # Fortunately, these elements can never reference other elements, which means
                    # that this method will always be invoked directly rather than queued.
                    # Because of this, we can assume that the element to apply is the last
                    # item in the list.
                    assert child_element

                    child_element = child_element[-1]
                    assert isinstance(child_element, Elements.ExtensionElement), child_element
                    assert child_element._item == child_item

                assert child_element is not None

                assert child_index < len(child_elements)
                assert child_elements[child_index] is None
                child_elements[child_index] = child_element

            # ----------------------------------------------------------------------

            if elements.get(child_item.Key, None) is None:
                delayed_instruction_queue.append(ApplyChild)
            else:
                ApplyChild()

        return child_elements

    # ----------------------------------------------------------------------
    @classmethod
    def _ApplyReference(cls, element, item, elements, delayed_instruction_queue, create_element_func):
        assert len(item.references) == 1, item.references
        reference = item.references[0]

        # The element will be placed in the elements map
        create_element_func(reference)

        # ----------------------------------------------------------------------
        def ApplyReference():
            assert reference.Key in elements, reference.Key
            referenced_element = elements[reference.Key]
            assert referenced_element

            assert element.Reference is None, element.Reference
            element.Reference = referenced_element

        # ----------------------------------------------------------------------

        if elements.get(reference.Key, None) is None:
            delayed_instruction_queue.append(ApplyReference)
        else:
            ApplyReference()


# ----------------------------------------------------------------------
@staticderived
class _ApplyTypeInfoVisitor(ItemVisitor):
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnFundamental(cls, item, metadata_item, element, elements, delayed_instruction_queue): # <Parameters differ from overridden...> pylint: disable = W0221
        element.TypeInfo = cls._CreateFundamentalTypeInfo(metadata_item, item)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnCompound(cls, item, metadata_item, element, elements, delayed_instruction_queue): # <Parameters differ from overridden...> pylint: disable = W0221
        cls._ApplyClass(metadata_item, item, element, elements, delayed_instruction_queue, item.items)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnSimple(cls, item, metadata_item, element, elements, delayed_instruction_queue): # <Parameters differ from overridden...> pylint: disable = W0221
        cls._ApplyClass(metadata_item, item, element, elements, delayed_instruction_queue, item.items)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnVariant(cls, item, metadata_item, element, elements, delayed_instruction_queue): # <Parameters differ from overridden...> pylint: disable = W0221
        # Create a placeholder
        element.TypeInfo = AnyOfTypeInfo(
            [cls._PlaceholderTypeInfo()],
            arity=metadata_item.arity,
        )

        # ----------------------------------------------------------------------
        def ApplyTypeInfo():
            # Update this element's TypeInfo to include the TypeInfos of all possible values
            new_type_infos = []

            for child in element.Resolve().Children:
                child = child.Resolve()

                new_type_infos.append(child.TypeInfo)

            assert isinstance(element.TypeInfo, AnyOfTypeInfo), element.TypeInfo
            assert len(element.TypeInfo.ElementTypeInfos) == 1, element.TypeInfo.ElementTypeInfos
            assert isinstance(element.TypeInfo.ElementTypeInfos[0], cls._PlaceholderTypeInfo), element.TypeInfo.ElementTypeInfos

            element.TypeInfo.ElementTypeInfos[:] = new_type_infos

        # ----------------------------------------------------------------------

        delayed_instruction_queue.append(ApplyTypeInfo)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnReference(cls, item, metadata_item, element, elements, delayed_instruction_queue): # <Parameters differ from overridden...> pylint: disable = W0221
        assert len(item.references) == 1, item.references
        reference = item.references[0]

        cls.Accept(reference, metadata_item, element, elements, delayed_instruction_queue)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnList(cls, item, metadata_item, element, elements, delayed_instruction_queue): # <Parameters differ from overridden...> pylint: disable = W0221
        element.TypeInfo = ListTypeInfo(
            cls._PlaceholderTypeInfo(),
            arity=metadata_item.arity,
        )

        assert len(item.references) == 1, item.references
        reference = item.references[0]

        # ----------------------------------------------------------------------
        def ApplyTypeInfo():
            assert reference.Key in elements, reference.Key
            referenced_element = elements[reference.Key]
            assert referenced_element
            assert referenced_element.TypeInfo
            assert isinstance(element.TypeInfo.ElementTypeInfo, cls._PlaceholderTypeInfo), element.TypeInfo.ElementTypeInfo
            element.TypeInfo.ElementTypeInfo = referenced_element.TypeInfo

        # ----------------------------------------------------------------------

        referenced_element = elements.get(reference.Key, None)
        if referenced_element is None or referenced_element.TypeInfo is None:
            delayed_instruction_queue.append(ApplyTypeInfo)
        else:
            ApplyTypeInfo()

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnAny(item, metadata_item, element, elements, delayed_instruction_queue): # <Parameters differ from overridden...> pylint: disable = W0221
        element.TypeInfo = GenericTypeInfo(
            arity=metadata_item.arity,
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnCustom(item, metadata_item, element, elements, delayed_instruction_queue): # <Parameters differ from overridden...> pylint: disable = W0221
        element.TypeInfo = GenericTypeInfo(
            arity=metadata_item.arity,
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnExtension(item, metadata_item, element, elements, delayed_instruction_queue): # <Parameters differ from overridden...> pylint: disable = W0221
        element.TypeInfo = GenericTypeInfo(
            arity=metadata_item.arity,
        )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    class _PlaceholderTypeInfo(TypeInfo):
        Desc                                = DerivedProperty("")
        ConstraintsDesc                     = DerivedProperty("")
        ExpectedType                        = bool

        @staticmethod
        @override
        def _ValidateItemNoThrowImpl(item):             # <Parameters differ from overridden...> pylint: disable = W0221
            pass

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _CreateFundamentalTypeInfo(
        item,
        resolved_item,
        arity_override=None,
    ):
        assert len(resolved_item.references) == 1, resolved_item.references
        fundamental_attribute_info = resolved_item.references[0]

        kwargs = {"arity": arity_override or item.arity}

        for md in itertools.chain(fundamental_attribute_info.RequiredItems, fundamental_attribute_info.OptionalItems):
            if md.Name in item.metadata.Values:
                kwargs[md.Name] = item.metadata.Values[md.Name].Value
                del item.metadata.Values[md.Name]

        return fundamental_attribute_info.TypeInfoClass(**kwargs)

    # ----------------------------------------------------------------------
    @classmethod
    def _ApplyClass(cls, item, resolved_item, element, elements, delayed_instruction_queue, child_items):
        child_type_info_placeholders = OrderedDict()

        for child_item in child_items:
            if child_item.element_type == Elements.ExtensionElement:
                continue

            if child_item.ItemType == Item.ItemType.Definition:
                continue

            child_type_info_placeholders[child_item.name] = cls._PlaceholderTypeInfo()

        element.TypeInfo = ClassTypeInfo(
            # Placeholders values are overridden below
            child_type_info_placeholders,
            require_exact_match=bool(child_type_info_placeholders),
            arity=item.arity,
        )

        for child_item in child_items:
            if child_item.element_type == Elements.ExtensionElement:
                continue

            if child_item.ItemType == Item.ItemType.Definition:
                continue

            assert not child_item.ignore, child_item

            # ----------------------------------------------------------------------
            def ApplyChild(
                child_item=child_item,
            ):
                assert child_item.Key in elements, child_item.Key
                child_element = elements[child_item.Key]
                assert child_element
                assert child_element.TypeInfo
                assert not isinstance(child_element.TypeInfo, cls._PlaceholderTypeInfo), child_element.Name
                assert child_element.Name in element.TypeInfo.Items, child_element.Name
                assert isinstance(element.TypeInfo.Items[child_element.Name], cls._PlaceholderTypeInfo), element.TypeInfo.Items[child_element.Name]
                element.TypeInfo.Items[child_element.Name] = child_element.TypeInfo

            # ----------------------------------------------------------------------

            child_element = elements.get(child_item.Key, None)
            if child_element is None or child_element.TypeInfo is None:
                delayed_instruction_queue.append(ApplyChild)
            else:
                ApplyChild()
