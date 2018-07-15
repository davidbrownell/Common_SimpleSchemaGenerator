# ----------------------------------------------------------------------
# |  
# |  Validate.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-12 10:10:20
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Validates Items in an Item hierarchy relative to each other"""

import itertools
import os
import sys

import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import StringHelpers

from CommonEnvironment.TypeInfo import ValidationException
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

from CommonEnvironmentEx.Package import ApplyRelativePackage

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------
    
with ApplyRelativePackage():
    from ..Exceptions import *
    from ..Metadata import *
    from ...Plugin import PluginFlag

# ----------------------------------------------------------------------
def Validate( root,
              plugin,
              filter_unsupported_extensions,
              filter_unsupported_metadata,
            ):
    # ----------------------------------------------------------------------
    def Impl(item, functor):
        functor(item)

        for child in item.items:
            Impl(child, functor)

    # ----------------------------------------------------------------------

    visited = set()
    extension_names = { ext.Name for ext in plugin.GetExtensions() }
    
    Impl(root, lambda item: _ValidateAcyclic(visited, item))
    Impl(root, lambda item: _ValidateSupported(plugin.Flags, item))
    Impl(root, lambda item: _ValidateExtensions(filter_unsupported_extensions, extension_names, item))
    Impl(root, _ValidateUniqueNames)
    Impl(root, _ValidateVariantArity)
    Impl(root, lambda item: _ValidateMetadata(filter_unsupported_metadata, item))
    Impl(root, _ValidateCustomMetadata)

    return root

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ValidateAcyclic(visited, item, stack=None):
    for item in item.Enumerate():
        if item in visited:
            return

        if stack:
            if item in stack:
                raise ValidateCycleException( item.Source,
                                              item.Line,
                                              item.Column,
                                              info=StringHelpers.LeftJustify( '\n'.join([ "- {name} ({source} [{line} <{column}>])".format( name=i.name,
                                                                                                                                            source=i.Source,
                                                                                                                                            line=i.Line,
                                                                                                                                            column=i.Column,
                                                                                                                                          )
                                                                                          for i in stack + [ item, ]
                                                                                        ]).rstrip(),
                                                                              4,
                                                                              skip_first_line=False,
                                                                            ),
                                            )
        else:
            stack = []

        stack.append(item)
        with CallOnExit(stack.pop):
            for child in item.items:
                _ValidateAcyclic(visited, child, stack)

        visited.add(item)

# ----------------------------------------------------------------------
def _ValidateSupported(plugin_flags, item):
    for item in Item.Enumerate():
        if item.element_type == CustomElement and not plugin_flags & PluginFlag.SupportCustomElements:
            raise ValidateUnsupportedCustomElementsException(item.Source, item.Line, item.Column)

        if item.element_type == AnyElement and not plugin_flags & PluginFlag.SupportAnyElements:
            raise ValidateUnsupportedAnyElementsException(item.Source, item.Line, item.Column)

        if item.element_type == AliasElement and not plugin_flags & PluginFlag.SupportAliasElements:
            raise ValidateUnsupportedAliasElementsException(item.Source, item.Line, item.Column)

        # BugBug: Convert simple?
        if item.element_type == SimpleElement and not plugin_flags & PluginFlag.SupportSimpleObjectElements:
            raise ValidateUnsupportedSimpleObjectElementsException(item.Source, item.Line, item.Column)

        if item.element_type == VariantElement and not plugin_flags & PluginFlag.SupportVariantElements:
            raise ValidateUnsupportedVariantElementsException(item.Source, item.Line, item.Column)

# ----------------------------------------------------------------------
def _ValidateExtensions(filter_unsupported_extensions, valid_extension_names, item):
    index = 0

    while index < len(item.items):
        if item.items[index].DeclarationType == Item.DeclarationType.Extension:
            name = item.items[index].name
            if name not in valid_extension_names:
                if filter_unsupported_extensions:
                    del item.items[index]
                    continue

                raise ValidateInvalidExtensionException( item.Source,
                                                         item.Line,
                                                         item.Column,
                                                         name=name,
                                                       )
        index += 1

# ----------------------------------------------------------------------
def _ValidateUniqueNames(item, names=None):
    names = names or {}

    for child in item.items:
        if child.name in names:
            raise ValidateDuplicateNameException( child.Source,
                                                  child.Line,
                                                  child.Column,
                                                  name=child.name,
                                                  original_source=names[child.name].Source,
                                                  original_line=names[child.name].Line,
                                                  original_column=names[child.name].Column,
                                                )

        names[child.name] = child

    if isinstance(item.reference, Item):
        _ValidateUniqueNames(item.reference, names)

# ----------------------------------------------------------------------
def _ValidateVariantArity(item):
    if Item.element_type != VariantElement:
        return

    original_item = item

    for index, item in enumerate(item.Enumerate()):
        if not item.arity.IsSingle:
            raise ValidateInvalidVariantArityException( item.Source,
                                                        item.Line,
                                                        item.Column,
                                                        index=index,
                                                      )

# ----------------------------------------------------------------------
def _ValidateMetadata(filter_unsupported_metadata, item):
    for item in item.Enumerate():
        # Ensure that required values are present
        for md in item.metadata.RequiredMetadataItems:
            if md.Name not in item.metadata.Values:
                raise ValidateMissingMetadataException( item.Source,
                                                        item.Line,
                                                        item.Column,
                                                        name=md.Name,
                                                      )

        # Verify / eliminate / Convert extra metadata
        md_lookup = { md.Name : md for md in itertools.chain( item.metadata.RequiredMetadataItems,
                                                              item.metadata.OptionalMetadataItems,
                                                            ) }

        md_keys = list(six.iterkeys(item.metadata.Values))
        
        for k in md_keys:
            if k not in md_lookup:
                if filter_unsupported_metadata:
                    del item.metadata.Values[k]
                    continue

                raise ValidateExtraneousMetadataException( item.Source,
                                                           item.Line,
                                                           item.Column,
                                                           name=k,
                                                         )

            md = md_lookup[k]
            value = item.metadata.Values[k]

            try:
                if isinstance(value, six.string_types):
                    value = StringSerialization.DeserializeItem(md.TypeInfo, value)
                else:
                    md.TypeInfo.ValidateItem(value)

            except ValidationException as ex:
                raise ValidateInvalidMetadataException( item.Source, 
                                                        item.Line,
                                                        item.Column,
                                                        name=k,
                                                        value=value,
                                                        reason=str(ex),
                                                      )

            item.metadata.Values[k] = value

# ----------------------------------------------------------------------
def _ValidateCustomMetadata(item):
    # 'suppress_polymorphic' is only valid for use on items with a parent that has 'polymorphic' defined as true
    if item.element_type == CompoundElement and "suppress_polymorphic" in item.metadata.Values and item.metadata.Values["suppression_polymorphic"].Value:
        ref = item.reference
        while ref:
            if "polymorphic" in ref.metadata.Values and ref.metadata.Values["polymorphic"].Value:
                break

            ref = ref.reference

        if not ref:
            raise ValidateInvalidSuppressPolymorphicException( item.Source,
                                                               item.Line,
                                                               item.Column,
                                                             )

    # 'unique_key' must be the name of a fundamental, defined child with an arity of 1
    if item.arity.IsCollection and "unique_key" in item.metadata.Values:
        unique_key = item.metadata.Values["unique_key"].Value
        unique_key_element = None

        for child in item.items:
            if child.name == unique_key:
                unique_key_element = child
                break

        if unique_key_element is None:
            raise ValidateMissingUniqueKeyException( item.Source,
                                                     item.Line,
                                                     item.Column,
                                                     name=unique_key,
                                                   )

        if ( unique_key_element.element_type != FundamentalElement or
             not unique_key_element.arity.IsSingle or
             unique_key_element.ItemType == Item.ItemType.Definition
           ):
            raise ValidateInvalidUniqueKeyException( item.Source,
                                                     item.Line,
                                                     item.Column,
                                                   )

    # 'refines_arity' is only valid on references
    if item.arity.IsCollection and "refines_arity" in item.metadata.Values and item.metadata.Values["refines_arity"] and item.element_type != ReferenceElement:
        raise ValidateInvalidRefinesArityException( item.Source,
                                                    item.Line,
                                                    item.Column,
                                                  )
