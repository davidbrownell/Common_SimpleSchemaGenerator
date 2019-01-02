# ----------------------------------------------------------------------
# |  
# |  Elements.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-12 11:24:42
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""\
Definition for all Elements produced while compiling SimpleSchema files. Compiled
Elements are passed to Plugins to perform custom code generation.
"""

import os

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.Interface import Interface, abstractmethod, extensionmethod, override, staticderived

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
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
                  type_info,
                  name,
                  parent,
                  source,
                  line,
                  column,
                  is_definition_only,
                  is_external,
                ):
        self.TypeInfo                       = type_info
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
            names = []

            element = self
            while element:
                names.append(element.Name)
                element = element.Parent

            names.reverse()

            self._cached_dotted_name = '.'.join(names)

        return self._cached_dotted_name

    # ----------------------------------------------------------------------
    def Resolve(self):
        return self
        
# ----------------------------------------------------------------------
class ChildrenMixin(object):
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
class FundamentalElement(Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  is_attribute,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        
        self.IsAttribute                    = is_attribute

# ----------------------------------------------------------------------
class CompoundElement(ChildrenMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  children,
                  base,
                  derived,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ChildrenMixin.__init__(self, children)
        
        self.Base                           = base
        self.Derived                        = derived

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl( self,
                                                 Parent=lambda e: e.Name if e else "None",
                                                 Base=lambda b: b.DottedName if b else "<None>",
                                                 Derived=lambda derived: [ d.DottedName for d in derived ],
                                               )
                                               
# ----------------------------------------------------------------------
class SimpleElement(ChildrenMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  attributes,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ChildrenMixin.__init__(self, attributes)
        
        # The referenced fundamental type's TypeInfo is available as
        # self.TypeInfo.Items[None].

        self.Attributes                     = self.Children

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl( self,
                                                 Parent=lambda e: e.Name if e else "None",
                                                 Children=lambda e: None,
                                               )

# ----------------------------------------------------------------------
class VariantElement(ChildrenMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  variations,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ChildrenMixin.__init__(self, variations)

        self.Variations                     = self.Children

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl( self,
                                                 Parent=lambda e: e.Name if e else "None",
                                                 Children=lambda e: None,
                                               )
    
# ----------------------------------------------------------------------
class ReferenceElement(ReferenceMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  reference,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ReferenceMixin.__init__(self, reference)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl( self,
                                                 Parent=lambda e: e.Name if e else "None",
                                                 Reference=lambda r: r.Name if r else "None",
                                               )

# ----------------------------------------------------------------------
class ListElement(ReferenceMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  reference,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ReferenceMixin.__init__(self, reference)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl( self,
                                                 Parent=lambda e: e.Name if e else "None",
                                                 Reference=lambda r: r.Name,
                                               )
    
# ----------------------------------------------------------------------
class AnyElement(Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)

# ----------------------------------------------------------------------
class CustomElement(Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)

# ----------------------------------------------------------------------
class ExtensionElement(Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  positional_arguments,
                  keyword_arguments,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)

        self.PositionalArguments            = positional_arguments
        self.KeywordArguments               = keyword_arguments
        
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class ElementVisitor(Interface):

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def OnEnteringElement(element, *args, **kwargs):
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def OnExitingElement(element, *args, **kwargs):
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnFundamental(element, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnCompound(element, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def OnCompound_VisitingChildren(element, *args, **kwargs):              # <Unused argument> pylint: disable = W0613
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
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def OnSimple_VisitingChildren(element, *args, **kwargs):                # <Unused argument> pylint: disable = W0613
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
    def OnVariant(element, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnReference(element, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnList(element, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnAny(element, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnCustom(element, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnExtension(element, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def Accept( cls, 
                element_or_elements, 
                *args, 
                traverse=True,
                include_dotted_names=None,  # set of the dotted_names of elements that should be traversed.
                **kwargs
              ):
        """Calls the appropriate On___ method based on the element type"""

        if include_dotted_names is None:
            should_traverse_func = lambda element: True
        else:
            should_traverse_func = lambda element: element.DottedName in include_dotted_names

        lookup = { FundamentalElement       : cls.OnFundamental,
                   CompoundElement          : cls.OnCompound,
                   SimpleElement            : cls.OnSimple,
                   VariantElement           : cls.OnVariant,
                   ReferenceElement         : cls.OnReference,
                   ListElement              : cls.OnList,
                   AnyElement               : cls.OnAny,
                   CustomElement            : cls.OnCustom,
                   ExtensionElement         : cls.OnExtension,
                 }

        if isinstance(element_or_elements, list):
            elements = element_or_elements
        else:
            elements = [ element_or_elements, ]

        for element in elements:
            if not should_traverse_func(element):
                continue

            typ = type(element)

            if typ not in lookup:
                raise Exception("'{}' was not expected ({})".format(typ, element))

            cls.OnEnteringElement(element, *args, **kwargs)
            with CallOnExit(lambda: cls.OnExitingElement(element, *args, **kwargs)):
                nonlocals = CommonEnvironment.Nonlocals( result=lookup[typ](element, *args, **kwargs),
                                                       )

                if isinstance(element, ChildrenMixin) and traverse:
                    if not isinstance(element, VariantElement):
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

                if nonlocals.result is not None:
                    return nonlocals.result

        return None

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def CreateElementVisitor( on_entering_element=None,                         # def Func(element, *args, **kwargs)
                          on_exiting_element=None,                          # def Func(element, *args, **kwargs)
                          on_fundamental_func=None,                         # def Func(element, *args, **kwargs)
                          on_compound_func=None,                            # def Func(element, *args, **kwargs)
                          on_compound_visiting_children_func=None,          # def Func(element, *args, **kwargs)
                          on_compound_visited_children_func=None,           # def Func(element, *args, **kwargs)
                          on_simple_func=None,                              # def Func(element, *args, **kwargs)
                          on_simple_visiting_children_func=None,            # def Func(element, *args, **kwargs)
                          on_simple_visited_children_func=None,             # def Func(element, *args, **kwargs)
                          on_variant_func=None,                             # def Func(element, *args, **kwargs)
                          on_reference_func=None,                           # def Func(element, *args, **kwargs)
                          on_list_func=None,                                # def Func(element, *args, **kwargs)
                          on_any_func=None,                                 # def Func(element, *args, **kwargs)
                          on_custom_func=None,                              # def Func(element, *args, **kwargs)
                          on_extension_func=None,                           # def Func(element, *args, **kwargs)
                          on_default_func=None,                             # def Func(element, *args, **kwargs)
                        ):
    """Creates an ElementVisitor instance implemented in terms of the non-None function arguments."""

    on_default_func = on_default_func or (lambda element, *args, **kwargs: None)

    on_entering_element = on_entering_element or on_default_func
    on_exiting_element = on_exiting_element or on_default_func
    on_fundamental_func = on_fundamental_func or on_default_func
    on_compound_func = on_compound_func or on_default_func
    on_compound_visiting_children_func = on_compound_visiting_children_func or on_default_func
    on_compound_visited_children_func = on_compound_visited_children_func or on_default_func
    on_simple_func = on_simple_func or on_default_func
    on_simple_visiting_children_func = on_simple_visiting_children_func or on_default_func
    on_simple_visited_children_func = on_simple_visited_children_func or on_default_func
    on_variant_func = on_variant_func or on_default_func
    on_reference_func = on_reference_func or on_default_func
    on_list_func = on_list_func or on_default_func
    on_any_func = on_any_func or on_default_func
    on_custom_func = on_custom_func or on_default_func
    on_extension_func = on_extension_func or on_default_func
    
    # ----------------------------------------------------------------------
    @staticderived
    class ThisElementVisitor(ElementVisitor):
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnEnteringElement(element, *args, **kwargs):
            return on_entering_element(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExitingElement(element, *args, **kwargs):
            return on_exiting_element(element, *args, **kwargs)

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
        def OnVariant(element, *args, **kwargs):
            return on_variant_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnReference(element, *args, **kwargs):
            return on_reference_func(element, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnList(element, *args, **kwargs):
            return on_list_func(element, *args, **kwargs)

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

    return ThisElementVisitor
