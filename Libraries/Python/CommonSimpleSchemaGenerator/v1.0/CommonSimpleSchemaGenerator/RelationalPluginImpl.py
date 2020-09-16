# ----------------------------------------------------------------------
# |
# |  RelationalPluginImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-02-03 20:11:12
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains functionality used when implementing a relational plugin"""

import inspect
import os
import pickle

from collections import namedtuple

from enum import Enum, auto
import six

import inflect as inflect_mod

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment import StringHelpers
from CommonEnvironment.Visitor import Visitor

from CommonEnvironment.TypeInfo.FundamentalTypes.BoolTypeInfo import BoolTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.DateTimeTypeInfo import DateTimeTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.EnumTypeInfo import EnumTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.GuidTypeInfo import GuidTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.IntTypeInfo import IntTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.StringTypeInfo import StringTypeInfo

# Note that these imports have already been import by SimpleSchemaGenerator and
# should always be available without explicit path information.
from SimpleSchemaGenerator.Schema.Attributes import Attribute
from SimpleSchemaGenerator.Schema.Elements import CompoundElement, ExtensionElement, FundamentalElement, ListElement, ReferenceElement
from SimpleSchemaGenerator.Schema.Exceptions import SimpleSchemaException
from SimpleSchemaGenerator.Plugin import Plugin as PluginBase, ParseFlag, Extension

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
class _Base(object):
    """Base class used by Fundamental, Relationship, and Object objects"""

    # ----------------------------------------------------------------------
    def __init__(self, element_or_source_line_column_tuple):
        if isinstance(element_or_source_line_column_tuple, tuple):
            element = None
            source, line, column = element_or_source_line_column_tuple
        else:
            element = element_or_source_line_column_tuple
            source = element.Source
            line = element.Line
            column = element.Column

        self.Element                        = element
        self.Source                         = source
        self.Line                           = line
        self.Column                         = column

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(
            self,
            Element=lambda key: None,
        )

# ----------------------------------------------------------------------
class Fundamental(_Base):
    """Scalar type (int, string, number, etc.)"""

    # ----------------------------------------------------------------------
    def __init__(
        self,
        element_or_source_line_column_tuple,

        name,
        type_info,

        is_identity,
        is_mutable,
        is_index,
        is_unique,
    ):
        super(Fundamental, self).__init__(element_or_source_line_column_tuple)

        self.Name                           = name
        self.TypeInfo                       = type_info
        self.IsIdentity                     = is_identity
        self.IsMutable                      = is_mutable
        self.IsIndex                        = is_index
        self.IsUnique                       = is_unique

# ----------------------------------------------------------------------
class Relationship(_Base):
    """Relationship between different objects/tables"""

    # ----------------------------------------------------------------------
    # |  Public Types
    class RelationshipType(Enum):
        OneToOne                            = auto()
        OneToMany                           = auto()
        ManyToMany                          = auto()

    # ----------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    def FromChild(cls, element):
        """Creates a relationship from a child to its parent (M:1)"""

        return cls(
            element,
            cls.RelationshipType.OneToMany,
            element.Object,
            element.Parent.Object,
            is_optional=False,
            is_mutable=False,
            is_parent_child=True,
            reference_name=element.Parent.Object.SingularSnakeName,
            backref_name=element.Object.PluralSnakeName,
        )

    # ----------------------------------------------------------------------
    @classmethod
    def FromReference(cls, referencing_element, referenced_element):
        """Creates a relationship from two elements"""

        if getattr(referencing_element, "backref_is_one_to_one", False):
            relationship_type = cls.RelationshipType.OneToOne
        elif (
            referencing_element.TypeInfo.Arity.IsOneOrMore
            or referencing_element.TypeInfo.Arity.IsZeroOrMore
        ):
            relationship_type = cls.RelationshipType.ManyToMany
        else:
            relationship_type = cls.RelationshipType.OneToMany

        if getattr(referencing_element, "backref", False):
            backref_name = getattr(
                referencing_element,
                "backref_name",
                referencing_element.Parent.Object.SingularSnakeName if relationship_type == cls.RelationshipType.OneToOne else referencing_element.Parent.Object.PluralSnakeName,
            )

            is_backref_optional = True
            is_backref_mutable = referencing_element.mutable and relationship_type == cls.RelationshipType.ManyToMany
        else:
            backref_name = None
            is_backref_optional = None
            is_backref_mutable = None

        return cls(
            referencing_element,
            relationship_type,
            referencing_element.Parent.Object,
            referenced_element.Object,
            is_optional=referencing_element.TypeInfo.Arity.Min == 0,
            is_mutable=getattr(referencing_element, "mutable", False),
            is_parent_child=False,
            reference_name=StringHelpers.ToSnakeCase(referencing_element.Name if relationship_type == cls.RelationshipType.ManyToMany else referencing_element.Name),
            backref_name=backref_name,
            is_backref_optional=is_backref_optional,
            is_backref_mutable=is_backref_mutable,
        )

    # ----------------------------------------------------------------------
    def __init__(
        self,
        location_element,
        relationship_type,
        referencing_obj,
        referenced_obj,
        is_optional,
        is_mutable,
        is_parent_child,
        reference_name,
        backref_name=None,
        is_backref_optional=None,
        is_backref_mutable=None,
    ):
        super(Relationship, self).__init__(location_element)

        self.RelationshipType               = relationship_type
        self.ReferencingObject              = referencing_obj
        self.ReferencedObject               = referenced_obj

        self.IsOptional                     = is_optional
        self.IsMutable                      = is_mutable
        self.IsParentChild                  = is_parent_child

        self.ReferenceName                  = reference_name
        self.BackrefName                    = backref_name

        self.IsBackrefOptional              = is_backref_optional
        self.IsBackrefMutable               = is_backref_mutable

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(
            self,
            Element=lambda key: None,
            ReferencingObject=lambda key: None,
            ReferencedObject=lambda key: None,
        )


# ----------------------------------------------------------------------
class Object(_Base):
    """Object instance of a row within a table"""

    # ----------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ----------------------------------------------------------------------
    class IdentityType(Enum):
        """Specifies how the concept of identity is represented within the object"""

        Integer                             = auto()    # Contains an integer id
        Basic                               = auto()    # Contains a guid id
        Simple                              = auto()    # Contains a guid id and creation date
        Deletable                           = auto()    # Contains a guid id, creation date, deleted date, and restored date

    # ----------------------------------------------------------------------
    class ItemType(Enum):
        """Defines the item type"""

        Fundamental                         = auto()
        Reference                           = auto()
        Backref                             = auto()

    # ----------------------------------------------------------------------
    Child                                   = namedtuple("Child", ["Name", "Item", "Type_"])

    # ----------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ----------------------------------------------------------------------
    @classmethod
    def FromElement(cls, element):
        # ----------------------------------------------------------------------
        def UniqueName():
            parts = []

            e = element

            while e:
                parts.append(StringHelpers.ToPascalCase(e.Name))
                e = e.Parent

            return "_".join(reversed(parts))

        # ----------------------------------------------------------------------

        return cls(
            next(it for it in cls.IdentityType if it.name == element.identity),
            UniqueName(),
            element.Name,
            element,
        )

    # ----------------------------------------------------------------------
    def __init__(
        self,
        identity,
        unique_name,
        name,
        element_or_source_line_column_tuple,
    ):
        super(Object, self).__init__(element_or_source_line_column_tuple)

        self.Identity                       = identity

        self.SingularName                   = name
        self.PluralName                     = inflect.plural(name)
        self.UniqueName                     = unique_name

        self.SingularPascalName             = StringHelpers.ToPascalCase(self.SingularName)
        self.PluralPascalName               = StringHelpers.ToPascalCase(self.PluralName)
        self.UniquePascalName               = StringHelpers.ToPascalCase(self.UniqueName)

        self.SingularSnakeName              = StringHelpers.ToSnakeCase(self.SingularName)
        self.PluralSnakeName                = StringHelpers.ToSnakeCase(self.PluralName)
        self.UniqueSnakeName                = StringHelpers.ToSnakeCase(self.UniqueName)

        self.constraints                    = []
        self.children                       = []

        # Add the identity info
        self.Add(
            Fundamental(
                (_script_name, inspect.currentframe().f_lineno, 0),
                "id",
                IntTypeInfo(min=0) if self.Identity == self.IdentityType.Integer else GuidTypeInfo(),
                is_identity=True,
                is_mutable=False,
                is_index=True,
                is_unique=True,
            ),
        )

        if self.Identity in [self.IdentityType.Simple, self.IdentityType.Deletable]:
            self.Add(
                Fundamental(
                    (_script_name, inspect.currentframe().f_lineno, 0),
                    "created",
                    DateTimeTypeInfo(),
                    is_identity=True,
                    is_mutable=False,
                    is_index=False,
                    is_unique=False,
                ),
            )

        if self.Identity == self.IdentityType.Deletable:
            for name in ["deleted", "restored"]:
                self.Add(
                    Fundamental(
                        (_script_name, inspect.currentframe().f_lineno, 0),
                        name,
                        DateTimeTypeInfo(
                            arity="?",
                        ),
                        is_identity=True,
                        is_mutable=False,
                        is_index=False,
                        is_unique=False,
                    ),
                )

    # ----------------------------------------------------------------------
    def Add(self, child):
        if isinstance(child, six.string_types):
            self.constraints.append(child)
            return

        # ----------------------------------------------------------------------
        def EnsureUniqueName(obj, name):
            existing = CommonEnvironment.Get(obj.children, lambda child: child.Name == name)
            if existing:
                raise SimpleSchemaException(
                    child.Source,
                    child.Line,
                    child.Column,
                    "The name '{}' in '{}' has already been defined by {} [{} <{}>]".format(
                        name,
                        self.UniqueName,
                        existing.Item.Source,
                        existing.Item.Line,
                        existing.Item.Column,
                    ),
                )

        # ----------------------------------------------------------------------

        if isinstance(child, Fundamental):
            name = child.Name
            type_ = self.ItemType.Fundamental

        elif isinstance(child, Relationship):
            name = child.ReferenceName
            type_ = self.ItemType.Reference

            if child.BackrefName:
                EnsureUniqueName(child.ReferencedObject, child.BackrefName)
                child.ReferencedObject.children.append(self.Child(child.BackrefName, child, self.ItemType.Backref))

        else:
            assert False, child

        EnsureUniqueName(self, name)

        self.children.append(self.Child(name, child, type_))

        return self


# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
class RelationalPluginImpl(PluginBase):

    # ----------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ----------------------------------------------------------------------
    Flags                                   = Interface.DerivedProperty(
        0
        # | ParseFlag.SupportAttributes
        | ParseFlag.SupportIncludeStatements
        # | ParseFlag.SupportConfigStatements
        | ParseFlag.SupportExtensionsStatements
        # | ParseFlag.SupportUnnamedDeclarations
        # | ParseFlag.SupportUnnamedObjects
        | ParseFlag.SupportNamedDeclarations
        | ParseFlag.SupportNamedObjects
        | ParseFlag.SupportRootDeclarations
        | ParseFlag.SupportRootObjects
        | ParseFlag.SupportChildDeclarations
        | ParseFlag.SupportChildObjects
        # | ParseFlag.SupportCustomElements
        # | ParseFlag.SupportAnyElements
        | ParseFlag.SupportReferenceElements
        | ParseFlag.SupportListElements
        # | ParseFlag.SupportSimpleObjectElements
        # | ParseFlag.SupportVariantElements
        # | ParseFlag.SupportDictionaryElements
        | ParseFlag.MaintainAugmentingReferences
        | ParseFlag.MaintainReferenceArity
    )

    # ----------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def IsValidEnvironment():
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GenerateCustomSettingsAndDefaults():
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GetExtensions():
        return [
            # constraint("SQL statement")
            Extension(
                "constraint",
                allow_duplicates=True,
            ),
        ]

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GetRequiredMetadataItems(item):
        if (
            item.element_type == CompoundElement
            and item.ItemType == type(item).ItemType.Standard
        ):
            return [
                Attribute(
                    "identity",
                    EnumTypeInfo([e.name for e in Object.IdentityType]),
                    is_metadata=True,
                ),
            ]

        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GetOptionalMetadataItems(item):
        if (
            item.element_type == CompoundElement
            and item.ItemType == type(item).ItemType.Standard
        ):
            return [
                Attribute(
                    "operations",
                    EnumTypeInfo(
                        [
                            # C - Create
                            # R - Read
                            # U - Update
                            # D - Delete
                            # E - Enumerate
                            "CRUDE",
                            "CRUD",
                            "CRU",
                            "CR",
                            "C",
                            "RUDE",
                            "RUD",
                            "RU",
                            "R",
                            "UDE",
                            "UD",
                            "U",
                            "DE",
                            "D",
                            "E",
                        ],
                    ),
                    default_value="CRUDE",
                    is_metadata=True,
                ),
            ]

        elif item.element_type == FundamentalElement:
            return [
                Attribute(
                    "mutable",
                    BoolTypeInfo(),
                    default_value=False,
                    is_metadata=True,
                ),
                Attribute(
                    "index",
                    BoolTypeInfo(),
                    default_value=False,
                    is_metadata=True,
                ),
                Attribute(
                    "unique",
                    BoolTypeInfo(),
                    default_value=False,
                    is_metadata=True,
                ),
            ]

        if item.element_type in [ListElement, ReferenceElement]:
            assert len(item.references) == 1, item.references
            reference = item.references[0]

            if reference.element_type == CompoundElement:
                return [
                    Attribute(
                        "mutable",
                        BoolTypeInfo(),
                        default_value=False,
                        is_metadata=True,
                    ),
                    Attribute(
                        "backref",
                        BoolTypeInfo(),
                        is_metadata=True,
                    ),
                    Attribute(
                        "backref_name",
                        StringTypeInfo(),
                        is_metadata=True,
                        validate_func=_ValidateBackrefName,
                    ),
                    Attribute(
                        "backref_is_one_to_one",
                        BoolTypeInfo(),
                        is_metadata=True,
                        validate_func=_ValidateBackrefIsOneToOne,
                    ),
                ]

        return []

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PreprocessContext(cls, context):

        # Augment all elements with their corresponding relational elements
        all_objects = []

        all_elements = pickle.loads(context["pickled_elements"])

        # Pass 1: Create objects
        for element in _EnumCompoundElements(all_elements):
            element.Object = Object.FromElement(element)
            all_objects.append(element.Object)

        # Pass 2: Relationships
        for element in _EnumCompoundElements(all_elements):
            if element.Parent:
                element.Object.Add(Relationship.FromChild(element))

            for child in cls._EnumerateChildren(
                element,
                include_definitions=False,
            ):
                if isinstance(child, FundamentalElement):
                    element.Object.Add(
                        Fundamental(
                            child,
                            StringHelpers.ToSnakeCase(child.Name),
                            child.TypeInfo,
                            is_identity=False,
                            is_mutable=child.mutable,
                            is_index=child.index,
                            is_unique=child.unique,
                        ),
                    )

                elif isinstance(child, CompoundElement):
                    # Nothing to do here, as the child will create a reference to
                    # this element when created.
                    pass

                elif isinstance(child, ExtensionElement):
                    content = child.PositionalArguments[0]

                    if content.startswith('"'): content = content[1:]
                    if content.endswith('"'): content = content[:-1]

                    element.Object.Add(content)

                elif isinstance(child, ReferenceElement):
                    resolved_element = child.Resolve()

                    if isinstance(resolved_element, FundamentalElement):
                        element.Object.Add(
                            Fundamental(
                                child,
                                StringHelpers.ToSnakeCase(child.Name),
                                child.TypeInfo,
                                is_identity=False,
                                is_mutable=getattr(child, "mutable", False),
                                is_index=getattr(child, "index", False),
                                is_unique=getattr(child, "unique", False),
                            ),
                        )
                    elif isinstance(resolved_element, CompoundElement):
                        element.Object.Add(Relationship.FromReference(child, resolved_element))
                    else:
                        assert False, resolved_element

                elif isinstance(child, ListElement):
                    assert isinstance(child.Reference, CompoundElement), child.Reference
                    element.Object.Add(Relationship.FromReference(child, child.Reference))

                else:
                    assert False, child

        cls.AllElements = all_elements
        cls.AllObjects = all_objects

        return context

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PostprocessContext(cls, context):
        # The following validation methods validate the relationship between elements where
        # as the validation associated with attributes only look at the associated element
        # in isolation.

        # ----------------------------------------------------------------------
        def ValidateDefinitionCompoundElementChildren(element):
            for child in cls._EnumerateChildren(
                element,
                include_standard=True,
                include_definitions=True,
            ):
                if not isinstance(child, FundamentalElement) or child.IsDefinitionOnly:
                    return {
                        "child_source": child.Source,
                        "child_line": child.Line,
                        "child_column": child.Column,
                    }

            return True

        # ----------------------------------------------------------------------
        def ValidateIntegerIdentityRelationships(element):
            for child in cls._EnumerateChildren(
                element,
                include_standard=True,
                include_definitions=False,
            ):
                if (
                    isinstance(child, (ListElement, ReferenceElement))
                    and child.TypeInfo.Arity.Min == 1
                    and child.TypeInfo.Arity.Max != 1
                ):
                    return False

            return True

        # ----------------------------------------------------------------------

        validation_data = [
            (
                "Top-level elements must be CompoundElements",
                lambda element: not element.Parent and not element.IsDefinitionOnly,
                lambda element: isinstance(element, CompoundElement),
            ),
            (
                "Elements must have an arity of 1, ?, +, or *",
                lambda element: not isinstance(element, ExtensionElement),
                lambda element: (
                    element.TypeInfo.Arity.IsSingle
                    or element.TypeInfo.Arity.IsOptional
                    or element.TypeInfo.Arity.IsOneOrMore
                    or element.TypeInfo.Arity.IsZeroOrMore
                ),
            ),
            (
                "CompoundElements must have an arity of *",
                lambda element: isinstance(element, CompoundElement) and not element.IsDefinitionOnly,
                lambda element: element.TypeInfo.Arity.IsZeroOrMore,
            ),
            (
                "CompoundElements with many-to-many references may not have the 'integer' identity, as it isn't possible to insert into the M2M table when the referencing id is not yet known",
                lambda element: isinstance(element, CompoundElement) and not element.IsDefinitionOnly and element.identity == Object.IdentityType.Integer,
                ValidateIntegerIdentityRelationships,
            ),
            (
                "FundamentalElements must have an arity of 1 or ?",
                lambda element: isinstance(element, FundamentalElement),
                lambda element: element.TypeInfo.Arity.IsSingle or element.TypeInfo.Arity.IsOptional,
            ),
            (
                "'Definition' CompoundElements must have an arity of 1",
                lambda element: isinstance(element, CompoundElement) and element.IsDefinitionOnly,
                lambda element: element.TypeInfo.Arity.IsSingle,
            ),
            (
                "'Definition' CompoundElements may not be referenced directory", # They can only appear as the base of another class
                lambda element: isinstance(element, ReferenceElement),
                lambda element: not isinstance(element.Resolve(), CompoundElement) and element.Resolve().IsDefinitionOnly,
            ),
            (
                "'constraint' elements must be associated with a CompoundElement",
                lambda element: isinstance(element, ExtensionElement) and element.Name == "constraint",
                lambda element: bool(element.Parent),
            ),
            (
                "'constraint' elements may only have one positional argument",
                lambda element: isinstance(element, ExtensionElement) and element.Name == "constraint",
                lambda element: len(element.PositionalArguments) == 1 and not element.KeywordArguments,
            ),
            (
                "'ReferenceElements' may only reference Compound- or Fundamental-Elements",
                lambda element: isinstance(element, ReferenceElement),
                lambda element: isinstance(element.Resolve(), (CompoundElement, FundamentalElement)),
            ),
            (
                "'ListElements' may only reference CompoundElements",
                lambda element: isinstance(element, ListElement),
                lambda element: isinstance(element.Reference.Resolve(), CompoundElement),
            ),
            (
                "'Definition' CompoundElements may only contain fundamental elements ({child_source} <{child_line} [{child_column}]>)",
                lambda element: isinstance(element, CompoundElement) and element.IsDefinitionOnly,
                ValidateDefinitionCompoundElementChildren,
            ),
        ]

        for element in cls.AllElements:
            for failure_message, applies_func, is_valid_func in validation_data:
                if not applies_func(element):
                    continue

                result = is_valid_func(element)
                if result is True:
                    continue

                if isinstance(result, dict):
                    failure_message = failure_message.format(**result)

                raise SimpleSchemaException(
                    element.Source,
                    element.Line,
                    element.Column,
                    failure_message,
                )

        return context

    # ----------------------------------------------------------------------
    # |
    # |  Protected Data
    # |
    # ----------------------------------------------------------------------
    AllElements                             = None # Set in PreprocessContext
    AllObjects                              = None # Set in PreprocessContext


# ----------------------------------------------------------------------
class ChildVisitor(Visitor):
    """Visitor for children"""

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def OnIdentity(item):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def OnFundamental(item):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def OnReference(item):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def OnBackref(item):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def Accept(cls, obj):
        for child in obj.children:
            if child.Type_ == Object.ItemType.Fundamental:
                if child.Item.IsIdentity:
                    cls.OnIdentity(child.Item)
                else:
                    cls.OnFundamental(child.Item)

            elif child.Type_ == Object.ItemType.Reference:
                cls.OnReference(child.Item)

            elif child.Type_ == Object.ItemType.Backref:
                cls.OnBackref(child.Item)

            else:
                assert False, child.Type_


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _EnumCompoundElements(element_or_elements):
    if isinstance(element_or_elements, list):
        for element in element_or_elements:
            yield from _EnumCompoundElements(element)

        return

    if not isinstance(element_or_elements, CompoundElement) or element_or_elements.IsDefinitionOnly:
        return

    yield element_or_elements

    for child in element_or_elements.Children:
        yield from _EnumCompoundElements(child)


# ----------------------------------------------------------------------
def _ValidateBackrefName(plugin, element):
    if not getattr(element, "backref", False):
        return "'backref' must be 'True' when 'backref_name' is set"

    return None


# ----------------------------------------------------------------------
def _ValidateBackrefIsOneToOne(plugin, element):
    if not getattr(element, "backref", False):
        return "'backref_is_one_to_one' must be 'True' when 'backref_name' is set"

    return None
