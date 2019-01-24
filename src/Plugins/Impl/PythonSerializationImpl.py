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
from CommonEnvironment.TypeInfo.FundamentalTypes.StringTypeInfo import StringTypeInfo

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

with InitRelativeImports():
    from ...Plugin import Plugin as PluginBase, ParseFlag
    from ...Schema import Attributes
    from ...Schema import Elements

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
            | ParseFlag.ResolveReferences
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetAdditionalGeneratorItems(cls, context):
        return [_script_fullpath] + super(PythonSerializationImpl, cls).GetAdditionalGeneratorItems(
            context,
        )

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

                cls._WriteFileHeader(f)
                with CallOnExit(lambda: cls._WriteFileFooter(f)):
                    f.write(
                        textwrap.dedent(
                            """\
                            # ----------------------------------------------------------------------
                            # <Method name "..." doesn't conform to PascalCase naming style> pylint: disable = C0103
                            # <Line too long> pylint: disable = C0301

                            # <Too many public methods> pylint: disable = R0904
                            # <Too many branches> pylint: disable = R0912
                            # <Too many statements> pylint: disable = R0915

                            # <Unused import> pylint: disable = W0611
                            # <Unused import> pylint: disable = W0614

                            """,
                        )
                    )

                    if no_serialization and no_deserialization:
                        return

                    elements = cls._CalculateElementsToWrite(elements, include_map)

                    top_level_elements = [
                        element
                        for element in elements
                        if isinstance(
                            element.Resolve(),
                            (Elements.CompoundElement, Elements.SimpleElement),
                        ) and not element.IsDefinitionOnly and element.Parent not in elements
                    ]

                    if not top_level_elements:
                        return

                    cls._WriteGlobalMethods(top_level_elements, f)

                    if not no_serialization:
                        cls._WriteSerializeMethods(top_level_elements, f)

                    if not no_deserialization:
                        cls._WriteDeserializeMethods(top_level_elements, f)

                    cls._WriteTypeInfos(top_level_elements, elements, f)

                    if not no_serialization:
                        cls._WriteSerializer(elements, f, custom_serialize_item_args)

                    if not no_deserialization:
                        cls._WriteDeserializer(elements, f, custom_deserialize_item_args)

    # ----------------------------------------------------------------------
    # |
    # |  Protected Types
    # |
    # ----------------------------------------------------------------------
    class StatementWriter(Interface.Interface):
        """Contains helper methods used by all StatementWriter objects."""

        # ----------------------------------------------------------------------
        @staticmethod
        def GetElementStatementName(element):
            """\
            Returns a value that can be used within a statement
            to represent the name of an element.
            """

            if callable(element.Name):
                return element.Name()

            return '"{}"'.format(element.Name)

        # ----------------------------------------------------------------------
        @staticmethod
        def CreateTemporaryElement(name, is_collection):
            return Elements.Element(
                StringTypeInfo(
                    arity="*" if is_collection else "1",
                ),
                lambda: name,
                parent=None,
                source=None,
                line=None,
                column=None,
                is_definition_only=None,
                is_external=None,
            )

    # ----------------------------------------------------------------------
    class SourceStatementWriter(StatementWriter):
        """\
        Interface for components that are able to write python statements used when
        reading objects.
        """

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.abstractmethod
        def GetChild(var_name, child_element):
            """Gets the child_element from a variable"""
            raise Exception("Abstract method")

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.abstractmethod
        def GetFundamentalString(var_name, child_element, is_attribute):
            """Gets the string representation of the fundamental child element from a variable"""
            raise Exception("Abstract method")

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.abstractmethod
        def GetApplyAdditionalData(dest_writer):
            """Creates the statements for the _ApplyAdditionalData method"""
            raise Exception("Abstract method")

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.abstractmethod
        def GetUtilityMethods(dest_writer):
            """Returns any statements that should be written"""
            raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    class DestinationStatementWriter(StatementWriter):
        """\
        Interface for components that are able to write python statements used when
        writing objects.
        """

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.abstractmethod
        def CreateCompoundElement(element, attributes_var_or_none):
            """Creates a CompoundElement"""
            raise Exception("Abstract method")

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.abstractmethod
        def CreateSimpleElement(element, attributes_var_or_none, fundamental_statement):
            """Creates a SimpleElement"""
            raise Exception("Abstract method")

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.abstractmethod
        def CreateFundamentalElement(element, fundamental_statement):
            """Create a FundamentalElement"""
            raise Exception("Abstract method")

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.abstractmethod
        def AppendChild(child_element, parent_var_name, var_name_or_none):
            """Appends a child to an existing CompoundElement"""
            raise Exception("Abstract method")

        # ----------------------------------------------------------------------
        @staticmethod
        @Interface.abstractmethod
        def GetUtilityMethods(source_writer):
            """Returns any statements that should be written"""
            raise Exception("Abstract method")

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

    # BugBug # ----------------------------------------------------------------------
    # BugBug @Interface.abstractproperty
    # BugBug def _SourceStatementWriter(self):
    # BugBug     """Returns the derived SourceStatementWriter type"""
    # BugBug     raise Exception("Abstract property")

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

        # Calculate the elements that are referenced
        referenced = set()

        # ----------------------------------------------------------------------
        def OnReference(element):
            referenced.add(element.Reference)

        # ----------------------------------------------------------------------

        Elements.CreateElementVisitor(
            on_reference_func=OnReference,
        ).Accept(
            elements,
            include_dotted_names=include_dotted_names,
        )

        # Calculate the elements to write
        to_write = []

        # ----------------------------------------------------------------------
        def ShouldWrite(element):
            if element.IsDefinitionOnly and element not in referenced:
                return False

            if element.DottedName in include_map and include_map[element.DottedName].Type == cls.IncludeMapType.Parent:
                return False

            return True

        # ----------------------------------------------------------------------
        def OnEnteringElement(element):
            if ShouldWrite(element) and element not in to_write:
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
    def _WriteGlobalMethods(cls, elements, output_stream):
        pass  # BugBug

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteSerializeMethods(cls, elements, output_stream):
        pass  # BugBug

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteDeserializeMethods(cls, elements, output_stream):
        pass  # BugBug

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
            )
        )

        type_info_template = "{0:<75} = {1}\n"

        # Write the top-level type infos
        python_code_visitor = PythonCodeVisitor()

        # ----------------------------------------------------------------------
        def OnElement(element):
            output_stream.write(
                type_info_template.format(
                    "{}_TypeInfo".format(_ToPythonName(element)),
                    python_code_visitor.Accept(element.TypeInfo),
                ),
            )

        # ----------------------------------------------------------------------

        cls._VisitElements(top_level_elements, OnElement)
        output_stream.write("\n")

        # Write all type infos
        type_infos = OrderedDict()
        cached_children_statements = OrderedDict()

        type_info_visitor = _TypeInfoElementVisitor()

        # ----------------------------------------------------------------------
        def OnElement(element):
            type_info_value = type_info_visitor.Accept(
                element,
                python_code_visitor,
                cached_children_statements,
            )

            if type_info_value is not None:
                type_infos["_{}_TypeInfo".format(_ToPythonName(element))] = type_info_value

        # ----------------------------------------------------------------------

        cls._VisitElements(elements, OnElement)

        if cached_children_statements:
            for k, v in six.iteritems(cached_children_statements):
                output_stream.write(type_info_template.format(v, k))

            output_stream.write("\n")

        for k, v in six.iteritems(type_infos):
            output_stream.write(type_info_template.format(k, v))

        output_stream.write(
            textwrap.dedent(
                """\

                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                class Object(object):
                    def __repr__(self):
                        return CommonEnvironment.ObjectReprImpl(self)

                class SerializationException(Exception):                                    pass
                class UniqueKeySerializationException(SerializationException):              pass
                class SerializeException(SerializationException):                           pass
                class DeserializeException(SerializationException):                         pass

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
            )
        )

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteSerializer(cls, elements, output_stream, custom_serialize_item_args):
        output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # |
                # |  Serializer
                # |
                # ----------------------------------------------------------------------
                class Serializer(object):
                    # BugBug: SerializeImpl

                """,
            )
        )

        source_writer = _PythonSourceStatementWriter()
        dest_writer = cls._DestinationStatementWriter()

        cls._WriteImpl(
            elements,
            output_stream,
            custom_serialize_item_args,
            source_writer,
            dest_writer,
            is_serializer=True,
        )

    # ----------------------------------------------------------------------
    @classmethod
    def _WriteDeserializer(cls, elements, output_stream, custom_deserialize_item_args):
        output_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # |
                # |  Deserializer
                # |
                # ----------------------------------------------------------------------
                class Deserializer(object):
                    # BugBug: DeserializeImpl

                """,
            )
        )

        source_writer = _PythonSourceStatementWriter()  # BugBug cls._SourceStatementWraier()
        dest_writer = _PythonDestinationStatementWriter()

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
        # BugBug
        if not is_serializer:
            return
        # BugBug

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
            python_name = _ToPythonName(element)

            is_compound_like = isinstance(
                element.Resolve(),
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
                    def {python_name}(cls, item{extra_params}):
                    """,
                ).format(
                    python_name=python_name,
                    extra_params=extra_params,
                )
            )

            # Reference content...
            if isinstance(element, Elements.ReferenceElement):
                content_stream.write(
                    textwrap.dedent(
                        """\
                        return cls.{reference_python_name}(item{extra_params})

                        """,
                    ).format(
                        reference_python_name=_ToPythonName(element.Reference),
                        extra_params=extra_params,
                    )
                )
                return

            # Standard content...
            if element.TypeInfo.Arity.IsCollection:
                arg_name = "items"
                result_name = "results"

                # ----------------------------------------------------------------------
                def ApplyContent(statement):
                    unique_statement = None

                    if hasattr(element, "unique_key"):
                        unique_statement = '_ValidateUniqueKeys("{unique_key}", {arg_name})\n\n'.format(
                            unique_key=element.unique_key,
                            arg_name=arg_name if is_serializer else result_name,
                        )

                    if unique_statement and is_serializer:
                        content_stream.write(unique_statement)

                    content_stream.write(
                        textwrap.dedent(
                            """\
                            {result_name} = []

                            for this_index, this_item in enumerate({arg_name}):
                                try:
                                    {result_name}.append({statement})
                                except:
                                    _DecorateActiveException("Index {{}}".format(this_index))
                            """,
                        ).format(
                            result_name=result_name,
                            arg_name=arg_name,
                            statement=statement,
                        )
                    )

                    if unique_statement and not is_serializer:
                        content_stream.write(unique_statement)

                # ----------------------------------------------------------------------
            else:
                arg_name = "item"
                result_name = "result"

                # ----------------------------------------------------------------------
                def ApplyContent(statement):
                    content_stream.write(
                        "{result_name} = {statement}".format(
                            result_name=result_name,
                            statement=statement,
                        ),
                    )

                # ----------------------------------------------------------------------

            if is_serializer:
                content_stream.write(
                    textwrap.dedent(
                        """\
                        {python_name}_TypeInfo.ValidateArity({arg_name})

                        if {arg_name} is None:
                            return None

                        """,
                    ).format(
                        python_name=python_name,
                        arg_name=arg_name,
                    )
                )

            ApplyContent(
                "cls._{python_name}_Item(item{extra_params})".format(
                    python_name=python_name,
                    extra_params=extra_params,
                ),
            )

            if not is_serializer:
                content_stream.write(
                    textwrap.dedent(
                        """\
                        {python_name}_TypeInfo.ValidateArity({result_name})

                        """,
                    ).format(
                        python_name=python_name,
                        result_name=result_name,
                    )
                )

            content_stream.write(
                textwrap.dedent(
                    """\

                    return {result_name}

                    """,
                ).format(
                    result_name=result_name,
                )
            )

        # ----------------------------------------------------------------------

        cls._VisitElements(elements, OnElement)

        # Item_ methods

        # ----------------------------------------------------------------------
        @Interface.staticderived
        class Visitor(_ElementVisitor):
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
            @staticmethod
            @Interface.override
            def OnFundamental(element):
                python_name = _ToPythonName(element)

                statement = "{type_info}.SerializeItem({python_name}_TypeInfo, item, **{serialize_args})".format(
                    type_info=cls._TypeInfoSerializationName,
                    python_name=python_name,
                    serialize_args=custom_serialize_item_args,
                )

                if not element.IsAttribute:
                    statement = dest_writer.CreateFundamentalElement(element, statement)

                indented_stream.write(
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
            @staticmethod
            @Interface.override
            def OnCompound(element):
                pass  # BugBug

            # ----------------------------------------------------------------------
            @staticmethod
            @Interface.override
            def OnSimple(element):
                pass  # BugBug

            # ----------------------------------------------------------------------
            @staticmethod
            @Interface.override
            def OnVariant(element):
                pass  # BugBug

            # ----------------------------------------------------------------------
            @staticmethod
            @Interface.override
            def OnReference(element):
                # Nothing to do here
                pass

            # ----------------------------------------------------------------------
            @staticmethod
            @Interface.override
            def OnList(element):
                pass  # BugBug

            # ----------------------------------------------------------------------
            @staticmethod
            @Interface.override
            def OnAny(element):
                pass  # BugBug

        # ----------------------------------------------------------------------

        Visitor().Accept(elements)

        # Helper methods
        indented_stream.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                @classmethod
                def _ApplyAdditionalData(
                    cls,
                    source,
                    dest,
                    exclude_names=None,
                ):
                    exclude_names = exclude_names or set()

                    {}

                {}

                {}
                """,
            ).format(
                StringHelpers.LeftJustify(
                    source_writer.GetApplyAdditionalData(dest_writer).strip(),
                    4,
                ).strip(),
                source_writer.GetUtilityMethods(dest_writer).strip(),
                dest_writer.GetUtilityMethods(source_writer).strip(),
            )
        )

        output_stream.write("\n\n")

    # ----------------------------------------------------------------------
    @staticmethod
    def _VisitElements(elements, on_element_func, *args, **kwargs):
        Elements.CreateElementVisitor(
            on_entering_element=on_element_func,
            on_compound_visiting_children_func=lambda element: False,
            on_simple_visited_children_func=lambda element: False,
        ).Accept(elements, *args, **kwargs)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
_PYTHON_ATTRIBUTES_ATTRIBUTE_NAME           = "_attributes_"
_PYTHON_FUNDAMENTAL_DEFAULT_ATTRIBUTE_NAME  = "_value_"


# ----------------------------------------------------------------------
class _ElementVisitor(Elements.ElementVisitor):
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnCustom(element, *args, **kwargs):
        raise Exception("CustomElements are not supported")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnExtension(element, *args, **kwargs):
        raise Exception("ExtensionElements are not supported")


# ----------------------------------------------------------------------
@Interface.staticderived
class _PythonSourceStatementWriter(PythonSerializationImpl.SourceStatementWriter):
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GetChild(var_name, child_element):
        return 'cls._GetPythonAttribute({}, "{}")'.format(var_name, child_element.Name)

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GetFundamentalString(var_name, child_element, is_attribute):
        pass  # BugBug

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetApplyAdditionalData(cls, dest_writer):
        temporary_element = dest_writer.CreateTemporaryElement(
            "k",
            is_collection=False,
        )

        return textwrap.dedent(
            """\
            if not isinstance(source, dict):
                source = source.__dict__

            for k, v in six.iteritems(source):
                if k.startswith("_") or k in exclude_names:
                    continue

                # BugBug: Handle lists
                if isinstance(v, dict):
                    child = {create_compound_element_statement}

                    cls._ApplyAdditionalData(
                        v,
                        child,
                        exclude_names=exclude_names,
                    )

                    v = child
                else:
                    v = {create_fundamental_element_statement}

                {append_statement}
            """,
        ).format(
            create_compound_element_statement=StringHelpers.LeftJustify(
                dest_writer.CreateCompoundElement(temporary_element, None),
                8,
            ).strip(),
            create_fundamental_element_statement=StringHelpers.LeftJustify(
                dest_writer.CreateFundamentalElement(temporary_element, "str(v)"),
                8,
            ).strip(),
            append_statement=StringHelpers.LeftJustify(
                dest_writer.AppendChild(
                    dest_writer.CreateTemporaryElement(
                        "k",
                        is_collection=False,
                    ),
                    "dest",
                    "v",
                ),
                4,
            ).strip(),
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetUtilityMethods(cls, dest_writer):
        optional_child_empty_element = dest_writer.CreateTemporaryElement(
            "attribute_name",
            is_collection=False,
        )
        optional_children_empty_element = dest_writer.CreateTemporaryElement(
            "attribute_name",
            is_collection=True,
        )

        return textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            class PythonAttributeDoesNotExist(object):
                pass

            # ----------------------------------------------------------------------
            @classmethod
            def _GetPythonAttribute(
                cls,
                item,
                attribute_name,
                default_value=cls.PythonAttributeDoesNotExist,
            ):
                if isinstance(item, dict):
                    return item.get(attribute_name, default_value)

                return getattr(item, attribute_name, default_value)

            # ----------------------------------------------------------------------
            @classmethod
            def _ApplyOptionalChild(cls, item, attribute_name, dest, apply_func, always_include_optional):
                value = cls._GetPythonAttribute(item, attribute_name)
                if value is not PythonAttributeDoesNotExist:
                    value = apply_func(value)
                    {add_child}
                    return

                if always_include_optional:
                    {add_child_empty}

            # ----------------------------------------------------------------------
            @classmethod
            def _ApplyOptionalChildren(cls, item, attribute_name, dest, apply_func, always_include_optional):
                value = cls._GetPythonAttribute(item, attribute_name)
                if value is not PythonAttributeDoesNotExist:
                    value = apply_func(value)
                    {add_children}
                    return

                if always_include_optional:
                    {add_children_empty}

            """,
        ).format(
            add_child=StringHelpers.LeftJustify(
                dest_writer.AppendChild(optional_child_empty_element, "dest", "value"),
                8,
            ).strip(),
            add_child_empty=StringHelpers.LeftJustify(
                dest_writer.AppendChild(optional_child_empty_element, "dest", None),
                8,
            ).strip(),
            add_children=StringHelpers.LeftJustify(
                dest_writer.AppendChild(optional_children_empty_element, "dest", "value"),
                8,
            ).strip(),
            add_children_empty=StringHelpers.LeftJustify(
                dest_writer.AppendChild(optional_children_empty_element, "dest", None),
                8,
            ).strip(),
        )


