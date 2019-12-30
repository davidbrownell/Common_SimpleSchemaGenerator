# ----------------------------------------------------------------------
# |
# |  XsdSchemaPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-20 19:38:27
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Pluign object"""

import os
import textwrap

from collections import OrderedDict

import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Interface
from CommonEnvironment import RegularExpression
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers
from CommonEnvironment.TypeInfo.FundamentalTypes.BoolTypeInfo import BoolTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import RegularExpressionVisitor
from CommonEnvironment.TypeInfo.FundamentalTypes.Visitor import Visitor as FundamentalTypeInfoVisitor

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..Plugin import Plugin as PluginBase, ParseFlag
    from ..Schema import Attributes
    from ..Schema import Elements

# <parameters differ from overridden method> pylint: disable=W0221

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(PluginBase):
    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = Interface.DerivedProperty("XsdSchema")
    Description                             = Interface.DerivedProperty("Generates an XSD Schema file (XML Schema Definition)")
    Flags                                   = Interface.DerivedProperty(
        ParseFlag.SupportAttributes | ParseFlag.SupportIncludeStatements                                                                                                                                              # | ParseFlag.SupportConfigStatements
                                                                                                                                                                                                                      # | ParseFlag.SupportExtensionsStatements
                                                                                                                                                                                                                      # | ParseFlag.SupportUnnamedDeclarations
        # | ParseFlag.SupportUnnamedObjects
        | ParseFlag.SupportNamedDeclarations | ParseFlag.SupportNamedObjects | ParseFlag.SupportRootDeclarations | ParseFlag.SupportRootObjects | ParseFlag.SupportChildDeclarations | ParseFlag.SupportChildObjects  # | ParseFlag.SupportCustomElements
        | ParseFlag.SupportAnyElements | ParseFlag.SupportReferenceElements | ParseFlag.SupportListElements | ParseFlag.SupportSimpleObjectElements | ParseFlag.SupportVariantElements | ParseFlag.ResolveReferences,
    )

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.override
    def IsValidEnvironment():
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def GenerateCustomSettingsAndDefaults():
        yield "root_name", ""
        yield "allow_additional_children", False

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GenerateOutputFilenames(cls, context):
        return ["{}.xsd".format(context["output_name"])]

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def GetOptionalMetadataItems(cls, item):
        results = []

        if item.element_type == Elements.CompoundElement:
            results.append(
                Attributes.Attribute(
                    "allow_additional_children",
                    BoolTypeInfo(
                        arity="?",
                    ),
                    default_value=None,
                ),
            )

        return results + super(Plugin, cls).GetOptionalMetadataItems(item)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def Generate(
        cls,
        simple_schema_generator,
        invoke_reason,
        input_filenames,
        output_filenames,
        name,
        elements,
        include_indexes,
        status_stream,
        verbose_stream,
        verbose,
        root_name,
        allow_additional_children,
    ):
        assert len(output_filenames) == 1
        output_filename = output_filenames[0]
        del output_filenames

        include_map = cls._GenerateIncludeMap(elements, include_indexes)
        include_dotted_names = set(six.iterkeys(include_map))

        top_level_elements = [element for element in elements if element.Parent is None and not element.IsDefinitionOnly and element.DottedName in include_map]

        status_stream.write("Creating '{}'...".format(output_filename))
        with status_stream.DoneManager() as dm:
            with open(output_filename, "w") as f:
                f.write(
                    textwrap.dedent(
                        """\
                            <?xml version="1.0"?>
                            <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">

                            <!--
                            {}
                            -->
                        """,
                    ).format(
                        cls._GenerateFileHeader(
                            line_break="-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-",
                            filename_prefix="<SimpleSchemaGenerator>/",
                        ),
                    ),
                )

                # XML only always 1 root element. If there are multiple top-level elements
                # defined by the schema, unite them under a common parent.
                if len(top_level_elements) > 1:
                    f.write(
                        textwrap.dedent(
                            """\
                            <xsd:element name="{}">
                              <xsd:complexType>
                                <xsd:sequence>
                            """,
                        ).format(root_name or name),
                    )

                    element_stream = StreamDecorator(
                        f,
                        line_prefix="      ",
                    )

                    # ----------------------------------------------------------------------
                    def Cleanup():
                        f.write(
                            textwrap.dedent(
                                """\
                                    </xsd:sequence>
                                  </xsd:complexType>
                                </xsd:element>

                                """,
                            ),
                        )

                    # ----------------------------------------------------------------------

                else:
                    element_stream = f

                    # ----------------------------------------------------------------------
                    def Cleanup():
                        f.write("\n")

                    # ----------------------------------------------------------------------

                with CallOnExit(Cleanup):
                    for element in top_level_elements:
                        element_stream.write(
                            '<xsd:element name="{name}" type="_{type}" />\n'.format(
                                name=element.Name,
                                type=element.Resolve().DottedName,
                            ),
                        )

                fundamental_type_info_visitor = _FundamentalTypeInfoVisitor()

                # ----------------------------------------------------------------------
                def GetBaseTypeName(
                    element,
                    item_suffix=True,
                ):
                    name = getattr(element, "_xsd_base_type", None)
                    if name is None:
                        name = "_{}".format(element.DottedName)

                        if item_suffix:
                            name = "{}_Item".format(name)

                    return name

                # ----------------------------------------------------------------------
                class Visitor(Elements.ElementVisitor):
                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnFundamental(element):
                        content = fundamental_type_info_visitor.Accept(element.TypeInfo)

                        if content.startswith("<xsd:restriction"):
                            f.write(
                                textwrap.dedent(
                                    """\
                                    <xsd:simpleType name="_{}_Item">
                                      {}
                                    </xsd:simpleType>

                                    """,
                                ).format(element.DottedName, StringHelpers.LeftJustify(content, 2).strip()),
                            )
                        else:
                            element._xsd_base_type = content

                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnCompound(element):
                        # Process the element after all children have been processed
                        pass

                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnCompound_VisitedChildren(element):
                        attributes = []
                        elements = []

                        for child in cls._EnumerateChildren(
                            element,
                            include_definitions=False,
                        ):
                            if getattr(child, "IsAttribute", False):
                                attributes.append(
                                    textwrap.dedent(
                                        """\
                                        <xsd:attribute name="{name}" use="{use}" type="{type}"{default} />
                                        """,
                                    ).format(
                                        name=child.Name,
                                        use="optional" if child.TypeInfo.Arity.IsOptional else "required",
                                        type=GetBaseTypeName(child.Resolve()),
                                        default="" if not hasattr(child, "default") else ' default="{}"'.format(child.default),
                                    ),
                                )
                            else:
                                elements.append(
                                    textwrap.dedent(
                                        """\
                                        <xsd:element name="{name}" type="_{type}" minOccurs="{min}" maxOccurs="1"{default} />
                                        """,
                                    ).format(
                                        name=child.Name,
                                        type=child.DottedName,
                                        min="0" if child.TypeInfo.Arity.Min == 0 else "1",
                                        default="" if not hasattr(child, "default") else ' default="{}"'.format(child.default),
                                    ),
                                )

                        element_allow_additional_children = getattr(element, "allow_additional_children", None)
                        if element_allow_additional_children is None:
                            element_allow_additional_children = allow_additional_children

                        if element_allow_additional_children:
                            elements.append('<xsd:any minOccurs="0" maxOccurs="unbounded" processContents="skip" />\n')

                        content = textwrap.dedent(
                            """\
                            <xsd:sequence>
                              {elements}
                            </xsd:sequence>
                            {attributes}
                            """,
                        ).format(
                            elements=StringHelpers.LeftJustify("".join(elements), 2).strip(),
                            attributes="".join(attributes).strip(),
                        )

                        f.write(
                            textwrap.dedent(
                                """\
                                <xsd:complexType name="_{name}_Item"{mixed}>
                                  {content}
                                </xsd:complexType>

                                """,
                            ).format(
                                name=element.DottedName,
                                content=StringHelpers.LeftJustify(content, 2).strip(),
                                mixed=' mixed="true"' if element_allow_additional_children else "",
                            ),
                        )

                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnSimple(element):
                        # Process the element after all children have been processed
                        pass

                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnSimple_VisitedChildren(element):
                        content = fundamental_type_info_visitor.Accept(element.TypeInfo.Items[element.FundamentalAttributeName])

                        if content.startswith("<xsd:restriction"):
                            f.write(
                                textwrap.dedent(
                                    """\
                                    <xsd:simpleType name="_{}_Item_content">
                                      {}
                                    </xsd:simpleType>

                                    """,
                                ).format(element.DottedName, StringHelpers.LeftJustify(content.strip(), 2)),
                            )

                            content = "_{}_Item_content".format(element.DottedName)

                        f.write(
                            textwrap.dedent(
                                """\
                                <xsd:complexType name="_{name}_Item">
                                  <xsd:simpleContent>
                                    <xsd:extension base="{base}">
                                      {attributes}
                                    </xsd:extension>
                                  </xsd:simpleContent>
                                </xsd:complexType>

                                """,
                            ).format(
                                name=element.DottedName,
                                base=content,
                                attributes=StringHelpers.LeftJustify(
                                    "".join(
                                        [
                                            textwrap.dedent(
                                                """\
                                                <xsd:attribute name="{name}" use="{use}" type="{type}" />
                                                """,
                                            ).format(
                                                name=attribute.Name,
                                                use="optional" if attribute.TypeInfo.Arity.IsOptional else "required",
                                                type=GetBaseTypeName(attribute.Resolve()),
                                            ) for attribute in element.Attributes
                                        ],
                                    ),
                                    6,
                                ).rstrip(),
                            ),
                        )

                    # ----------------------------------------------------------------------
                    @classmethod
                    @Interface.override
                    def OnVariant(this_cls, element):
                        # Xsd makes it difficult to work with variants. We could
                        # use <xsd:alternative...>, but the test clause is problematic
                        # for the arbitrary types that can be expressed by the different
                        # Element types. Bail on the authentication of variants by
                        # allowing anything; this means that the variant will need to
                        # be validate by other means.
                        return this_cls.OnAny(element)

                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnReference(element):
                        # References don't need to be added, as they will be resolved inline.
                        pass

                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnList(element):
                        f.write(
                            textwrap.dedent(
                                """\
                                <xsd:complexType name="_{name}_Item">
                                  <xsd:complexContent>
                                    <xsd:extension base="_{type}" />
                                  </xsd:complexContent>
                                </xsd:complexType>

                                """,
                            ).format(
                                name=element.DottedName,
                                type=element.Reference.Resolve().DottedName,
                            ),
                        )

                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnAny(element):
                        f.write(
                            textwrap.dedent(
                                """\
                                <xsd:complexType name="_{}_Item" mixed="true">
                                  <xsd:sequence>
                                    <xsd:any minOccurs="0" processContents="skip" />
                                  </xsd:sequence>
                                </xsd:complexType>

                                """,
                            ).format(element.DottedName),
                        )

                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnCustom(element):
                        raise Exception("CustomElements are not supported")

                    # ----------------------------------------------------------------------
                    @staticmethod
                    @Interface.override
                    def OnExtension(element):
                        raise Exception("ExtensionElements are not supported")

                # ----------------------------------------------------------------------

                Visitor().Accept(
                    elements,
                    include_dotted_names=include_dotted_names,
                )

                # ----------------------------------------------------------------------
                def OnElement(element):
                    typ = GetBaseTypeName(element.Resolve())

                    if element.TypeInfo.Arity.Max == 1:
                        f.write(
                            textwrap.dedent(
                                """\
                                <xsd:complexType name="_{name}">
                                  <xsd:{type}Content>
                                    <xsd:extension base="{base}" />
                                  </xsd:{type}Content>
                                </xsd:complexType>

                                """,
                            ).format(
                                type="simple" if isinstance(element.Resolve(), Elements.FundamentalElement) else "complex",
                                name=element.DottedName,
                                base=typ,
                                min=element.TypeInfo.Arity.Min,
                                max=element.TypeInfo.Arity.Max,
                            ),
                        )
                        return

                    f.write(
                        textwrap.dedent(
                            """\
                            <xsd:complexType name="_{name}">
                              <xsd:sequence>
                                <xsd:element name="item" type="{type}" minOccurs="{min}" maxOccurs="{max}" />
                              </xsd:sequence>
                            </xsd:complexType>

                            """,
                        ).format(
                            name=element.DottedName,
                            type=typ,
                            min=element.TypeInfo.Arity.Min,
                            max=element.TypeInfo.Arity.Max or "unbounded",
                        ),
                    )

                # ----------------------------------------------------------------------

                Elements.CreateElementVisitor(OnElement).Accept(
                    elements,
                    include_dotted_names=include_dotted_names,
                )

                f.write(
                    textwrap.dedent(
                        """\
                        </xsd:schema>
                        """,
                    ),
                )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _ArityToString(arity):
        if arity.IsSingle:
            return ""

        return ' minOccurs="{}" maxOccurs="{}"'.format(arity.Min, arity.Max or "unbounded")


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@Interface.staticderived
class _FundamentalTypeInfoVisitor(FundamentalTypeInfoVisitor):
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnBool(type_info):
        return "xsd:boolean"

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnDateTime(type_info):
        return "xsd:dateTime"

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnDate(type_info):
        return "xsd:date"

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnDirectory(type_info):
        return textwrap.dedent(
            """\
            <xsd:restriction base="xsd:string">
              <xsd:minLength value="1" />
            </xsd:restriction>
            """,
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnDuration(type_info):
        return "xsd:duration"

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnEnum(type_info):
        return textwrap.dedent(
            """\
            <xsd:restriction base="xsd:string">
            {}
            </xsd:restriction>
            """,
        ).format("\n".join(['  <xsd:enumeration value="{}" />'.format(value) for value in type_info.Values]))

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnFilename(type_info):
        return textwrap.dedent(
            """\
            <xsd:restriction base="xsd:string">
              <xsd:minLength value="1" />
            </xsd:restriction>
            """,
        )

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnFloat(type_info):
        restrictions = OrderedDict()

        if type_info.Min is not None:
            restrictions["minInclusive"] = type_info.Min
        if type_info.Max is not None:
            restrictions["maxInclusive"] = type_info.Max

        if not restrictions:
            return "xsd:decimal"

        return textwrap.dedent(
            """\
            <xsd:restriction base="xsd:decimal">
            {}
            </xsd:restriction>
            """,
        ).format("\n".join(['  <xsd:{} value="{}" />'.format(k, v) for k, v in six.iteritems(restrictions)]))

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnGuid(type_info):
        return textwrap.dedent(
            """\
            <xsd:restriction base="xsd:string">
              <xsd:pattern value="{}" />
            </xsd:restriction>
            """,
        ).format(RegularExpression.PythonToJavaScript(RegularExpressionVisitor().Accept(type_info)[0]))

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnInt(type_info):
        typ = None
        restrictions = OrderedDict()

        if type_info.Bytes is None:
            typ = "integer"
        elif type_info.Bytes == 1:
            typ = "byte"
        elif type_info.Bytes == 2:
            typ = "short"
        elif type_info.Bytes == 4:
            typ = "int"
        elif type_info.Bytes == 8:
            typ = "long"
        else:
            assert False, type_info.Bytes

        if type_info.Min is not None:
            if type_info.Unsigned:
                typ = "nonNegative{}{}".format(typ[0].upper(), typ[1:])

            if type_info.Min != 0:
                restrictions["minInclusive"] = type_info.Min

        if type_info.Max is not None:
            if type_info.Max < 0:
                typ = "negative{}{}".format(typ[0].upper(), typ[1:])

            restrictions["maxInclusive"] = type_info.Max

        if not restrictions:
            return "xsd:{}".format(typ)

        return textwrap.dedent(
            """\
            <xsd:restriction base="xsd:{}">
            {}
            </xsd:restriction>
            """,
        ).format(typ, "\n".join(['  <xsd:{} value="{}" />'.format(k, v) for k, v in six.iteritems(restrictions)]))

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnString(type_info):
        restrictions = OrderedDict()

        if type_info.ValidationExpression is not None:
            restrictions["pattern"] = RegularExpression.PythonToJavaScript(type_info.ValidationExpression)
        else:
            if type_info.MinLength not in [None, 0]:
                restrictions["minLength"] = type_info.MinLength
            if type_info.MaxLength is not None:
                restrictions["maxLength"] = type_info.MaxLength

        if not restrictions:
            return "xsd:string"

        return textwrap.dedent(
            """\
            <xsd:restriction base="xsd:string">
            {}
            </xsd:restriction>
            """,
        ).format("\n".join(['  <xsd:{} value="{}" />'.format(k, v) for k, v in six.iteritems(restrictions)]))

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnTime(type_info):
        return "xsd:time"

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def OnUri(type_info):
        return textwrap.dedent(
            """\
            <xsd:restriction base="xsd:string">
              <xsd:pattern value="{}" />
            </xsd:restriction>
            """,
        ).format(RegularExpression.PythonToJavaScript(RegularExpressionVisitor().Accept(type_info)[0]).replace("?", ""))
