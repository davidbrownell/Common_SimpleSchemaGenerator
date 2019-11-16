# ----------------------------------------------------------------------
# |
# |  Validate.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-12 10:10:20
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Validates Items in an Item hierarchy relative to each other"""

import itertools
import os

import six

import CommonEnvironment

from CommonEnvironment.TypeInfo import ValidationException
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import (
    StringSerialization,
)

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from .Item import Item

    from .. import Attributes
    from .. import Elements
    from .. import Exceptions

    from ...Plugin import ParseFlag

# ----------------------------------------------------------------------
def Validate(root, plugin, filter_unsupported_extensions, filter_unsupported_metadata):
    # ----------------------------------------------------------------------
    def Impl(item, functor):
        functor(item)

        for child in item.items:
            Impl(child, functor)

    # ----------------------------------------------------------------------

    extension_names = {ext.Name for ext in plugin.GetExtensions()}
    extensions_allowing_duplicate_names = {
        ext.Name for ext in plugin.GetExtensions() if ext.AllowDuplicates
    }

    Impl(root, lambda item: _ValidateSupported(plugin.Flags, item))
    Impl(root, lambda item: _ValidateUniqueNames(extensions_allowing_duplicate_names, item))
    Impl(root, _ValidateVariantArity)
    Impl(root, lambda item: _ValidateMetadata(filter_unsupported_metadata, item))
    Impl(root, _ValidateSimpleElements)
    Impl(
        root,
        lambda item: _ValidateExtension(filter_unsupported_extensions, extension_names, item),
    )
    Impl(root, _ValidateReference)

    return root


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ValidateSupported(plugin_flags, item):
    for item in item.Enumerate():
        if (
            item.element_type == Elements.CustomElement
            and not plugin_flags & ParseFlag.SupportCustomElements
        ):
            raise Exceptions.ValidateUnsupportedCustomElementsException(
                item.Source,
                item.Line,
                item.Column,
            )

        if (
            item.element_type == Elements.AnyElement
            and not plugin_flags & ParseFlag.SupportAnyElements
        ):
            raise Exceptions.ValidateUnsupportedAnyElementsException(
                item.Source,
                item.Line,
                item.Column,
            )

        if (
            item.element_type == Elements.ReferenceElement
            and not plugin_flags & ParseFlag.SupportReferenceElements
        ):
            raise Exceptions.ValidateUnsupportedReferenceElementsException(
                item.Source,
                item.Line,
                item.Column,
            )

        if (
            item.element_type == Elements.ListElement
            and not plugin_flags & ParseFlag.SupportListElements
        ):
            raise Exceptions.ValidateUnsupportedListElementsException(
                item.Source,
                item.Line,
                item.Column,
            )

        if (
            item.element_type == Elements.VariantElement
            and not plugin_flags & ParseFlag.SupportVariantElements
        ):
            raise Exceptions.ValidateUnsupportedVariantElementsException(
                item.Source,
                item.Line,
                item.Column,
            )


# ----------------------------------------------------------------------
def _ValidateUniqueNames(
    extensions_allowing_duplicate_names,
    item,
    names=None,
):
    names = names or {}

    for child in item.items:
        if (
            child.element_type == Elements.ExtensionElement
            and child.name in extensions_allowing_duplicate_names
        ):
            continue

        if child.name in names:
            raise Exceptions.ValidateDuplicateNameException(
                child.Source,
                child.Line,
                child.Column,
                name=child.name,
                original_source=names[child.name].Source,
                original_line=names[child.name].Line,
                original_column=names[child.name].Column,
            )

        names[child.name] = child

    for ref in item.references:
        if isinstance(ref, Item):
            _ValidateUniqueNames(extensions_allowing_duplicate_names, ref, names)


# ----------------------------------------------------------------------
def _ValidateVariantArity(item):
    if item.element_type != Elements.VariantElement:
        return

    for index, item in enumerate(item.Enumerate()):
        if not item.arity.IsSingle:
            raise Exceptions.ValidateInvalidVariantArityException(
                item.Source,
                item.Line,
                item.Column,
                index=index,
            )


# ----------------------------------------------------------------------
def _ValidateMetadata(filter_unsupported_metadata, item):
    for item in item.Enumerate():
        # Ensure that required values are present
        for md in item.metadata.RequiredItems:
            if md.Name not in item.metadata.Values:
                raise Exceptions.ValidateMissingAttributeException(
                    item.Source,
                    item.Line,
                    item.Column,
                    name=md.Name,
                )

        # Verify / eliminate / Convert extra metadata
        md_lookup = {
            md.Name: md
            for md in itertools.chain(item.metadata.RequiredItems, item.metadata.OptionalItems)
        }

        md_keys = list(six.iterkeys(item.metadata.Values))

        for k in md_keys:
            if k not in md_lookup:
                if filter_unsupported_metadata:
                    del item.metadata.Values[k]
                    continue

                raise Exceptions.ValidateExtraneousAttributeException(
                    item.Source,
                    item.Line,
                    item.Column,
                    name=k,
                )

            md = md_lookup[k]
            value = item.metadata.Values[k].Value

            try:
                if isinstance(value, six.string_types):
                    value = StringSerialization.DeserializeItem(md.TypeInfo, value)
                else:
                    md.TypeInfo.Validate(value)

            except ValidationException as ex:
                raise Exceptions.ValidateInvalidAttributeException(
                    item.Source,
                    item.Line,
                    item.Column,
                    name=k,
                    reason=str(ex),
                )

            item.metadata.Values[k] = item.metadata.Values[k]._replace(
                Value=value,
            )


# ----------------------------------------------------------------------
def _ValidateSimpleElements(item):
    if item.element_type != Elements.SimpleElement:
        return

    # ----------------------------------------------------------------------
    def ValidateAttribute(child):
        if child.ItemType != Item.ItemType.Attribute:
            return False

        if child.arity.Max != 1:
            return False

        while child.element_type == Elements.ReferenceElement:
            assert len(child.references) == 1, child.references
            child = child.references[0]

        return child.element_type == Elements.FundamentalElement

    # ----------------------------------------------------------------------

    # Validate that this element is only based on 1 FundamentalElement
    found_simple = False

    for reference in item.references:
        if (
            isinstance(reference, Attributes.FundamentalAttributeInfo)
            or reference.element_type == Elements.SimpleElement
        ):
            if found_simple:
                raise Exceptions.ValidateInvalidSimpleReferenceException(
                    item.Source,
                    item.Line,
                    item.Column,
                )
            found_simple = True

    # Validate the attributes
    for child in item.items:
        if not ValidateAttribute(child):
            raise Exceptions.ValidateInvalidSimpleChildException(
                child.Source,
                child.Line,
                child.Column,
            )


# ----------------------------------------------------------------------
def _ValidateExtension(filter_unsupported_extensions, valid_extension_names, item):
    if item.element_type != Elements.ExtensionElement:
        return

    if item.name not in valid_extension_names:
        if filter_unsupported_extensions:
            item.ignore = True
        else:
            raise Exceptions.ValidateInvalidExtensionException(
                item.Source,
                item.Line,
                item.Column,
                name=item.name,
            )


# ----------------------------------------------------------------------
def _ValidateReference(item):
    if item.element_type != Elements.ReferenceElement:
        return

    ref = item
    while len(ref.references) == 1 and isinstance(ref.references[0], Item):
        ref = ref.references[0]

    if ref.element_type == Elements.ExtensionElement:
        raise Exceptions.ValidateInvalidReferenceException(item.Source, item.Line, item.Column)
