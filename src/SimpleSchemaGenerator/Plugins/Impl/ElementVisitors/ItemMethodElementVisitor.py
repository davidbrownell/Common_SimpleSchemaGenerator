# ----------------------------------------------------------------------
# |
# |  ItemMethodElementVisitor.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-24 20:09:30
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-21
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
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ....Schema import Elements

    from ..ElementVisitors import ElementVisitor, ToPythonName

# ----------------------------------------------------------------------
class ItemMethodElementVisitor(ElementVisitor):
    # ----------------------------------------------------------------------
    def __init__(self, type_info_serialization_name, custom_serialize_item_args, source_writer, dest_writer, output_stream, enumerate_children_func, is_serializer):
        self._type_info_serialization_name  = type_info_serialization_name
        self._custom_serialize_item_args    = custom_serialize_item_args
        self._source_writer                 = source_writer
        self._dest_writer                   = dest_writer
        self._output_stream                 = output_stream
        self._enumerate_children_func       = enumerate_children_func
        self._is_serializer                 = is_serializer
        self._method_prefix                 = "Serialize" if is_serializer else "Deserialize"

        self.IncludeApplyOptionalChild      = False
        self.IncludeApplyOptionalChildren   = False
        self.IncludeApplyOptionalAttribute  = False

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

        statement = "{type_info}.{method_prefix}Item({python_name}_TypeInfo, {item_statement}, **{serialize_args})".format(
            type_info=self._type_info_serialization_name,
            method_prefix=self._method_prefix,
            python_name=python_name,
            item_statement=self._source_writer.GetFundamental("item", element),
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
            ),
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
        statements = []
        new_types = []

        for variation in element.Variations:
            if isinstance(variation, Elements.ReferenceElement):
                statement = "cls._{}_Item".format(ToPythonName(variation.Reference))

                resolved_element = variation.Reference.Resolve()

                if isinstance(resolved_element, (Elements.CompoundElement, Elements.SimpleElement)):
                    statement = '((lambda item: {}(item, process_additional_data=False, always_include_optional=False)), "{}")'.format(statement, resolved_element.DottedName)

                statements.append(statement)
            else:
                assert not isinstance(variation, (Elements.CompoundElement, Elements.SimpleElement)), variation

                new_types.append(variation)
                statements.append("cls._{}_Item".format(ToPythonName(variation)))

        python_name = ToPythonName(element)

        self._output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @classmethod
                def _{python_name}_Item(cls, item):
                    for method_info in [
                        {statements}
                    ]:
                        if isinstance(method_info, tuple):
                            potential_method, class_name = method_info
                        else:
                            potential_method = method_info
                            class_name = None

                        try:
                            result = potential_method(item)

                            if class_name is not None:
                                {apply_class_name_statement}

                            return result
                        except:
                            pass

                    raise {exception_type}Exception("The value cannot be converted to any of the supported variations")

                """,
            ).format(
                python_name=python_name,
                statements=StringHelpers.LeftJustify("\n".join(["{},".format(statement) for statement in statements]), 8).rstrip(),
                apply_class_name_statement=StringHelpers.LeftJustify(
                    self._dest_writer.AppendChild(
                        self._dest_writer.CreateTemporaryElement('"{}"'.format(self._dest_writer.VARIANT_CLASS_TYPE_ATTRIBUTE_NAME), "1"),
                        "result",
                        "class_name",
                    ),
                    16,
                ).rstrip(),
                exception_type="Serialize" if self._is_serializer else "Deserialize",
            ),
        )

        self.Accept(new_types)

    # ----------------------------------------------------------------------
    @Interface.override
    def OnReference(self, element):
        # Nothing to do here
        pass

    # ----------------------------------------------------------------------
    @Interface.override
    def OnList(self, element):
        self._output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @classmethod
                def _{python_name}_Item(cls, items):
                    try:
                        return cls.{reference_python_name}(items)
                    except:
                        _DecorateActiveException("{reference_name}")

                """,
            ).format(
                python_name=ToPythonName(element),
                reference_python_name=ToPythonName(element.Reference),
                reference_name=element.Reference.Name,
            ),
        )

    # ----------------------------------------------------------------------
    @Interface.override
    def OnAny(self, element):
        self._output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @classmethod
                def _{python_name}_Item(cls, item):
                    return cls._CreateAdditionalDataItem("{name}", item)

                """,
            ).format(
                python_name=ToPythonName(element),
                name=element.Name,
            ),
        )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _GenerateClass(self, element):
        if getattr(element, "as_dictionary", False):
            return self._GenerateDictionary(element)

        attributes = []
        statements = []

        attribute_names = []

        for child in self._enumerate_children_func(
            element,
            include_definitions=False,
        ):
            child_python_name = ToPythonName(child)
            resolved_child_python_name = ToPythonName(child.Resolve())

            attribute_names.append(child.Name)

            is_compound_like = isinstance(child.Resolve(), (Elements.CompoundElement, Elements.SimpleElement))

            # Note that we have to use getattr here, as Compound- and SimpleElements don't support IsAttribute
            if getattr(child, "IsAttribute", False):
                is_attribute = True

                assert not child.TypeInfo.Arity.IsCollection

                if child.TypeInfo.Arity.IsOptional:
                    if hasattr(child, "default"):
                        default_value = ', default_value_func=lambda: StringSerialization.DeserializeItem({}_TypeInfo, "{}")'.format(resolved_child_python_name, child.default)
                    else:
                        default_value = ""

                    self.IncludeApplyOptionalAttribute = True
                    statement_template = 'cls._ApplyOptionalAttribute(item, "{{name}}", attributes, cls.{{python_name}}, always_include_optional{})'.format(default_value)
                else:
                    statement_template = textwrap.dedent(
                        """\
                        attributes["{name}"] = cls.{python_name}(
                            {get_child_statement},
                        )
                        """,
                    )

                statement = statement_template.format(
                    name=child.Name,
                    python_name=child_python_name,
                    get_child_statement=StringHelpers.LeftJustify(self._source_writer.GetChild("item", child), 4).strip(),
                )

            else:
                is_attribute = False

                if child.TypeInfo.Arity.Min == 0:
                    if is_compound_like:
                        statement = "lambda value: cls.{}(value, always_include_optional, process_additional_data)".format(child_python_name)
                    else:
                        statement = "cls.{}".format(child_python_name)

                    if child.TypeInfo.Arity.Max == 1:
                        self.IncludeApplyOptionalChild = True
                        function_name = "_ApplyOptionalChild"

                        if hasattr(child, "default"):
                            default_value = ', default_value_func=lambda: StringSerialization.DeserializeItem({}_TypeInfo, "{}")'.format(resolved_child_python_name, child.default)
                        else:
                            default_value = ""
                    else:
                        self.IncludeApplyOptionalChildren = True
                        function_name = "_ApplyOptionalChildren"
                        default_value = ""

                    statement = 'cls.{function_name}(item, "{name}", result, {statement}, always_include_optional{default_value})'.format(
                        function_name=function_name,
                        name=child.Name,
                        statement=statement,
                        default_value=default_value,
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

            statement = textwrap.dedent(
                """\
                # <fundamental value>
                try:
                    fundamental_value = {}
                except:
                    _DecorateActiveException("value type")

                result = {}

                {}
                """,
            ).format(
                StringHelpers.LeftJustify(
                    "{type_info}.{method_prefix}Item({python_name}__value__TypeInfo, {value}, **{serialize_args})".format(
                        type_info=self._type_info_serialization_name,
                        method_prefix=self._method_prefix,
                        python_name=ToPythonName(element),
                        value=self._source_writer.GetChild(
                            "item",
                            self._source_writer.CreateTemporaryElement('"{}"'.format(element.FundamentalAttributeName), "1"),
                            is_simple_schema_fundamental=True,
                        ),
                        serialize_args=self._custom_serialize_item_args,
                    ),
                    4,
                ),
                self._dest_writer.CreateSimpleElement(element, "attributes" if attributes else None, "fundamental_value"),
                "".join(statements).strip(),
            )

        else:
            statement = textwrap.dedent(
                """\
                result = {}

                {}
                """,
            ).format(self._dest_writer.CreateCompoundElement(element, "attributes" if attributes else None).strip(), "".join(statements).strip())

        python_name = ToPythonName(element)

        validation_statement_template = textwrap.dedent(
            """\
            {}_TypeInfo.ValidateItem(
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
            suffix = textwrap.dedent(
                """\
                else:
                    cls._RejectAdditionalData(
                        item,
                        exclude_names=[{attribute_names}],
                    )

                {validation_statement}
                """,
            ).format(
                attribute_names=", ".join(['"{}"'.format(attribute_name) for attribute_name in attribute_names]),
                validation_statement=validation_statement_template.format("result"),
            )

        self._output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @classmethod
                def _{python_name}_Item(cls, item, always_include_optional, process_additional_data):
                    {prefix}{prefix_whitespace}{attributes_decl}{attributes}{statement}

                    # Additional data
                    if process_additional_data:
                        cls._ApplyAdditionalData(
                            item,
                            result,
                            exclude_names={{{attribute_names}}},
                        )
                    {suffix}
                    return result

                """,
            ).format(
                python_name=python_name,
                prefix=StringHelpers.LeftJustify("{}\n\n".format(prefix.strip()) if prefix else prefix, 4),
                prefix_whitespace="    " if prefix else "",
                suffix=StringHelpers.LeftJustify("\n{}\n".format(suffix.strip()) if suffix else suffix, 4),
                attributes_decl="" if not attributes else "attributes = OrderedDict()\n\n    ",
                attributes="" if not attributes else "{}\n\n    ".format(StringHelpers.LeftJustify("".join(attributes), 4).strip()),
                statement=StringHelpers.LeftJustify(statement, 4).strip(),
                attribute_names=", ".join(['"{}"'.format(attribute_name) for attribute_name in attribute_names]),
            ),
        )

    # ----------------------------------------------------------------------
    def _GenerateDictionary(self, element):
        key_element = None
        value_element = None

        for child in element.Children:
            if child.Name == element.key:
                assert key_element is None, key_element
                key_element = child.Resolve()

            if child.Name == element.value:
                assert value_element is None, value_element
                value_element = child.Resolve()

        assert key_element
        assert value_element

        # ----------------------------------------------------------------------
        def ToExtraParams(element):
            is_compound_like = isinstance(element.Resolve(), (Elements.CompoundElement, Elements.SimpleElement))

            if is_compound_like:
                return ", always_include_optional, process_additional_data"

            return ""

        # ----------------------------------------------------------------------

        if value_element.TypeInfo.Arity.IsCollection:
            if getattr(value_element, "as_dictionary", False):
                default_value = "{}"
            else:
                default_value = "[]"
        else:
            default_value = None

        self._output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @classmethod
                def _{python_name}_Item(cls, item, always_include_optional, process_additional_data):
                    result = OrderedDict()

                    for key, value in six.iteritems(item or {{}}):
                        try:
                            this_result = cls.{value_python_name}(value{value_extra_params})
                            if this_result is DoesNotExist:
                                if always_include_optional:
                                    this_result = {default_value}
                                else:
                                    continue

                            result[cls.{key_python_name}(key{key_extra_params})] = this_result
                        except:
                            _DecorateActiveException("Key '{{}}'".format(key))

                    return result

                """,
            ).format(
                python_name=ToPythonName(element),
                key_python_name=ToPythonName(key_element),
                value_python_name=ToPythonName(value_element),
                key_extra_params=ToExtraParams(key_element),
                value_extra_params=ToExtraParams(value_element),
                default_value=default_value,
            ),
        )
