# ----------------------------------------------------------------------
# |
# |  PythonStatementWriterMixin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-03-07 18:48:02
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the PythonStatementWriterMixin object"""

import os
import textwrap

import CommonEnvironment
from CommonEnvironment import Interface

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class PythonStatementWriterMixin(object):
    # ----------------------------------------------------------------------
    @staticmethod
    def GetGlobalUtilityMethods(attributes_attribute_name):
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
            additional_data=attributes_attribute_name,
        )
