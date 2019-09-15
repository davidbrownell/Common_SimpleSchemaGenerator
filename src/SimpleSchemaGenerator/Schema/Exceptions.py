# ----------------------------------------------------------------------
# |
# |  Exceptions.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 15:15:53
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Exceptions thrown by SimpleSchema"""

import os
import sys

import six

import CommonEnvironment
from CommonEnvironment.Interface import abstractproperty, Interface

from CommonEnvironment.CompilerImpl import CompilerImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class SimpleSchemaException(CompilerImpl.DiagnosticException, Interface):
    """Base class for all exceptions raised by SimpleSchemaGenerator"""

    # ----------------------------------------------------------------------
    @abstractproperty
    def Display(self):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    def __init__(self, source, line, column, *args, **kwargs):
        if isinstance(source, (list, tuple)) and hasattr(source[-1], "filename"):
            self.Source                     = source[-1].filename
        else:
            self.Source                     = source

        self.Line                           = line
        self.Column                         = column

        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)

        msg = "{text} ({source} [{line} <{column}>])".format(
            text=(args[0] if args else self.Display).format(**self.__dict__),
            source=self.Source,
            line=self.Line,
            column=self.Column,
        )
        super(SimpleSchemaException, self).__init__(msg)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class PopulateUnsupportedIncludeStatementsException(SimpleSchemaException):
    Display                                 = "Include statements are not supported"


class PopulateUnsupportedConfigStatementsException(SimpleSchemaException):
    Display                                 = "Config statements are not supported"


class PopulateUnsupportedExtensionStatementException(SimpleSchemaException):
    Display                                 = "Extension statements are not supported"


class PopulateUnsupportedUnnamedObjectsException(SimpleSchemaException):
    Display                                 = "Unnamed objects are not supported"


class PopulateUnsupportedNamedObjectsException(SimpleSchemaException):
    Display                                 = "Named objects are not supported"


class PopulateUnsupportedRootObjectsException(SimpleSchemaException):
    Display                                 = "Root objects are not supported"


class PopulateUnsupportedChildObjectsException(SimpleSchemaException):
    Display                                 = "Child objects are not supported"


class PopulateUnsupportedUnnamedDeclarationsException(SimpleSchemaException):
    Display                                 = "Unnamed declarations are not supported"


class PopulateUnsupportedRootDeclarationsException(SimpleSchemaException):
    Display                                 = "Root declarations are not supported"


class PopulateUnsupportedChildDeclarationsException(SimpleSchemaException):
    Display                                 = "Child declarations are not supported"


class PopulateUnsupportedNamedDeclarationsException(SimpleSchemaException):
    Display                                 = "Named declarations are not supported"


class PopulateInvalidTripleStringHeaderException(SimpleSchemaException):
    Display                                 = "The content in a triple quote string must begin on a line horizontally aligned with the opening set of quotes"


class PopulateInvalidTripleStringFooterException(SimpleSchemaException):
    Display                                 = "The content in a triple quote string must end on a line horizontally aligned with the opening set of quotes"


class PopulateInvalidTripleStringPrefixException(SimpleSchemaException):
    Display                                 = "The content in a triple quote string must be horizontally aligned with the opening set of quotes"


class PopulateInvalidIncludeFilenameException(SimpleSchemaException):
    Display                                 = "The included filename '{name}' is not a valid filename"


class PopulateInvalidArityException(SimpleSchemaException):
    Display                                 = "The arity value '{value}' must be greater than or equal to 1"


class PopulateInvalidMaxArityException(SimpleSchemaException):
    Display                                 = "The maximum arity value '{max}' must be greater than the minimum value '{min}'"


class PopulateDuplicateMetadataException(SimpleSchemaException):
    Display                                 = "The metadata value '{name}' has already been provided ({original_source} [{original_line} <{original_column}>])"


class PopulateDuplicateKeywordArgumentException(SimpleSchemaException):
    Display                                 = "The keyword argument '{name}' with the value '{value}' has already been defined as '{original_value}'"


class PopulateReservedNameException(SimpleSchemaException):
    Display                                 = "The name '{name}' is reserved and cannot be used as an element name; consider using the attribute 'name' to explicitly override this value"


class ResolveInvalidReferenceException(SimpleSchemaException):
    Display                                 = "The reference '{name}' could not be resolved"


class ResolveInvalidCustomNameException(SimpleSchemaException):
    Display                                 = "The value '{name}' is not a valid name"


class ValidateUnsupportedCustomElementsException(SimpleSchemaException):
    Display                                 = "Custom elements are not supported"


class ValidateUnsupportedAnyElementsException(SimpleSchemaException):
    Display                                 = "Any elements are not supported"


class ValidateUnsupportedReferenceElementsException(SimpleSchemaException):
    Display                                 = "Reference elements are not supported"


class ValidateUnsupportedListElementsException(SimpleSchemaException):
    Display                                 = "List elements are not supported"


class ValidateUnsupportedSimpleObjectElementsException(SimpleSchemaException):
    Display                                 = "Pure simple object elements are not supported by this plugin; consider adding the attribute 'fundamental_name' to automatically convert this element into a compound element"


class ValidateUnsupportedVariantElementsException(SimpleSchemaException):
    Display                                 = "Variant elements are not supported"


class ValidateDuplicateNameException(SimpleSchemaException):
    Display                                 = "The element name '{name}' has already been defined ({original_source} [{original_line} <{original_column}>])"


class ValidateInvalidExtensionException(SimpleSchemaException):
    Display                                 = "The extension '{name}' is not a supported extension"


class ValidateInvalidVariantArityException(SimpleSchemaException):
    Display                                 = (
        "Variant elements may only reference other elements with an arity of 1 (Index: {index})"
    )


class ValidateInvalidReferenceException(SimpleSchemaException):
    Display                                 = "An extension may not be the target of a reference"


# TODO: Only 1 fundamental derived for simple elements


class ValidateInvalidSimpleChildException(SimpleSchemaException):
    Display                                 = "The children of simple elements must be fundamental attributes or references to fundamental elements/attributes with an arity of 1"


class ValidateMissingAttributeException(SimpleSchemaException):
    Display                                 = "The required attribute '{name}' was not provided"


class ValidateExtraneousAttributeException(SimpleSchemaException):
    Display                                 = "The attribute '{name}' is not valid for this element"


class ValidateInvalidAttributeException(SimpleSchemaException):
    Display                                 = "The attribute value for '{name}' is not valid: {reason}"


class InvalidAttributeNameException(SimpleSchemaException):
    Display                                 = "The metadata name '{name}' is reserved and cannot be used"


class InvalidAttributeException(SimpleSchemaException):
    Display                                 = "{desc}"
