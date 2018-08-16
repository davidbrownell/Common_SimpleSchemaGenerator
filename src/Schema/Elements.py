# ----------------------------------------------------------------------
# |  
# |  Elements.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-12 11:24:42
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Definition for all Elements produced while compiling SimpleSchema files. Compiled
Elements are passed to Plugins to perform custom code generation.
"""

import os
import sys

import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.Interface import *
from CommonEnvironment.TypeInfo import Arity

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Element(Interface):
    """Data common to all Elements"""

    # ----------------------------------------------------------------------
    def __init__( self,
                  original_name,
                  name,
                  parent,
                  source,
                  line,
                  column,
                  is_definition_only,
                  is_external,
                ):
        self.GivenName                      = original_name
        self.Name                           = name
        self.Parent                         = parent
        self.Source                         = source
        self.Line                           = line
        self.Column                         = column
        self.IsDefinitionOnly               = is_definition_only
        self.IsExternal                     = is_external

        # This will be the metadata associated with the original item. Metadata
        # contains the raw info generated during parsing. AttributeNames is a list
        # that contains the name of all attributes whose values have been associated
        # with the object. All values are directly accessible on the class instance.
        self.Metadata                       = None                          
        self.AttributeNames                 = None

        self._cached_dotted_name            = None
        self._cached_dotted_type_name       = None

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl( self, 
                                                 Parent=lambda e: e.Name if e else "None",
                                               )

    # ----------------------------------------------------------------------
    @property
    def DottedName(self):
        if self._cached_dotted_name is None:
            self._cached_dotted_name = self._DottedNameImpl(lambda e: e.Name)

        return self._cached_dotted_name
            
    @property
    def DottedTypeName(self):
        if self._cached_dotted_type_name is None:
            self._cached_dotted_type_name = self._DottedNameImpl(lambda e: e.GivenName)

        return self._cached_dotted_type_name

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _DottedNameImpl(self, name_functor):
        names = []

        element = self
        while element:
            names.append(name_functor(element))
            element = element.Parent

        names.reverse()

        # Don't include the root
        names = names[1:]

        return '.'.join(names)

# ----------------------------------------------------------------------
class TypeInfoMixin(object):
    # ----------------------------------------------------------------------
    def __init__(self, type_info):
        self.TypeInfo                       = type_info

# ----------------------------------------------------------------------
class ArityMixin(object):
    # ----------------------------------------------------------------------
    def __init__(self, arity):
        self.Arity                          = arity

# ----------------------------------------------------------------------
class ParentMixin(object):
    # ----------------------------------------------------------------------
    def __init__(self, children):
        self.Children                       = children

    # ----------------------------------------------------------------------
    def AddChild(self, element):
        self.Children.append(element)
        element.Parent = self

        if not element.IsDefinitionOnly:
            self.TypeInfo.Items[element.Name] = element.TypeInfo

# ----------------------------------------------------------------------
class ReferenceMixin(object):
    # ----------------------------------------------------------------------
    def __init__( self,
                  reference,
                ):
        self.Reference                      = reference

    # ----------------------------------------------------------------------
    def Resolve(self):
        ref = self.Reference
        while isinstance(ref, ReferenceMixin):
            ref = ref.Reference

        return ref

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class FundamentalElement(TypeInfoMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  is_attribute,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        TypeInfoMixin.__init__(self, type_info)

        self.IsAttribute                    = is_attribute

# ----------------------------------------------------------------------
class CompoundElement(ArityMixin, ParentMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  arity,
                  children,
                  base,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ParentMixin.__init__(self, children)
        ArityMixin.__init__(self, arity)

        self.Base                           = base

# ----------------------------------------------------------------------
class SimpleElement(TypeInfoMixin, ArityMixin, ParentMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  fundamental_type_info,
                  arity,
                  children,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ParentMixin.__init__(self, children)
        ArityMixin.__init__(self, arity)
        TypeInfoMixin.__init__(self, fundamental_type_info)

        self.Attributes                     = self.Children

# ----------------------------------------------------------------------
class AnyElement(ArityMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  arity,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ArityMixin.__init__(self, arity)

# ----------------------------------------------------------------------
class CustomElement(ArityMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  arity,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ArityMixin.__init__(self, arity)

# ----------------------------------------------------------------------
class ExtensionElement(Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  arity,
                  positional_arguments,
                  keyword_arguments,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ArityMixin.__init__(self, arity)

        self.PositionalArguments            = positional_arguments
        self.KeywordArguments               = keyword_arguments
        
# ----------------------------------------------------------------------
class VariantElement(ArityMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  arity,
                  variations,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ArityMixin.__init__(self, arity)

        self.Variations                     = variations

# ----------------------------------------------------------------------
class ReferenceElement(TypeInfoMixin, ArityMixin, ReferenceMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  type_info_or_arity,       # type_info if referencing a FundamentalElement, arity otherwise
                  reference,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ReferenceMixin.__init__(self, reference)

        if isinstance(type_info_or_arity, Arity):
            ArityMixin.__init__(self, type_info_or_arity)
            TypeInfoMixin.__init__(self, None)
        else:
            ArityMixin.__init__(self, None)
            TypeInfoMixin.__init__(self, type_info_or_arity)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class ElementVisitor(Interface):

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnFundamental(element, *args, **kwargs):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnCompound(element, *args, **kwargs):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def OnCompound_VisitingChildren(element, *args, **kwargs):
        """Return False to prevent the visitation of children. Called after OnCompound."""
        return True
        
    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def OnCompound_VisitedChildren(element, *args, **kwargs):
        pass 
    
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnSimple(element, *args, **kwargs):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def OnSimple_VisitingChildren(element, *args, **kwargs):
        """Return False to prevent the visitation of children. Called after OnSimple."""
        return True
        
    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def OnSimple_VisitedChildren(element, *args, **kwargs):
        pass
        
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnAny(element, *args, **kwargs):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnCustom(element, *args, **kwargs):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnExtension(element, *args, **kwargs):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnVariant(element, *args, **kwargs):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnReference(element, *args, **kwargs):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @classmethod
    def Accept( cls, 
                element, 
                *args, 
                traverse=True,
                **kwargs
              ):
        """Calls the appropriate On___ method based on the element type"""

        lookup = { FundamentalElement       : cls.OnFundamental,
                   CompoundElement          : cls.OnCompound,
                   SimpleElement            : cls.OnSimple,
                   AnyElement               : cls.OnAny,
                   CustomElement            : cls.OnCustom,
                   VariantElement           : cls.OnVariant,
                   ExtensionElement         : cls.OnExtension,
                   ReferenceElement         : cls.OnReference,
                 }

        typ = type(element)

        if typ not in lookup:
            raise Exception("'{}' was not expected".format(typ))

        nonlocals = CommonEnvironment.Nonlocals( result=lookup[typ](element, *args, **kwargs),
                                               )

        if isinstance(element, ParentMixin) and traverse:
            visitation_lookup = { CompoundElement       : ( cls.OnCompound_VisitingChildren, cls.OnCompound_VisitedChildren ),
                                  SimpleElement         : ( cls.OnSimple_VisitingChildren, cls.OnSimple_VisitedChildren ),
                                }

            if typ not in visitation_lookup:
                raise Exception("'{}' was not expected".format(typ))

            visiting_func, visited_func = visitation_lookup[typ]

            if visiting_func(element, *args, **kwargs) != False:
                # ----------------------------------------------------------------------
                def CallVisited():
                    visited_result = visited_func(element, *args, **kwargs)
                    if visited_result is not None and nonlocals.result is None:
                        nonlocals.result = visited_result

                # ----------------------------------------------------------------------
                
                with CallOnExit(CallVisited):
                    for child in element.Children:
                        cls.Accept(child, *args, **kwargs)

        return nonlocals.result

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def CreateSimpleElementVisitor( on_fundamental_func=None,                   # def Func(element, *args, **kwargs)
                                on_compound_func=None,                      # def Func(element, *args, **kwargs)
                                on_compound_visiting_children_func=None,    # def Func(element, *args, **kwargs)
                                on_compound_visited_children_func=None,     # def Func(element, *args, **kwargs)
                                on_simple_func=None,                        # def Func(element, *args, **kwargs)
                                on_simple_visiting_children_func=None,      # def Func(element, *args, **kwargs)
                                on_simple_visited_children_func=None,       # def Func(element, *args, **kwargs)
                                on_any_func=None,                           # def Func(element, *args, **kwargs)
                                on_custom_func=None,                        # def Func(element, *args, **kwargs)
                                on_extension_func=None,                     # def Func(element, *args, **kwargs)
                                on_variant_func=None,                       # def Func(element, *args, **kwargs)
                                on_reference_func=None,                     # def Func(element, *args, **kwargs)
                                on_default_func=None,                       # def Func(element, *args, **kwargs)
                              ):
    """Creates an ElementVisitor instance implemented in terms of the non-None function arguments."""

    on_default_func = on_default_func or (lambda element, *args, **kwargs: None)

    on_fundamental_func = on_fundamental_func or on_default_func
    on_compound_func = on_compound_func or on_default_func
    on_compound_visiting_children_func = on_compound_visiting_children_func or on_default_func
    on_compound_visited_children_func = on_compound_visited_children_func or on_default_func
    on_simple_func = on_simple_func or on_default_func
    on_simple_visiting_children_func = on_simple_visiting_children_func or on_default_func
    on_simple_visited_children_func = on_simple_visited_children_func or on_default_func
    on_any_func = on_any_func or on_default_func
    on_custom_func = on_custom_func or on_default_func
    on_extension_func = on_extension_func or on_default_func
    on_variant_func = on_variant_func or on_default_func
    on_reference_func = on_reference_func or on_default_func

    # ----------------------------------------------------------------------
    @staticderived
    class SimpleElementVisitor(ElementVisitor):
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnFundamental(element, *args, **kwargs):
            return on_fundamental_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCompound(element, *args, **kwargs):
            return on_compound_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCompound_VisitingChildren(element, *args, **kwargs):
            return on_compound_visiting_children_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCompound_VisitedChildren(element, *args, **kwargs):
            return on_compound_visited_children_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSimple(element, *args, **kwargs):
            return on_simple_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSimple_VisitingChildren(element, *args, **kwargs):
            return on_simple_visiting_children_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSimple_VisitedChildren(element, *args, **kwargs):
            return on_simple_visited_children_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnAny(element, *args, **kwargs):
            return on_any_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCustom(element, *args, **kwargs):
            return on_custom_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExtension(element, *args, **kwargs):
            return on_extension_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnVariant(element, *args, **kwargs):
            return on_variant_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnReference(element, *args, **kwargs):
            return on_reference_func(element, *args, **kwargs)

    # ----------------------------------------------------------------------

    return SimpleElementVisitor
    