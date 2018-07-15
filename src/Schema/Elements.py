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
from CommonEnvironment.Interface import *

from CommonEnvironmentEx.Package import ApplyRelativePackage

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with ApplyRelativePackage():
    from .Exceptions import *

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

        # This will be the metadata associated with the original item (including Source, Line, and Column info).
        # Individual values will be placed in Attributes and each key-value-pair will be made members of the class.
        self.Metadata                       = None                          
        self.AttributeNames                 = None

        self._cached_dotted_name            = None
        self._cached_dotted_type_name       = None

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

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

        return '.'.join(names)

# ----------------------------------------------------------------------
class TypeInfoMixin(object):
    # ----------------------------------------------------------------------
    def __init__(self, type_info):
        self.TypeInfo                       = type_info

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

    # BugBug: Resolve?

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
class CompoundElement(TypeInfoMixin, ParentMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  children,
                  base,
                  derived_elements,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ParentMixin.__init__(self, children)
        TypeInfoMixin.__init__(self, type_info)

        self.Base                           = base
        self.DerivedElements                = derived_elements

# ----------------------------------------------------------------------
class SimpleElement(TypeInfoMixin, ParentMixin, Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  type_info,
                  value_name,
                  children,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        ParentMixin.__init__(self, children)
        TypeInfoMixin.__init__(self, type_info)

        self.ValueName                      = value_name
        self.Attributes                     = self.Children

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
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)

# ----------------------------------------------------------------------
class VariantElement(Element):
    # ----------------------------------------------------------------------
    def __init__( self,
                  variations,
                  *args,
                  **kwargs
                ):
        Element.__init__(self, *args, **kwargs)
        self.Variations                     = variations

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
    @abstractmethod
    def OnSimple(element, *args, **kwargs):
        raise Exception("Abstract property")

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
    def Accept(cls, element, *args, **kwargs):
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

        return lookup[typ](element, *args, **kwargs)
