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

from CommonEnvironment.Interface import staticderived
from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
from CommonEnvironment.TypeInfo.ClassTypeInfo import ClassTypeInfo
from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo

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
    from ...Plugin import PluginFlag

# ----------------------------------------------------------------------
def Transform(root, plugin):
    lookup = {}

    # ----------------------------------------------------------------------
    def Create(item, use_cache=True):
        if item.key is None:
            item.key = _CreateKey(item)

        if ( not use_cache or
             item.key not in lookup or
             (item.element_type == ExtensionElement and next(ext for ext in plugin.GetExtensions() if ext.Name == item.name).AllowDuplicates)
           ):
            # Signal that we are processing this item
            lookup[item.key] = None

            # Create the element
            is_definition_only = item.ItemType == Item.ItemType.Definition

            # ----------------------------------------------------------------------
            @staticderived
            class CreateElementVisitor(ItemVisitor):
                # ----------------------------------------------------------------------
                @staticmethod
                def OnFundamental(item):
                    return FundamentalElement( is_attribute=item.ItemType == Item.ItemType.Attribute and (plugin.Flags & PluginFlag.SupportAttributes),
                                               
                                               name=item.name,
                                               source=item.Source,
                                               line=item.Line,
                                               column=item.Column,
                                               is_definition_only=is_definition_only,
                                               is_external=item.IsExternal,
                                               
                                               # Secondary pass
                                               parent=None,
                                               type_info=None,
                                             )
            
                # ----------------------------------------------------------------------
                @staticmethod
                def OnCompound(item):
                    return CompoundElement( children=[ Create(child) for child in item.items ],
                                            base=Create(item.reference) if item.reference else None,

                                            name=item.name,
                                            source=item.Source,
                                            line=item.Line,
                                            column=item.Column,
                                            is_definition_only=is_definition_only,
                                            is_external=item.IsExternal,
                                            
                                            # Secondary pass
                                            parent=None,
                                            type_info=None,
                                            derived_elements=[],
                                          )

                # ----------------------------------------------------------------------
                @staticmethod
                def OnSimple(item):
                    raise Exception("BugBug: Abstract method")
            
                # ----------------------------------------------------------------------
                @staticmethod
                def OnAny(item):
                    return AnyElement( name=item.Name,
                                       source=item.Source,
                                       line=item.Line,
                                       column=item.Column,
                                       is_definition_only=is_definition_only,
                                       is_external=item.IsExternal,
                                       
                                       # Secondary pass
                                       parent=None,
                                     )
            
                # ----------------------------------------------------------------------
                @staticmethod
                def OnCustom(item):
                    return CustomElement( name=item.Name,
                                          source=item.Source,
                                          line=item.Line,
                                          column=item.Column,
                                          is_definition_only=is_definition_only,
                                          is_external=item.IsExternal,
                                          
                                          # Secondary pass
                                          parent=None,
                                        )
            
                # ----------------------------------------------------------------------
                @staticmethod
                def OnVariant(item):
                    raise Exception("BugBug: Abstract method")
            
                # ----------------------------------------------------------------------
                @staticmethod
                def OnList(item):
                    raise Exception("BugBug: Abstract method")
            
                # ----------------------------------------------------------------------
                @staticmethod
                def OnExtension(item):
                    raise Exception("BugBug: Abstract method")
            
                # ----------------------------------------------------------------------
                @staticmethod
                def OnReference(item):
                    raise Exception("BugBug: Abstract method")

            # ----------------------------------------------------------------------

            element = CreateElementVisitor().Accept(item)
            element._item = item

            if not use_cache:
                return element

            lookup[item.key] = element

        assert item.key in lookup, item.key
        return lookup[item.key]

    # ----------------------------------------------------------------------
    def ResolveParents(element, parent):
        assert element.Parent is None
        element.Parent = parent

        for child in getattr(element, "Children", []):
            ResolveParents(child, element)

    # ----------------------------------------------------------------------
    def SecondaryPass(element):
        if hasattr(element, "secondary_pass_info"):
            spi = element.secondary_pass_info
            del element.secondary_pass_info

            for name, value in six.iteritems(spi.__dict__):
                if name == "derived_elements":
                    pass # BugBug
                elif name == "reference":
                    pass # BugBug
                else:
                    assert False, name

        for child in getattr(element, "Children", []):
            SecondaryPass(child)

    # ----------------------------------------------------------------------
    def ApplyTypeInfo(element):
        # ----------------------------------------------------------------------
        @staticderived
        class ApplyVisitor(ElementVisitor):
            # ----------------------------------------------------------------------
            @staticmethod
            def OnFundamental(element):
                kwargs = { "arity" : element._item.arity,
                         }

                for md in itertools.chain( element._item.reference.RequiredMetadataItems,
                                           element._item.reference.OptionalMetadataItems,
                                         ):
                    if md.Name in element._item.metadata.Values:
                        kwargs[md.Name] = element._item.metadata.Values[md.Name].Value
                        del element._item.metadata.Values[md.Name]

                return element._item.reference.TypeInfoClass(**kwargs)
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnCompound(element):
                child_type_info = OrderedDict()

                for child in element.Children:
                    ApplyTypeInfo(child)

                    if hasattr(child, "TypeInfo"):
                        child_type_info[child.Name] = child.TypeInfo

                return AnyOfTypeInfo( [ DictTypeInfo(child_type_info),
                                        ClassTypeInfo(child_type_info),
                                      ],
                                      arity=element._item.arity,
                                    )
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnSimple(element):
                raise Exception("BugBug: Abstract property")
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnAny(element):
                assert False, "AnyElement doesn't have TypeInfo"
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnCustom(element):
                assert False, "CustomElement doesn't have TypeInfo"
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnExtension(element):
                assert False, "ExtensionElement doesn't have TypeInfo"
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnVariant(element):
                raise Exception("BugBug: Abstract property")
        
            # ----------------------------------------------------------------------
            @staticmethod
            def OnReference(element):
                ApplyTypeInfo(element.Reference)

                new_type_info = copy.deepcopy(element.Reference.TypeInfo)
                new_type_info.Arity = element._item.Arity

                return new_type_info

        # ----------------------------------------------------------------------

        if hasattr(element, "TypeInfo") and element.TypeInfo is None:
            element.TypeInfo = ApplyVisitor.Accept(element)

    # ----------------------------------------------------------------------
    def ApplyMetadata(element):
        element.ApplyMetadata(element._item.metadata.Values)

        for child in getattr(element, "Children", []):
            ApplyMetadata(child)

    # ----------------------------------------------------------------------
    def Cleanup(element):
        del element._item

        for child in getattr(element, "Children", []):
            Cleanup(child)

    # ----------------------------------------------------------------------

    root_element = Create(root)

    ResolveParents(root_element, None)
    SecondaryPass(root_element)
    ApplyTypeInfo(root_element)
    ApplyMetadata(root_element)
    Cleanup(root_element)

    return root_element

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _CreateKey(item):
    names = []

    item = self
    while item:
        names.append(item.name)
        item = item.Parent

    names.reverse()

    # Don't include the root element
    return tuple(names[1:])
