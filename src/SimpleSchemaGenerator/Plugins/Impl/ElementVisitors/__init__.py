# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-24 19:58:14
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the ElementVisitor object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ....Schema import Elements

# ----------------------------------------------------------------------
class ElementVisitor(Elements.ElementVisitor):
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnCustom(element, python_code_visitor, cached_children_statements):
        raise Exception("CustomElements are not supported")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnExtension(element, python_code_visitor, cached_children_statements):
        raise Exception("ExtensionElements are not supported")


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def ToPythonName(element):
    name = element.DottedName

    for char in [".", "-", " "]:
        name = name.replace(char, "_")

    return name
