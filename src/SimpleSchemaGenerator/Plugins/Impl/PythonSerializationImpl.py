# ----------------------------------------------------------------------
# |
# |  PythonSerializationImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-20 09:22:05
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the PythonSerializationImpl object"""

import os
import textwrap

from collections import OrderedDict

import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Interface
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers

from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
from CommonEnvironment.TypeInfo.ClassTypeInfo import ClassTypeInfo
from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo
from CommonEnvironment.TypeInfo.ListTypeInfo import ListTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.PythonCodeVisitor import PythonCodeVisitor

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

with InitRelativeImports():
    from ...Plugin import Plugin as PluginBase, ParseFlag
    from ...Schema import Attributes
    from ...Schema import Elements

    from .ElementVisitors import ToPythonName
    from .ElementVisitors.ItemMethodElementVisitor import ItemMethodElementVisitor
    from .ElementVisitors.TypeInfoElementVisitor import TypeInfoElementVisitor

    from .StatementWriters import SourceStatementWriter, DestinationStatementWriter
    from .StatementWriters.PythonDestinationStatementWriter import PythonDestinationStatementWriter
    from .StatementWriters.PythonSourceStatementWriter import PythonSourceStatementWriter

# ----------------------------------------------------------------------
class PythonSerializationImpl(PluginBase):
    """\
    Common base class for all plugins that serialize from python objects/dicts
    and deserialize to python objects.
    """

    # ----------------------------------------------------------------------
    # |
    # |  Methods
    # |
    # ----------------------------------------------------------------------
    @classmethod
    def __clsinit__(cls):
        cls.Flags = Interface.DerivedProperty(
            (ParseFlag.SupportAttributes if cls._SupportAttributes else 0)
            | ParseFlag.SupportIncludeStatements
            # | ParseFlag.SupportConfigStatements
            # | ParseFlag.SupportExtensionsStatements
            # | ParseFlag.SupportUnnamedDeclarations
            # | ParseFlag.SupportUnnamedObjects
            | ParseFlag.SupportNamedDeclarations
            | ParseFlag.SupportNamedObjects
            | ParseFlag.SupportRootDeclarations
            | ParseFlag.SupportRootObjects
            | ParseFlag.SupportChildDeclarations
            | ParseFlag.SupportChildObjects
            # | ParseFlag.SupportCustomElements
            | (ParseFlag.SupportAnyElements if cls._SupportAnyElements else 0)
            | ParseFlag.SupportReferenceElements
            | ParseFlag.SupportListElements
            | (ParseFlag.SupportSimpleObjectElements if cls._SupportAttributes else 0)
            | ParseFlag.SupportVariantElements
            | ParseFlag.ResolveReferences,
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetAdditionalGeneratorItems(cls, context):
        return [_script_fullpath, ItemMethodElementVisitor, TypeInfoElementVisitor, PythonDestinationStatementWriter, PythonSourceStatementWriter] + super(
            PythonSerializationImpl,
            cls,
        ).GetAdditionalGeneratorItems(context)

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GenerateCustomSettingsAndDefaults():
        yield "no_serialization", False
        yield "no_deserialization", False
        yield "custom_serialize_item_args", "{}"
        yield "custom_deserialize_item_args", "{}"

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def IsValidEnvironment():
        return True

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GenerateOutputFilenames(cls, context):
        yield os.path.join(
            context["output_dir"],
            "{}_{}Serialization.py".format(context["output_name"], cls.Name),
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetRequiredMetadataItems(cls, item):
        metadata_items = super(PythonSerializationImpl, cls).GetRequiredMetadataItems(item)

        # Ensure that SimpleElements include a value for the fundamental name.
        # By default, the attribute is optional but we want to make it required.
        if item.element_type == Elements.SimpleElement:
            found = False

            for attribute in Attributes.SIMPLE_ATTRIBUTE_INFO.OptionalItems:
                if attribute.Name == Attributes.SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME:
                    metadata_items.append(attribute)
                    found = True
                    break

            assert found

        return metadata_items

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def Generate(
        cls,
        simple_schema_code_generator,
        invoke_reason,
        input_filenames,
        output_filenames,
        name,
        elements,
        include_indexes,
        status_stream,
        verbose_stream,
        verbose,
        no_serialization,
        no_deserialization,
        custom_serialize_item_args,
        custom_deserialize_item_args,
    ):
        assert len(output_filenames) == 1, output_filenames
        output_filename = output_filenames[0]

        status_stream.write("Creating '{}'...".format(output_filename))
        with status_stream.DoneManager() as dm:
            include_map = cls._GenerateIncludeMap(elements, include_indexes)

            with open(output_filename, "w") as f:
                f.write(
                    cls._GenerateFileHeader(
                        prefix="# ",
                    ),
                )

                f.write(
                    textwrap.dedent(
                        """\
                        import copy
                        import sys

                        from collections import OrderedDict

                        import six

                        import CommonEnvironment
                        from CommonEnvironment.TypeInfo import Arity
                        from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
                        from CommonEnvironment.TypeInfo.ClassTypeInfo import ClassTypeInfo
                        from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo
                        from CommonEnvironment.TypeInfo.GenericTypeInfo import GenericTypeInfo
                        from CommonEnvironment.TypeInfo.ListTypeInfo import ListTypeInfo

                        from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.PythonCodeVisitor import PythonCodeVisitor

                        # <Unused import> pylint: disable = W0611
                        # <Unused import> pylint: disable = W0614
                        from CommonEnvironment.TypeInfo.FundamentalTypes.All import *               # <Wildcard import> pylint: disable = W0401

                        # <Standard import should be placed before...> pylint: disable = C0411

                        # ----------------------------------------------------------------------
                        """,
                    ),
                )

                cls._WriteFileHeader(f)
                with CallOnExit(lambda: cls._WriteFileFooter(f)):
                    f.write(
                        textwrap.dedent(
                            """\
                            # ----------------------------------------------------------------------
                            # <Method name "..." doesn't conform to PascalCase naming style> pylint: disable = C0103
                            # <Line too long> pylint: disable = C0301
                            # <Too many lines in module> pylint: disable = C0302
                            # <Wrong hanging indentation> pylint: disable = C0330

                            # <Too few public methods> pylint: disable = R0903
                            # <Too many public methods> pylint: disable = R0904
                            # <Too many branches> pylint: disable = R0912
                            # <Too many statements> pylint: disable = R0915


                            # ----------------------------------------------------------------------
                            class SerializationException(Exception):
                                def __init__(self, ex_or_string):
                                    if isinstance(ex_or_string, six.string_types):
                                        super(SerializationException, self).__init__(ex_or_string)
                                    else:
                                        super(SerializationException, self).__init__(str(ex_or_string))

                                        self.__dict__ = copy.deepcopy(ex_or_string.__dict__)


                            class UniqueKeySerializationException(SerializationException):              pass
                            class SerializeException(SerializationException):                           pass
                            class DeserializeException(SerializationException):                         pass


                            class DoesNotExist(object):                                                 pass


                            """,
                        ),
                    )

                    if no_serialization and no_deserialization:
                        return

                    elements = cls._CalculateElementsToWrite(elements, include_map)

                    top_level_elements = [element for element in elements if not element.IsDefinitionOnly and element.Parent not in elements]

                    if not top_level_elements:
                        return

                    serialize_source_writer = PythonSourceStatementWriter()
                    serialize_dest_writer = cls._DestinationStatementWriter()

                    deserialize_source_writer = cls._SourceStatementWriter()
                    deserialize_dest_writer = PythonDestinationStatementWriter()

                    # Global methods
                    f.write(
                        textwrap.dedent(
                            """\
                            # ----------------------------------------------------------------------
                            # |
                            # |  Utility Methods
                            # |
                            """,
                        ),
                    )

                    if not no_serialization:
                        cls._WriteGlobalMethods(
                            top_level_elements,
                            f,
                            serialize_source_writer,
                            serialize_dest_writer,
                            is_serialization=True,
                        )

                    if not no_deserialization:
                        cls._WriteGlobalMethods(
                            top_level_elements,
                            f,
                            deserialize_source_writer,
                            deserialize_dest_writer,
                            is_serialization=False,
                        )

                    # Serialize/Deserialize methods
                    if not no_serialization:
                        cls._WriteTopLevelMethods(
                            top_level_elements,
                            f,
                            serialize_source_writer,
                            serialize_dest_writer,
                            is_serialize=True,
                        )

                    if not no_deserialization:
                        cls._WriteTopLevelMethods(
                            top_level_elements,
                            f,
                            deserialize_source_writer,
                            deserialize_dest_writer,
                            is_serialize=False,
                        )

                    # Type Infos
                    cls._WriteTypeInfos(top_level_elements, elements, f)

                    # Serializer/Deserializer methods
                    if not no_serialization:
                        cls._WriteSerializer(
                            elements,
                            f,
                            serialize_source_writer,
                            serialize_dest_writer,
                            custom_serialize_item_args,
                        )

                    if not no_deserialization:
                        cls._WriteDeserializer(
                            elements,
                            f,
                            deserialize_source_writer,
                            deserialize_dest_writer,
                            custom_deserialize_item_args,
                        )

                    f.write(
                        textwrap.dedent(
                            """\
                            # ----------------------------------------------------------------------
                            # ----------------------------------------------------------------------
                            # ----------------------------------------------------------------------
                            def _ValidateUniqueKeys(unique_key_attribute_name, items):
                                unique_keys = set()

                                for item in items:
                                    if isinstance(item, dict):
                                        unique_key = item.get(unique_key_attribute_name)
                                    else:
                                        unique_key = getattr(item, unique_key_attribute_name)

                                    if unique_key in unique_keys:
                                        raise UniqueKeySerializationException("The unique key '{}' is not unique: '{}'".format(unique_key_attribute_name, unique_key))

                                    unique_keys.add(unique_key)


                            # ----------------------------------------------------------------------
                            def _DecorateActiveException(frame_desc):
                                exception = sys.exc_info()[1]

                                if not hasattr(exception, "stack"):
                                    setattr(exception, "stack", [])

                                exception.stack.insert(0, frame_desc)

                                # <The raise statement is not inside an except clause> pylint: disable = E0704
                                raise
                            """,
                        ),
                    )

            # Open the file again and trim all empty lines; this
            # is surprisingly difficult to do inline, which is why
            # it is implemented in a second pass.
            lines = []

            with open(output_filename) as f:
                for line in f.readlines():
                    if not line.strip():
                        lines.append("\n")
                    else:
                        lines.append(line)

            with open(output_filename, "w") as f:
                f.write("".join(lines))

    # ----------------------------------------------------------------------
    # |
    # |  Protected Types
    # |
    # ----------------------------------------------------------------------
    SourceStatementWriter                   = SourceStatementWriter
    DestinationStatementWriter              = DestinationStatementWriter

    # ----------------------------------------------------------------------
    # |
    # |  Private Properties
    # |
    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def _SupportAttributes(self):
        """Return True if attributes are supported"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def _SupportAnyElements(self):
        """Return True if the AnyElement type is supported"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def _TypeInfoSerializationName(self):
        """Returns the name of the TypeInfo object used by generated code during serialization activities"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def _SourceStatementWriter(self):
        """Returns the derived SourceStatementWriter type"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def _DestinationStatementWriter(self):
        """Returns the derived DestinationStatementWriter type"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def _WriteFileHeader(output_stream):
        """Writes a file header for the generated code"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def _WriteFileFooter(output_stream):
        """Writes a file footer for the generated code"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _CalculateElementsToWrite(cls, elements, include_map):
        include_dotted_names = set(six.iterkeys(include_map))

        to_write = []

        # ----------------------------------------------------------------------
        def OnEnteringElement(element):
            if element not in to_write:
                to_write.append(element)

        # ----------------------------------------------------------------------

        Elements.CreateElementVisitor(
            on_entering_element=OnEnteringElement,
        ).Accept(
            elements,
            include_dotted_names=include_dotted_names,
        )

        return to_write

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteGlobalMethods(
        cls,
        elements,
        output_stream,
        source_writer,
        dest_writer,
        is_serialization,
    ):
        if is_serialization:
            method_name = "Serialize"

            to_string_statements = dest_writer.SerializeToString("result")

            extra_args = textwrap.dedent(
                """
                to_string=False,
                """,
            )

            if "pretty_print" in to_string_statements:
                extra_args += textwrap.dedent(
                    """\
                    pretty_print=False,
                    """,
                )

            suffix = textwrap.dedent(
                """\
                if to_string:
                    result = {}

                """,
            ).format(StringHelpers.LeftJustify(to_string_statements, 4).strip())
        else:
            method_name = "Deserialize"
            extra_args = ""
            suffix = ""

        statements = []
        has_compound = False

        for element in elements:
            if isinstance(element.Resolve(), (Elements.CompoundElement, Elements.SimpleElement)):
                has_compound = True

                compound_args = textwrap.dedent(
                    """
                    process_additional_data=process_additional_data,
                    always_include_optional=always_include_optional,
                    """,
                )
            else:
                compound_args = ""

            statements.append(
                textwrap.dedent(
                    """\
                    this_result = {method_name}_{name}(
                        root,
                        is_root=True,{compound_args}
                    )
                    if this_result is not DoesNotExist:
                        {append_statement}
                    elif always_include_optional:
                        {append_empty_statement}

                    """,
                ).format(
                    method_name=method_name,
                    name=ToPythonName(element),
                    compound_args=StringHelpers.LeftJustify(compound_args, 4),
                    append_statement=StringHelpers.LeftJustify(
                        dest_writer.AppendChild(element, "result", "this_result"),
                        4,
                    ).strip(),
                    append_empty_statement=StringHelpers.LeftJustify(
                        dest_writer.AppendChild(element, "result", None),
                        4,
                    ).strip(),
                ),
            )

        if has_compound:
            compound_args = textwrap.dedent(
                """
                process_additional_data=False,
                always_include_optional=False,
                """,
            )
        else:
            compound_args = ""

        output_stream.write(
            textwrap.dedent(
                '''\
                # ----------------------------------------------------------------------
                def {method_name}(
                    root,{compound_args}{extra_args}
                ):
                    """Convenience method that {method_name_lower}s all top-level elements"""

                    {convenience}

                    result = {create_compound}

                    {statements}

                    {suffix}return result


                ''',
            ).format(
                method_name=method_name,
                method_name_lower=method_name.lower(),
                compound_args=StringHelpers.LeftJustify(compound_args, 4).rstrip(),
                extra_args=StringHelpers.LeftJustify(extra_args, 4).rstrip(),
                convenience=StringHelpers.LeftJustify(
                    source_writer.ConvenienceConversions("root", None) or "# No convenience conversions",
                    4,
                ).strip(),
                create_compound=StringHelpers.LeftJustify(
                    dest_writer.CreateCompoundElement(
                        dest_writer.CreateTemporaryElement('"_"', "1"),
                        None,
                    ),
                    4,
                ).strip(),
                suffix="{}\n\n    ".format(
                    StringHelpers.LeftJustify("{}\n\n".format(suffix), 4).strip(),
                ) if suffix else "",
                statements=StringHelpers.LeftJustify("".join(statements), 4).strip(),
            ),
        )

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteTopLevelMethods(
        cls,
        elements,
        output_stream,
        source_writer,
        dest_writer,
        is_serialize,
    ):
        if is_serialize:
            method_name = "Serialize"
        else:
            method_name = "Deserialize"

        for element in elements:
            if isinstance(element.Resolve(), (Elements.CompoundElement, Elements.SimpleElement)):
                compound_params = textwrap.dedent(
                    """
                    process_additional_data=False,
                    always_include_optional=False,
                    """,
                )

                compound_args = textwrap.dedent(
                    """
                    process_additional_data=process_additional_data,
                    always_include_optional=always_include_optional,
                    """,
                )
            else:
                compound_params = ""
                compound_args = ""

            optional_collection_clause = ""

            if element.TypeInfo.Arity.IsCollection:
                var_name = "items"

                if element.TypeInfo.Arity.Min == 0:
                    optional_collection_clause = textwrap.dedent(
                        """

                        if {var_name} is DoesNotExist:
                            {var_name} = []
                        """,
                    ).format(
                        var_name=var_name,
                    )
            else:
                var_name = "item"

            extra_args = ""
            suffix = ""

            if is_serialize:
                to_string_statements = dest_writer.SerializeToString(var_name)

                if to_string_statements:
                    extra_args = textwrap.dedent(
                        """
                        to_string=False,
                        pretty_print=False,
                        """,
                    )

                    suffix = textwrap.dedent(
                        """\

                        if to_string and {var_name} not in [DoesNotExist, None]:
                            {var_name} = {statement}
                        """,
                    ).format(
                        var_name=var_name,
                        statement=StringHelpers.LeftJustify(to_string_statements, 4).strip(),
                    )

            convenience_conversions = source_writer.ConvenienceConversions(var_name, element)
            if "is_root" in convenience_conversions:
                if not extra_args:
                    extra_args = "\n"

                extra_args += "is_root=False,\n"

            output_stream.write(
                textwrap.dedent(
                    '''\
                    # ----------------------------------------------------------------------
                    def {method_name}_{name}(
                        {var_name},{compound_params}{extra_args}
                    ):
                        """{method_name}s '{name}' from {source_type} to {dest_type}"""

                        {convenience}

                        try:
                            try:
                                {var_name} = {method_name}r().{resolved_name}(
                                    {var_name},{compound_args}
                                ){optional_collection_clause}
                            except:
                                _DecorateActiveException("{name}")
                        except SerializationException:
                            raise
                        except Exception as ex:
                            raise {method_name}Exception(ex)
                        {suffix}
                        return {var_name}


                    ''',
                ).format(
                    name=ToPythonName(element),
                    method_name=method_name,
                    resolved_name=ToPythonName(element.Resolve()),
                    var_name=var_name,
                    compound_params=StringHelpers.LeftJustify(compound_params, 4).rstrip(),
                    compound_args=StringHelpers.LeftJustify(compound_args, 16).rstrip(),
                    optional_collection_clause=StringHelpers.LeftJustify(
                        optional_collection_clause,
                        12,
                    ).rstrip(),
                    extra_args=StringHelpers.LeftJustify(extra_args, 4).rstrip(),
                    source_type=source_writer.ObjectTypeDesc,
                    dest_type=dest_writer.ObjectTypeDesc,
                    convenience=StringHelpers.LeftJustify(
                        convenience_conversions or "# No convenience conversions",
                        4,
                    ).strip(),
                    suffix=StringHelpers.LeftJustify(suffix, 4),
                ),
            )

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteTypeInfos(cls, top_level_elements, elements, output_stream):
        output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # |
                # |  Type Infos
                # |
                # ----------------------------------------------------------------------
                """,
            ),
        )

        type_info_template = "{0:<75} = {1}\n"

        # Write the top-level type infos
        python_code_visitor = PythonCodeVisitor()

        # ----------------------------------------------------------------------
        def OnElement(element):
            output_stream.write(
                type_info_template.format(
                    "{}_TypeInfo".format(ToPythonName(element)),
                    python_code_visitor.Accept(element.TypeInfo),
                ),
            )

        # ----------------------------------------------------------------------

        cls._VisitElements(top_level_elements, OnElement)
        output_stream.write("\n")

        # Write all type infos
        type_infos = OrderedDict()
        cached_children_statements = OrderedDict()

        type_info_visitor = TypeInfoElementVisitor(python_code_visitor, cached_children_statements)

        # ----------------------------------------------------------------------
        def OnElement(element):
            type_info_value = type_info_visitor.Accept(element)
            if type_info_value is not None:
                python_name = ToPythonName(element)

                type_infos["_{}_TypeInfo".format(python_name)] = type_info_value

                if isinstance(element, Elements.SimpleElement):
                    type_infos["_{}__value__TypeInfo".format(python_name)] = python_code_visitor.Accept(
                        element.TypeInfo.Items[element.FundamentalAttributeName],
                    )

            if isinstance(element, Elements.VariantElement):
                for variation in element.Variations:
                    if isinstance(variation, Elements.ReferenceElement):
                        continue

                    assert isinstance(variation, Elements.FundamentalElement), variation
                    type_info_value = type_info_visitor.Accept(variation)

                    if type_info_value is not None:
                        type_infos["_{}_TypeInfo".format(ToPythonName(variation))] = type_info_value

        # ----------------------------------------------------------------------

        cls._VisitElements(elements, OnElement)

        if cached_children_statements:
            for k, v in six.iteritems(cached_children_statements):
                output_stream.write(type_info_template.format(v, k))

            output_stream.write("\n")

        for k, v in six.iteritems(type_infos):
            output_stream.write(type_info_template.format(k, v))

        output_stream.write("\n")

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteSerializer(
        cls,
        elements,
        output_stream,
        source_writer,
        dest_writer,
        custom_serialize_item_args,
    ):
        output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # |
                # |  Serializer
                # |
                # ----------------------------------------------------------------------
                class Serializer(object):

                """,
            ),
        )

        cls._WriteImpl(
            elements,
            output_stream,
            custom_serialize_item_args,
            source_writer,
            dest_writer,
            is_serializer=True,
        )

        indented_stream = StreamDecorator(
            output_stream,
            line_prefix="    ",
        )

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteDeserializer(
        cls,
        elements,
        output_stream,
        source_writer,
        dest_writer,
        custom_deserialize_item_args,
    ):
        output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # |
                # |  Deserializer
                # |
                # ----------------------------------------------------------------------
                class Deserializer(object):

                """,
            ),
        )

        cls._WriteImpl(
            elements,
            output_stream,
            custom_deserialize_item_args,
            source_writer,
            dest_writer,
            is_serializer=False,
        )

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteImpl(
        cls,
        elements,
        output_stream,
        custom_serialize_item_args,
        source_writer,
        dest_writer,
        is_serializer,
    ):
        indented_stream = StreamDecorator(
            output_stream,
            line_prefix="    ",
        )

        content_stream = StreamDecorator(
            indented_stream,
            line_prefix="    ",
        )

        # Write the arity-based methods

        # ----------------------------------------------------------------------
        def OnElement(element):
            python_name = ToPythonName(element)

            resolved_element = element.Resolve()

            if resolved_element.TypeInfo.Arity.IsCollection:
                arg_name = "items"
                item_name = "this_item"
                result_name = "results"

                # ----------------------------------------------------------------------
                def ApplyContent(statement):
                    unique_statement = None

                    if hasattr(resolved_element, "unique_key"):
                        unique_statement = '_ValidateUniqueKeys("{unique_key}", {arg_name})\n\n'.format(
                            unique_key=resolved_element.unique_key,
                            arg_name=arg_name if is_serializer else result_name,
                        )

                    if unique_statement and is_serializer:
                        content_stream.write(unique_statement)

                    content_stream.write(
                        textwrap.dedent(
                            """\
                            {result_name} = []

                            for this_index, this_item in enumerate({arg_name} or []):
                                try:
                                    {result_name}.append({statement})
                                except:
                                    _DecorateActiveException("Index {{}}".format(this_index))
                            """,
                        ).format(
                            result_name=result_name,
                            arg_name=arg_name,
                            statement=statement,
                        ),
                    )

                    if unique_statement and not is_serializer:
                        content_stream.write("\n")
                        content_stream.write(unique_statement)

                # ----------------------------------------------------------------------
            else:
                arg_name = "item"
                item_name = arg_name
                result_name = "result"

                # ----------------------------------------------------------------------
                def ApplyContent(statement):
                    content_stream.write(
                        textwrap.dedent(
                            """\
                            {result_name} = {statement}
                            """,
                        ).format(
                            result_name=result_name,
                            statement=statement,
                        ),
                    )

                # ----------------------------------------------------------------------

            is_compound_like = isinstance(
                resolved_element,
                (Elements.CompoundElement, Elements.SimpleElement),
            )

            if is_compound_like:
                extra_params = ", always_include_optional, process_additional_data"
            else:
                extra_params = ""

            # Write the header
            indented_stream.write(
                textwrap.dedent(
                    """\
                    # ----------------------------------------------------------------------
                    @classmethod
                    def {python_name}(cls, {arg_name}{extra_params}):
                    """,
                ).format(
                    python_name=python_name,
                    arg_name=arg_name,
                    extra_params=extra_params,
                ),
            )

            # Reference content...
            if isinstance(element, Elements.ReferenceElement):
                content_stream.write(
                    textwrap.dedent(
                        """\
                        return cls.{reference_python_name}({arg_name}{extra_params})

                        """,
                    ).format(
                        reference_python_name=ToPythonName(element.Reference),
                        arg_name=arg_name,
                        extra_params=extra_params,
                    ),
                )
                return

            # Standard content...
            does_not_exist_items = ["DoesNotExist", "None"]

            if element.TypeInfo.Arity.IsCollection:
                does_not_exist_items.append("[]")

            content_stream.write(
                textwrap.dedent(
                    """\
                    if {arg_name} in [{does_not_exist_items}]:
                        _{python_name}_TypeInfo.ValidateArity(None)
                        return DoesNotExist

                    """,
                ).format(
                    python_name=python_name,
                    does_not_exist_items=", ".join(does_not_exist_items),
                    arg_name=arg_name,
                ),
            )

            if is_serializer:
                content_stream.write(
                    textwrap.dedent(
                        """\
                        _{python_name}_TypeInfo.ValidateArity({arg_name})

                        """,
                    ).format(
                        python_name=python_name,
                        arg_name=arg_name,
                    ),
                )

            ApplyContent(
                "cls._{python_name}_Item({item_name}{extra_params})".format(
                    python_name=python_name,
                    item_name=item_name,
                    extra_params=extra_params,
                ),
            )

            if not is_serializer:
                content_stream.write(
                    textwrap.dedent(
                        """\

                        _{python_name}_TypeInfo.ValidateArity({result_name})
                        """,
                    ).format(
                        python_name=python_name,
                        result_name=result_name,
                    ),
                )

            if element.TypeInfo.Arity.IsCollection:
                return_statement = dest_writer.CreateCollection(element, result_name)
            else:
                return_statement = result_name

            content_stream.write(
                textwrap.dedent(
                    """\

                    return {return_statement}

                    """,
                ).format(
                    return_statement=return_statement,
                ),
            )

        # ----------------------------------------------------------------------

        cls._VisitElements(elements, OnElement)

        indented_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                """,
            ),
        )

        # Item_ methods
        ItemMethodElementVisitor(
            cls._TypeInfoSerializationName,
            custom_serialize_item_args,
            source_writer,
            dest_writer,
            indented_stream,
            cls._EnumerateChildren,
            is_serializer,
        ).Accept(elements)

        indented_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                """,
            ),
        )

        # _ApplyOptionalChild/_ApplyOptionalChildren/_ApplyOptionalAttribute
        content_template = textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            @classmethod
            def {method_name}(cls, {var_name}, attribute_name, dest, apply_func, always_include_optional):
                value = {get_statement}

                if value is not DoesNotExist:
                    value = apply_func(value)
                    if value is not DoesNotExist:
                        {add_child}
                        return

                if always_include_optional:
                    {add_child_empty}

            """,
        )

        optional_child_empty_element = source_writer.CreateTemporaryElement("attribute_name", "?")

        indented_stream.write(
            content_template.format(
                method_name="_ApplyOptionalChild",
                var_name="item",
                get_statement=StringHelpers.LeftJustify(
                    source_writer.GetChild("item", optional_child_empty_element),
                    4,
                ).strip(),
                add_child=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(optional_child_empty_element, "dest", "value"),
                    12,
                ).strip(),
                add_child_empty=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(optional_child_empty_element, "dest", None),
                    8,
                ).strip(),
            ),
        )

        optional_children_empty_element = dest_writer.CreateTemporaryElement("attribute_name", "*")

        indented_stream.write(
            content_template.format(
                method_name="_ApplyOptionalChildren",
                var_name="items",
                get_statement=StringHelpers.LeftJustify(
                    source_writer.GetChild("items", optional_children_empty_element),
                    4,
                ).strip(),
                add_child=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(optional_children_empty_element, "dest", "value"),
                    12,
                ).strip(),
                add_child_empty=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(optional_children_empty_element, "dest", None),
                    8,
                ).strip(),
            ),
        )

        optional_attribute_empty_element = dest_writer.CreateTemporaryElement(
            "attribute_name",
            "?",
            is_attribute=True,
        )

        indented_stream.write(
            content_template.format(
                method_name="_ApplyOptionalAttribute",
                var_name="item",
                get_statement=StringHelpers.LeftJustify(
                    source_writer.GetChild("item", optional_attribute_empty_element),
                    4,
                ).strip(),
                add_child="dest[attribute_name] = value",
                add_child_empty="dest[attribute_name] = None",
            ),
        )

        # _ApplyAdditionalData
        temporary_children_element = source_writer.CreateTemporaryElement("name", "+")

        indented_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @classmethod
                def _ApplyAdditionalData(
                    cls,
                    source,
                    dest,
                    exclude_names,
                ):
                    for name, child in {get_additional_children}:
                        try:
                            if isinstance(child, list):
                                children = []

                                for index, item in enumerate(child):
                                    item_name = "Index {{}}".format(index)

                                    try:
                                        children.append(cls._CreateAdditionalDataItem(item_name, item))
                                    except:
                                        _DecorateActiveException(item_name)

                                {append_children}
                            else:
                                {append}
                        except:
                            _DecorateActiveException(name)

                """,
            ).format(
                get_additional_children=StringHelpers.LeftJustify(
                    source_writer.GetAdditionalDataChildren(),
                    4,
                ).strip(),
                append=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(
                        source_writer.CreateTemporaryElement("name", "1"),
                        "dest",
                        "cls._CreateAdditionalDataItem(name, child)",
                    ),
                    12,
                ).strip(),
                append_children=StringHelpers.LeftJustify(
                    dest_writer.AppendChild(
                        temporary_children_element,
                        "dest",
                        dest_writer.CreateCollection(temporary_children_element, "children"),
                    ),
                    12,
                ).strip(),
            ),
        )

        # _CreateAdditionalDataItem
        indented_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                @classmethod
                def _CreateAdditionalDataItem(cls, name, source):
                    {statements}

                """,
            ).format(
                statements=StringHelpers.LeftJustify(
                    source_writer.CreateAdditionalDataItem(dest_writer, "name", "source"),
                    4,
                ).strip(),
            ),
        )

        # Write the utility funcs
        result = dest_writer.GetClassUtilityMethods(source_writer)
        if result is not None:
            indented_stream.write("{}\n\n".format(result.strip()))

        result = source_writer.GetClassUtilityMethods(dest_writer)
        if result is not None:
            indented_stream.write("{}\n\n".format(result.strip()))

        output_stream.write("\n")

        result = source_writer.GetGlobalUtilityMethods(dest_writer)
        if result is not None:
            output_stream.write("{}\n\n\n".format(result.strip()))

        result = dest_writer.GetGlobalUtilityMethods(source_writer)
        if result is not None:
            output_stream.write("{}\n\n\n".format(result.strip()))

    # ----------------------------------------------------------------------
    @staticmethod
    def _VisitElements(elements, on_element_func, *args, **kwargs):
        Elements.CreateElementVisitor(
            on_entering_element=on_element_func,
            on_compound_visiting_children_func=lambda element: False,
            on_simple_visiting_children_func=lambda element: False,
        ).Accept(elements, *args, **kwargs)
