# ----------------------------------------------------------------------
# |
# |  Attributes.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-12 10:24:18
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-22.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the Attributes object and default attribute values"""

import os

from collections import OrderedDict

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Visitor import Visitor as FundamentalTypesVisitor

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from . import Elements
    from ..Plugin import ParseFlag

# ----------------------------------------------------------------------
# <Wrong hanging indentation> pylint: disable = C0330

# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
class Attribute(object):
    """Attribute that can be applied to SimpleSchema elements"""

    class DoesNotExist(object):
        pass

    # ----------------------------------------------------------------------
    def __init__(
        self,
        name,
        type_info,
        default_value=DoesNotExist,         # Can be specific value or def Func(item) -> value
        validate_func=None,                 # Called when the attribute item is present:
                                            #   def Func(plugin, element) -> string if error
        missing_validate_func=None,         # Called when the attribute item is not present:
                                            #   def Func(plugin, element) -> string if error
        is_metadata=False,                  # In generic terms, this value should be true if the attribute should be considered metadata and
                                            # does not change the type information of the corresponding element. This is a general statement,
                                            # is often something that is determined by different plugins.
    ):
        self.Name                           = name
        self.TypeInfo                       = type_info
        self.DefaultValue                   = default_value
        self.ValidateFunc                   = validate_func
        self.MissingValidateFunc            = missing_validate_func
        self.IsMetadata                     = is_metadata

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class AttributeInfo(object):
    # ----------------------------------------------------------------------
    def __init__(
        self,
        required_items=None,
        optional_items=None,
    ):
        self.RequiredItems                  = required_items or []
        self.OptionalItems                  = optional_items or []

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
class FundamentalAttributeInfo(AttributeInfo):
    # ----------------------------------------------------------------------
    def __init__(
        self,
        type_info_class,
        required_items=None,
        optional_items=None,
    ):
        super(FundamentalAttributeInfo, self).__init__(required_items, optional_items)
        self.TypeInfoClass                  = type_info_class

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
# |
# |  Public Data
# |
# ----------------------------------------------------------------------
UNIVERSAL_NAME_OVERRIDE_ATTRIBUTE_NAME                  = "name"
UNIVERSAL_DESCRIPTION_ATTRIBUTE_NAME                    = "description"

COLLECTION_KEY_ATTRIBUTE_NAME                           = "key"
COLLECTION_VALUE_ATTRIBUTE_NAME                         = "value"
COLLECTION_AS_DICTIONARY_ATTRIBUTE_NAME                 = "as_dictionary"

COLLECTION_REFINES_ARITY_ATTRIBUTE_NAME                 = "refines_arity"

OPTIONAL_DEFAULT_ATTRIBUTE_NAME                         = "default"

# TODO: Should introduce the concept of refinement, where a derived type can replace the value with
#       the same name if certain conditions hold true?
#
#           - enum can refine string
#           - enum can refine enum if derived values are a subset of base values
#           - base has arity of 1, derived is optional with default value and the default value is valid
#           - <Likely more here>
#
#       Open Question:
#           - Should these concepts be introduced in TypeInfo? If so, how complicated should TypeInfo
#             be allowed to become?

SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME                  = "fundamental_name"

CUSTOM_TYPE_ATTRIBUTE_NAME                              = "type"

# ----------------------------------------------------------------------
def _ValidateKey(plugin, element):
    return __ValidateKey(plugin, element)


def _ValidateValue(plugin, element):
    return __ValidateValue(plugin, element)


def _ValidateAsDictionary(plugin, element):
    return __ValidateAsDictionary(plugin, element)


def _ValidateRefinesArity(plugin, element):
    return __ValidateRefinesArity(plugin, element)


def _ValidateCompoundFundamentalName(plugin, element):
    return __ValidateCompoundFundamentalName(plugin, element)


def _ValidateFundamentalName(plugin, element):
    return __ValidateFundamentalName(plugin, element)


# ----------------------------------------------------------------------
UNIVERSAL_ATTRIBUTE_INFO                    = AttributeInfo(
    optional_items=[
        # Override the name of the object. This is useful when the element should have a name that would otherwise## Note that this attribute value is processed during Parsing and not made available within an Element.                                                #
        Attribute(
            UNIVERSAL_NAME_OVERRIDE_ATTRIBUTE_NAME,
            StringTypeInfo(),
            is_metadata=True,
        ),
        Attribute(
            UNIVERSAL_DESCRIPTION_ATTRIBUTE_NAME,
            StringTypeInfo(
                min_length=0,
            ),
            default_value="",
            is_metadata=True,
        ),
    ],
)

COLLECTION_ATTRIBUTE_INFO                   = AttributeInfo(
    optional_items=[
        # Name of child element whose value should be unique across all children
        Attribute(
            COLLECTION_KEY_ATTRIBUTE_NAME,
            StringTypeInfo(),
            validate_func=_ValidateKey,
            is_metadata=True,
        ),
        # Name of child element whose value should be considered the definition of a key/value dictionary
        Attribute(
            COLLECTION_VALUE_ATTRIBUTE_NAME,
            StringTypeInfo(),
            validate_func=_ValidateValue,
            is_metadata=True,
        ),
        # Flag to indicate if the content should be treated as a dictionary
        Attribute(
            COLLECTION_AS_DICTIONARY_ATTRIBUTE_NAME,
            BoolTypeInfo(),
            validate_func=_ValidateAsDictionary,
            is_metadata=True,
        ),
        # Normally, a reference that is also a collection will break reference traversal and create a new dimension
        # in a N-dimension array. However, sometimes we just want to refine the arity of a referenced collection.
        Attribute(
            COLLECTION_REFINES_ARITY_ATTRIBUTE_NAME,
            BoolTypeInfo(),
            validate_func=_ValidateRefinesArity,
            is_metadata=True,
        ),
    ],
)

OPTIONAL_ATTRIBUTE_INFO                     = AttributeInfo(
    optional_items=[
        Attribute(
            OPTIONAL_DEFAULT_ATTRIBUTE_NAME,
            StringTypeInfo(
                min_length=0,
            ),
            is_metadata=True,
        ),
    ],
)

# ----------------------------------------------------------------------
COMPOUND_ATTRIBUTE_INFO                     = AttributeInfo(
    optional_items=[
        Attribute(
            SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME,
            StringTypeInfo(),
            validate_func=_ValidateCompoundFundamentalName,
        ),
    ],
)

SIMPLE_ATTRIBUTE_INFO                       = AttributeInfo(
    optional_items=[
        # Create a named child with this name for plugins that don't support simple objects
        Attribute(
            SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME,
            StringTypeInfo(),
            missing_validate_func=_ValidateFundamentalName,
        ),
    ],
)

ANY_ATTRIBUTE_INFO                          = AttributeInfo()

CUSTOM_ATTRIBUTE_INFO                       = AttributeInfo(
    required_items=[Attribute(CUSTOM_TYPE_ATTRIBUTE_NAME, StringTypeInfo())],
)

VARIANT_ATTRIBUTE_INFO                      = AttributeInfo()
REFERENCE_ATTRIBUTE_INFO                    = AttributeInfo()
LIST_ATTRIBUTE_INFO                         = AttributeInfo()
EXTENSION_ATTRIBUTE_INFO                    = AttributeInfo()

# This type is implemented in terms of a visitor not because it provides any value, but
# rather because the use of the visitor ensures that we will be made aware if any new types
# are added.
FUNDAMENTAL_ATTRIBUTE_INFO_MAP              = OrderedDict()

# ----------------------------------------------------------------------
@staticderived
class _InitializeFundamentalTypesVisitor(FundamentalTypesVisitor):

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnBool(type_info):                  # <Parameters differ from overridden...> pylint: disable = W0221
        return "bool", FundamentalAttributeInfo(BoolTypeInfo)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDateTime(type_info):              # <Parameters differ from overridden...> pylint: disable = W0221
        return "datetime", FundamentalAttributeInfo(DateTimeTypeInfo)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDate(type_info):                  # <Parameters differ from overridden...> pylint: disable = W0221
        return "date", FundamentalAttributeInfo(DateTypeInfo)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDirectory(type_info):             # <Parameters differ from overridden...> pylint: disable = W0221
        return (
            "directory",
            FundamentalAttributeInfo(
                DirectoryTypeInfo,
                optional_items=[
                    Attribute(
                        "ensure_exists",
                        BoolTypeInfo(),
                        default_value=True,
                    ),
                    Attribute("validation_expression", StringTypeInfo()),
                ],
            ),
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDuration(type_info):              # <Parameters differ from overridden...> pylint: disable = W0221
        return "duration", FundamentalAttributeInfo(DurationTypeInfo)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnEnum(type_info):                  # <Parameters differ from overridden...> pylint: disable = W0221
        return (
            "enum",
            FundamentalAttributeInfo(
                EnumTypeInfo,
                required_items=[
                    Attribute(
                        "values",
                        StringTypeInfo(
                            arity="+",
                        ),
                    ),
                ],
                optional_items=[
                    Attribute(
                        "friendly_values",
                        StringTypeInfo(
                            arity="+",
                        ),
                    ),
                ],
            ),
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnFilename(type_info):              # <Parameters differ from overridden...> pylint: disable = W0221
        return (
            "filename",
            FundamentalAttributeInfo(
                FilenameTypeInfo,
                optional_items=[
                    Attribute(
                        "ensure_exists",
                        BoolTypeInfo(),
                        default_value=True,
                    ),
                    Attribute("validation_expression", StringTypeInfo()),
                    Attribute(
                        "match_any",
                        BoolTypeInfo(),
                        default_value=False,
                    ),
                ],
            ),
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnFloat(type_info):                 # <Parameters differ from overridden...> pylint: disable = W0221
        return "number", FundamentalAttributeInfo(
            FloatTypeInfo,
            optional_items=[Attribute("min", FloatTypeInfo()), Attribute("max", FloatTypeInfo())],
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnGuid(type_info):                  # <Parameters differ from overridden...> pylint: disable = W0221
        return "guid", FundamentalAttributeInfo(GuidTypeInfo)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnInt(type_info):                   # <Parameters differ from overridden...> pylint: disable = W0221
        return (
            "int",
            FundamentalAttributeInfo(
                IntTypeInfo,
                optional_items=[
                    Attribute("min", IntTypeInfo()),
                    Attribute("max", IntTypeInfo()),
                    Attribute(
                        "bytes",
                        EnumTypeInfo(
                            [
                                1,
                                2,
                                4,
                                8,
                            ],
                        ),
                    ),
                    Attribute(
                        "unsigned",
                        BoolTypeInfo(),
                        default_value=False,
                    ),
                ],
            ),
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnString(type_info):                # <Parameters differ from overridden...> pylint: disable = W0221
        return (
            "string",
            FundamentalAttributeInfo(
                StringTypeInfo,
                optional_items=[
                    Attribute(
                        "min_length",
                        IntTypeInfo(
                            min=0,
                        ),
                    ),
                    Attribute(
                        "max_length",
                        IntTypeInfo(
                            min=0,
                        ),
                    ),
                    Attribute("validation_expression", StringTypeInfo()),
                ],
            ),
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnTime(type_info):                  # <Parameters differ from overridden...> pylint: disable = W0221
        return "time", FundamentalAttributeInfo(TimeTypeInfo)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnUri(type_info):                   # <Parameters differ from overridden...> pylint: disable = W0221
        return "uri", FundamentalAttributeInfo(UriTypeInfo)


# ----------------------------------------------------------------------

_visitor                                    = _InitializeFundamentalTypesVisitor()

for _type_info in [
    # Initialize these values to any value; they are only used as a way to invoke the visitor
    BoolTypeInfo(),
    DateTimeTypeInfo(),
    DateTypeInfo(),
    DirectoryTypeInfo(),
    DurationTypeInfo(),
    EnumTypeInfo(["placeholder"]),
    FilenameTypeInfo(),
    FloatTypeInfo(),
    GuidTypeInfo(),
    IntTypeInfo(),
    StringTypeInfo(),
    TimeTypeInfo(),
    UriTypeInfo(),
]:
    key, value                              = _visitor.Accept(_type_info)
    FUNDAMENTAL_ATTRIBUTE_INFO_MAP[key]     = value

del _visitor
del _InitializeFundamentalTypesVisitor

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def __ValidateKey(plugin, element):   # <Unused argument> pylint: disable = W0613
    key = element.key

    # Special case when the unique key is the fundamental part of a
    # SimpleElement.
    if isinstance(element, (Elements.SimpleElement, Elements.CompoundElement)) and getattr(element, SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME, None) == key:
        return None

    # Look for the key in all the children.
    unique_child = None

    for child in element.Resolve().Children:
        if child.Name == key:
            unique_child = child
            break

    if unique_child is None:
        return "The unique child '{}' does not exist".format(key)

    if not isinstance(unique_child, Elements.FundamentalElement):
        return "The unique child '{}' is not a fundamental element".format(key)

    if not unique_child.TypeInfo.Arity.IsSingle:
        return "The unique child '{}' does not have an arity of 1".format(key)

    if unique_child.IsDefinitionOnly:
        return "The unique child '{}' must not be a definition"

    return None


# ----------------------------------------------------------------------
def __ValidateValue(plugin, element):
    value_name = element.value

    value_element = None

    for child in element.Children:
        if child.Name == value_name:
            value_element = child
            break

    if value_element is None:
        return "The child '{}' does not exist".format(value_name)

    if value_element.IsDefinitionOnly:
        return "The child '{}' must not be a definition".format(value_name)

    if getattr(value_element, "IsAttribute", False):
        return "The child '{}' must not be an attribute".format(value_name)

    return None


# ----------------------------------------------------------------------
def __ValidateAsDictionary(plugin, element):
    if not element.as_dictionary:
        return "'{}' should always be true when provided".format(COLLECTION_AS_DICTIONARY_ATTRIBUTE_NAME)

    # Ensure that the plugin supports dictionaries
    if not plugin.Flags & ParseFlag.SupportDictionaryElements:
        return "Dictionary elements are not supported"

    if getattr(element, COLLECTION_KEY_ATTRIBUTE_NAME, None) is None:
        return "The '{}' attribute must be provided when defining dictionaries".format(COLLECTION_KEY_ATTRIBUTE_NAME)

    if getattr(element, COLLECTION_VALUE_ATTRIBUTE_NAME, None) is None:
        return "The '{}' attribute must be provided when defining dictionaries".format(COLLECTION_VALUE_ATTRIBUTE_NAME)

    # Ensure that we only have 2 children
    child_count = 0

    for child in element.Children:
        if child.IsDefinitionOnly:
            continue

        child_count += 1

    if child_count != 2:
        return "Only 2 child elements were expected (one for the key and one for the value); {} elements were found".format(child_count)

    return None


# ----------------------------------------------------------------------
def __ValidateRefinesArity(plugin, element):            # <Unused argument> pylint: disable = W0613
    if not isinstance(element, Elements.ReferenceElement):
        return "'{}' may only be used with reference elements".format(COLLECTION_REFINES_ARITY_ATTRIBUTE_NAME)

    return None


# ----------------------------------------------------------------------
def __ValidateCompoundFundamentalName(plugin, element):
    if plugin.Flags & ParseFlag.SupportSimpleObjectElements:
        return "The attribute '{}' should not be provided with plugins that support simple objects".format(SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME)

    if not hasattr(element, "FundamentalAttributeName"):
        return "The attribute '{}' should only be used with simple objects".format(SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME)

    return None


# ----------------------------------------------------------------------
def __ValidateFundamentalName(plugin, element):         # <Unused argument> pylint: disable = W0613
    if not plugin.Flags & ParseFlag.SupportSimpleObjectElements:
        return "The attribute '{}' must be provided for plugins that do not support simple objects".format(SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME)

    return None