# ----------------------------------------------------------------------
@Interface.staticderived
class _PythonDestinationStatementWriter(PythonSerializationImpl.DestinationStatementWriter):
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def CreateCompoundElement(element, attributes_var_or_none):
        return textwrap.dedent(
            """\
            cls._CreateObject(
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
            cls._CreateObject(
                attributes={attributes},
                **{{{value_name}: {fundamental}}},
            )
            """,
        ).format(
            attributes=attributes_var_or_none or "None",
            value_name=getattr(
                element,
                Attributes.SIMPLE_FUNDAMENTAL_NAME_ATTRIBUTE_NAME,
                _PYTHON_FUNDAMENTAL_DEFAULT_ATTRIBUTE_NAME,
            ),
            fundamental=fundamental_statement,
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def CreateFundamentalElement(element, fundamental_statement):
        return fundamental_statement

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def AppendChild(child_element, parent_var_name, var_name_or_none):
        if var_name_or_none is None:
            var_name_or_none = "[]" if child_element.TypeInfo.Arity.IsCollection else "None"

        return "setattr({}, {}, {})".format(parent_var_name, child_element.Name, var_name_or_none)

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GetUtilityMethods(source_writer):
        return textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            @staticmethod
            def _CreateObject(
                attributes=None,
            ):
                result = Object()

                for k, v in six.iteritems(attributes or {}):
                    setattr(result, k, v)

                return result

            """,
        )


# ----------------------------------------------------------------------
class _ElementVisitor(Elements.ElementVisitor):
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
@Interface.staticderived
class _TypeInfoElementVisitor(_ElementVisitor):

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnFundamental(element, python_code_visitor, cached_children_statements):
        return python_code_visitor.Accept(element.TypeInfo)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnCompound(cls, element, python_code_visitor, cached_children_statements):
        # Rather than using the existing type info, convert this into a structure
        # that can process classes or dictionaries. Also, handle the processing of
        # recursive data structure by creating a TypeInfo object that only parses one
        # level deep.
        children_statement = "OrderedDict([{}])".format(
            ", ".join(
                [
                    '("{}", GenericTypeInfo({}))'.format(
                        k,
                        cls._ToArityString(
                            v.Arity,
                            comma_prefix=False,
                        ),
                    ) for k, v in six.iteritems(element.TypeInfo.Items) if k is not None
                ]
            )
        )

        if children_statement not in cached_children_statements:
            cached_children_statements[children_statement] = "_{}_TypeInfo_Contents".format(
                _ToPythonName(element),
            )

        return "AnyOfTypeInfo([ClassTypeInfo({children}, require_exact_match=False), DictTypeInfo({children}, require_exact_match=False)]{arity})".format(
            children=cached_children_statements[children_statement],
            arity=cls._ToArityString(element.TypeInfo.Arity),
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnSimple(cls, element, python_code_visitor, cached_children_statements):
        # Use OnCompound to create type info information that reads the attributes. Write the
        # value type info as a separate type info object.
        return cls.OnCompound(element, python_code_visitor, cached_children_statements)

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnVariant(element, python_code_visitor, cached_children_statements):
        return python_code_visitor.Accept(element.TypeInfo)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnReference(cls, element, python_code_visitor, cached_children_statements):
        # References don't have type info objects
        return None

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnList(cls, element, python_code_visitor, cached_children_statements):
        return "ListTypeInfo(_{}_TypeInfo{})".format(
            _ToPythonName(element.Reference),
            cls._ToArityString(element.TypeInfo.Arity),
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnAny(element, python_code_visitor, cached_children_statements):
        return python_code_visitor.Accept(element.TypeInfo)

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
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ToPythonName(element):
    name = element.DottedName

    for char in [".", "-", " "]:
        name = name.replace(char, "_")

    return name
