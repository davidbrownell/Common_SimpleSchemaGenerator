# ----------------------------------------------------------------------
# |
# |  PythonDestinationStatementWriter.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-25 16:17:44
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the PythonDestinationStatementWriter object"""

import os
import textwrap

import CommonEnvironment
from CommonEnvironment import Interface

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..StatementWriters import DestinationStatementWriter

# ----------------------------------------------------------------------
@Interface.staticderived
class PythonDestinationStatementWriter(DestinationStatementWriter):

    # ----------------------------------------------------------------------
    ObjectTypeDesc                          = Interface.DerivedProperty("a python object")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def CreateCompoundElement(element, attributes_var_or_none):
        return textwrap.dedent(
            """\
            _CreatePythonObject(
                attributes={attributes},
            )
            """,
        ).format(
            attributes=attributes_var_or_none or "None",
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def CreateSimpleElement(cls, element, attributes_var_or_none, fundamental_statement):
        return textwrap.dedent(
            """\
            _CreatePythonObject(
                attributes={attributes},
                **{{"{value_name}": {fundamental}, "{simple_element_fundamental}": "{value_name}"}},
            )
            """,
        ).format(
            attributes=attributes_var_or_none or "None",
            value_name=getattr(element, "FundamentalAttributeName", "simple_value"),
            fundamental=fundamental_statement,
            simple_element_fundamental=cls.SIMPLE_ELEMENT_FUNDAMENTAL_ATTRIBUTE_NAME,
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def CreateFundamentalElement(element, fundamental_statement):
        return fundamental_statement

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def CreateCollection(element, result_name):
        return result_name

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def AppendChild(cls, child_element, parent_var_name, var_name_or_none):
        if var_name_or_none is None:
            var_name_or_none = "[]" if child_element.TypeInfo.Arity.IsCollection else "None"

        if getattr(child_element, "IsAttribute", False):
            return "{}[{}] = {}".format(parent_var_name, cls.GetElementStatementName(child_element), var_name_or_none)

        return "setattr({}, {}, {})".format(parent_var_name, cls.GetElementStatementName(child_element), var_name_or_none)

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def SerializeToString(var_name):
        raise Exception("This should not be called for python objects")

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetGlobalUtilityMethods(cls, source_writer):
        return textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            class Object(object):
                def __init__(self):
                    self.{additional_data} = set()

                def __repr__(self):
                    return CommonEnvironment.ObjectReprImpl(self)


            # ----------------------------------------------------------------------
            def _CreatePythonObject(
                attributes=None,
                **kwargs
            ):
                attributes = attributes or {{}}

                result = Object()

                for d in [attributes, kwargs]:
                    for k, v in six.iteritems(d):
                        setattr(result, k, v)

                for k in six.iterkeys(attributes):
                    result.{additional_data}.add(k)

                return result

            """,
        ).format(
            additional_data=cls.ATTRIBUTES_ATTRIBUTE_NAME,
        )
