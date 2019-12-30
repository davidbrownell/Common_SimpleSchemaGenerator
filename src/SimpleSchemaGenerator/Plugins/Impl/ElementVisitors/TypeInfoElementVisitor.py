# ----------------------------------------------------------------------
# |
# |  TypeInfoElementVisitor.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-24 20:00:10
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the TypeInfoElementVisitor object"""

import os

import six

import CommonEnvironment
from CommonEnvironment import Interface

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ....Schema import Elements

    from ..ElementVisitors import ElementVisitor, ToPythonName

# ----------------------------------------------------------------------
class TypeInfoElementVisitor(ElementVisitor):

    # ----------------------------------------------------------------------
    def __init__(self, python_code_visitor, cached_children_statements):
        self._python_code_visitor           = python_code_visitor
        self._cached_children_statements    = cached_children_statements

    # ----------------------------------------------------------------------
    @Interface.override
    def OnFundamental(self, element):
        return self._python_code_visitor.Accept(element.TypeInfo)

    # ----------------------------------------------------------------------
    @Interface.override
    def OnCompound(self, element):
        return self._GenerateClass(element)

    # ----------------------------------------------------------------------
    @Interface.override
    def OnSimple(self, element):
        return self._GenerateClass(element)

    # ----------------------------------------------------------------------
    @Interface.override
    def OnVariant(self, element):
        return self._python_code_visitor.Accept(element.TypeInfo)

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnReference(element):
        # References don't have type info objects
        return None

    # ----------------------------------------------------------------------
    @Interface.override
    def OnList(self, element):
        return "ListTypeInfo(_{}_TypeInfo{})".format(ToPythonName(element.Reference), self._ToArityString(element.TypeInfo.Arity))

    # ----------------------------------------------------------------------
    @Interface.override
    def OnAny(self, element):
        return self._python_code_visitor.Accept(element.TypeInfo)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _ToArityString(
        arity,
        comma_prefix=True,
    ):
        arity = arity.ToString()
        if not arity:
            return ""

        return "{}arity=Arity.FromString('{}')".format(", " if comma_prefix else "", arity)

    # ----------------------------------------------------------------------
    def _GenerateClass(self, element):
        # Rather than using the existing type info, convert this into a structure
        # that can process classes or dictionaries. Also, handle the processing of
        # recursive data structure by creating a TypeInfo object that only parses one
        # level deep.

        # ----------------------------------------------------------------------
        def GenerateChildren(element):
            queue = [element]

            while queue:
                element = queue.pop(0)
                if not isinstance(element, (Elements.CompoundElement, Elements.SimpleElement)):
                    continue

                for k, v in six.iteritems(element.TypeInfo.Items):
                    if k is None:
                        continue

                    yield k, v

                queue += getattr(element, "Bases", [])

        # ----------------------------------------------------------------------

        children_statement = "OrderedDict([{}])".format(
            ", ".join(
                [
                    '("{}", GenericTypeInfo({}))'.format(
                        k,
                        self._ToArityString(
                            v.Arity,
                            comma_prefix=False,
                        ),
                    ) for k,
                    v in GenerateChildren(element)
                ],
            ),
        )

        if children_statement not in self._cached_children_statements:
            self._cached_children_statements[children_statement] = "_{}_TypeInfo_Contents".format(ToPythonName(element))

        return "AnyOfTypeInfo([ClassTypeInfo({children}, require_exact_match=False), DictTypeInfo({children}, require_exact_match=False)]{arity})".format(
            children=self._cached_children_statements[children_statement],
            arity=self._ToArityString(element.TypeInfo.Arity),
        )
