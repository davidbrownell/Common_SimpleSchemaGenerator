# ----------------------------------------------------------------------
# |
# |  ItemMethodElementVisitor.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-24 20:09:30
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the ItemMethodElementVisitor object"""

import os
import textwrap

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment import StringHelpers

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

with InitRelativeImports():
    from ....Schema import Elements

    from ..ElementVisitors import ElementVisitor, ToPythonName

# ----------------------------------------------------------------------
class ItemMethodElementVisitor(ElementVisitor):
    # ----------------------------------------------------------------------
    def __init__(
        self,
        type_info_serialization_name,
        custom_serialize_item_args,
        source_writer,
        dest_writer,
        output_stream,
        enumerate_children_func,
        is_serializer,
    ):
        self._type_info_serialization_name  = type_info_serialization_name
        self._custom_serialize_item_args    = custom_serialize_item_args
        self._source_writer                 = source_writer
        self._dest_writer                   = dest_writer
        self._output_stream                 = output_stream
        self._enumerate_children_func       = enumerate_children_func
        self._is_serializer                 = is_serializer
        self._method_prefix                 = "Serialize" if is_serializer else "Deserialize"
        
    # BugBug: Handle optional

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnCompound_VisitingChildren(element):
        return False

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnSimple_VisitingChildren(element):
        return False

    # ----------------------------------------------------------------------
    @Interface.override
    def OnFundamental(self, element):
        python_name = ToPythonName(element)

        statement = "{type_info}.{method_prefix}Item(_{python_name}_TypeInfo, item, **{serialize_args})".format(
            type_info=self._type_info_serialization_name,
            method_prefix=self._method_prefix,
            python_name=python_name,
            serialize_args=self._custom_serialize_item_args,
        )

        if not element.IsAttribute:
            statement = self._dest_writer.CreateFundamentalElement(element, statement)

        self._output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @classmethod
                def _{python_name}_Item(cls, item):
                    return {statement}

                """,
            ).format(
                python_name=python_name,
                statement=StringHelpers.LeftJustify(statement, 4).strip(),
            )
        )

    # ----------------------------------------------------------------------
    @Interface.override
    def OnCompound(self, element):
        self._GenerateClass(element)

    # ----------------------------------------------------------------------
    @Interface.override
    def OnSimple(self, element):
        self._GenerateClass(element)

    # ----------------------------------------------------------------------
    @Interface.override
    def OnVariant(self, element):
        self._output_stream.write("BugBug: OnVariant - {}".format(ToPythonName(element)))

    # ----------------------------------------------------------------------
    @Interface.override
    def OnReference(self, element):
        # Nothing to do here
        pass
        
    # ----------------------------------------------------------------------
    @Interface.override
    def OnList(self, element):
        self._output_stream.write("BugBug: OnList - {}".format(ToPythonName(element)))

    # ----------------------------------------------------------------------
    @Interface.override
    def OnAny(self, element):
        self._output_stream.write("BugBug: OnAny - {}".format(ToPythonName(element)))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _GenerateClass(self, element):
        attributes = []
        statements = []

        attribute_names = []

        for child in self._enumerate_children_func(element):
            attribute_names.append(child.Name)

            is_compound_like = isinstance(child.Resolve(), (Elements.CompoundElement, Elements.SimpleElement))

            # Note that we have to use getattr here, as Compound- and SimpleElements don't support IsAttribute
            if getattr(child, "IsAttribute", False):
                is_attribute = True
                
                assert isinstance(child.Resolve(), Elements.FundamentalElement)
                assert not child.TypeInfo.Arity.IsCollection

                if child.TypeInfo.Arity.IsOptional:
                    statement_template = 'cls._ApplyOptionalAttribute(item, "{name}", attributes, cls.{python_name}, always_include_optional)'
                else:
                    statement_template = textwrap.dedent(
                        """\
                        attributes["{name}"] = cls.{python_name}(
                            {get_child_statement},
                        )
                        """)

                statement = statement_template.format(
                    name=child.Name,
                    python_name=ToPythonName(child),
                    get_child_statement=StringHelpers.LeftJustify(self._source_writer.GetChild("item", child), 4).strip(),
                )

            else:
                is_attribute = False

                if child.TypeInfo.Arity.Min == 0:
                    if is_compound_like:
                        statement = "lambda value: cls.{}(value, always_include_optional, process_additional_data)".format(ToPythonName(child))
                    else:
                        statement = "cls.{}".format(ToPythonName(child))

                    if child.TypeInfo.Arity.Max == 1:
                        function_name = "_ApplyOptionalChild"
                    else:
                        function_name = "_ApplyOptionalChildren"

                    statement = 'cls.{function_name}(item, "{name}", result, {statement}, always_include_optional)'.format(
                        function_name=function_name,
                        name=child.Name,
                        statement=statement,
                    )

                else:
                    if is_compound_like:
                        extra_params = StringHelpers.LeftJustify(
                            textwrap.dedent(
                                """\
                                    
                                always_include_optional,
                                process_additional_data
                                """,
                            ),
                            4,
                        )

                    else:
                        extra_params = ""

                    statement = self._dest_writer.AppendChild(
                        child,
                        "result",
                        textwrap.dedent(
                            """\
                            cls.{python_name}(
                                {get_child},{extra_params}
                            )
                            """,
                        ).format(
                            python_name=ToPythonName(child),
                            get_child=StringHelpers.LeftJustify(self._source_writer.GetChild("item", child), 4).strip(),
                            name=child.Name,
                            extra_params=extra_params,
                        ),
                    )

            (attributes if is_attribute else statements).append(
                textwrap.dedent(
                    """\
                    # {name}
                    try:
                        {statement}
                    except:
                        _DecorateActiveException("{name}")

                    """,
                ).format(
                    name=child.Name,
                    statement=StringHelpers.LeftJustify(statement, 4).strip(),
                ),
            )

        if isinstance(element, Elements.SimpleElement):
            attribute_names.append(element.FundamentalAttributeName)

            assert not statements
            statement = textwrap.dedent(
                """\
                # <fundamental value>
                try:
                    fundamental_value = {}
                except:
                    _DecorateActiveException("value type")

                result = {}

                """).format(
                    StringHelpers.LeftJustify(
                        '{type_info}.{method_prefix}Item(_{python_name}__value__TypeInfo, {value}, **{serialize_args})'.format(
                            type_info=self._type_info_serialization_name,
                            method_prefix=self._method_prefix,
                            python_name=ToPythonName(element),
                            value=self._source_writer.GetChild(
                                "item",
                                self._source_writer.CreateTemporaryElement(
                                    '"{}"'.format(element.FundamentalAttributeName),
                                    is_collection=False,
                                ),
                                is_simple_schema_fundamental=True,
                            ),
                            serialize_args=self._custom_serialize_item_args,
                        ),
                        4,
                    ),
                    self._dest_writer.CreateSimpleElement(
                        element,
                        "attributes" if attributes else None,
                        "fundamental_value",
                    ),
                )
                
        else:
            statement = textwrap.dedent(
                """\
                result = {}
                
                {}
                """,
            ).format(
                self._dest_writer.CreateCompoundElement(element, "attributes" if attributes else None).strip(),
                ''.join(statements).strip(),
            )

        python_name = ToPythonName(element)

        validation_statement_template = textwrap.dedent(
            """\
            _{}_TypeInfo.ValidateItem(
                {{}},
                recurse=False,
                require_exact_match=not process_additional_data,
            )
            """,
        ).format(python_name)

        if self._is_serializer:
            prefix = validation_statement_template.format("item")
            suffix = ""
        else:
            prefix = ""
            suffix = validation_statement_template.format("result")

        self._output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @classmethod
                def _{python_name}_Item(cls, item, always_include_optional, process_additional_data):
                    {prefix}{attributes_decl}{attributes}{statement}{suffix}

                    # Additional data
                    if process_additional_data:
                        cls._ApplyAdditionalData(
                            item,
                            result,
                            exclude_names={{{attribute_names}}},
                        )

                    return result

                """,
            ).format(
                python_name=python_name,
                prefix=StringHelpers.LeftJustify("{}\n\n".format(prefix.strip()) if prefix else prefix, 4),
                suffix=StringHelpers.LeftJustify("\n\n{}".format(suffix.strip()) if suffix else suffix, 4),
                attributes_decl='' if not attributes else "attributes = OrderedDict()\n\n    ",
                attributes='' if not attributes else "{}\n\n    ".format(StringHelpers.LeftJustify(''.join(attributes), 4).strip()),
                statement=StringHelpers.LeftJustify(statement, 4).strip(),
                attribute_names=", ".join(['"{}"'.format(attribute_name) for attribute_name in attribute_names]),
            ),
        )
