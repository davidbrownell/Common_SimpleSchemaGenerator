# ----------------------------------------------------------------------
# |  
# |  Exceptions.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 15:15:53
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Exceptions thrown by SimpleSchema"""

import os
import sys

import six

import CommonEnvironment
from CommonEnvironment.CompilerImpl import CompilerImpl

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class SimpleSchemaException(CompilerImpl.DiagnosticException):
    """Base class for all exceptions raised by SimpleSchemaGenerator"""

    # ----------------------------------------------------------------------
    def __init__( self,
                  source,
                  line,
                  column,
                  *args,
                  **kwargs
                ):
        if isinstance(source, (list, tuple)) and hasattr(source[-1], "filename"):
            self.Source                     = source[-1].filename
        else:
            self.Source                     = source

        self.Line                           = line
        self.Column                         = column

        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)

        msg = "{text} ({source} [{line} <{column}>])".format( text=(args[0] if args else self.Display).format(**self.__dict__),
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
class PopulateInvalidTripleStringHeaderException(SimpleSchemaException):            Display = "The content in a triple quote string must begin on a line horizontally aligned with the opening set of quotes"
class PopulateInvalidTripleStringFooterException(SimpleSchemaException):            Display = "The content in a triple quote string must end on a line horizontally aligned with the opening set of quotes"
class PopulateInvalidTripleStringPrefixException(SimpleSchemaException):            Display = "The content in a triple quote string must be horizontally aligned with the opening set of quotes"
class PopulateUnsupportedIncludeStatementsException(SimpleSchemaException):         Display = "Include statements are not supported"
class PopulateInvalidIncludeFilenameException(SimpleSchemaException):               Display = "The included filename '{name}' is not a valid filename"
class PopulateUnsupportedConfigStatementsException(SimpleSchemaException):          Display = "Config statements are not supported"
class PopulateDuplicateConfigException(SimpleSchemaException):                      Display = "Configuration information for '{name}' has already been specified in {original_source} <{original_line} [{original_column}]>"
class PopulateUnsupportedUnnamedObjectsException(SimpleSchemaException):            Display = "Unnamed objects are not supported"
class PopulateUnsupportedNamedObjectsException(SimpleSchemaException):              Display = "Named objects are not supported"
class PopulateUnsupportedRootObjectsException(SimpleSchemaException):               Display = "Root objects are not supported"
class PopulateUnsupportedChildObjectsException(SimpleSchemaException):              Display = "Child objects are not supported"
class PopulateInvalidArityException(SimpleSchemaException):                         Display = "The arity value '{value}' must be greater than or equal to 1"
class PopulateInvalidMaxArityException(SimpleSchemaException):                      Display = "The maximum arity value '{max}' must be greater than the minimum value '{min}'"
class PopulateUnsupportedUnnamedDeclarationsException(SimpleSchemaException):       Display = "Unnamed declarations are not supported"
class PopulateUnsupportedRootDeclarationsException(SimpleSchemaException):          Display = "Root declarations are not supported"
class PopulateUnsupportedChildDeclarationsException(SimpleSchemaException):         Display = "Child declarations are not supported"
class PopulateUnsupportedNamedDeclarationsException(SimpleSchemaException):         Display = "Named declarations are not supported"
