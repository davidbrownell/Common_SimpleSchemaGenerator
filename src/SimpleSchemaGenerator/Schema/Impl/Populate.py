# ----------------------------------------------------------------------
# |
# |  Populate.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 13:19:21
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Uses ANTLR-generated functionality to populate items"""

import os
import sys

from collections import OrderedDict
from contextlib import contextmanager

import antlr4
import six

import CommonEnvironment
from CommonEnvironment import Nonlocals
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.TypeInfo import Arity

from CommonEnvironmentEx.Antlr4Helpers.ErrorListener import ErrorListener
from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "..", "Grammar", "GeneratedCode"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SimpleSchemaLexer import SimpleSchemaLexer                         # <Unable to import> pylint: disable = E0401
    from SimpleSchemaParser import SimpleSchemaParser                       # <Unable to import> pylint: disable = E0401
    from SimpleSchemaVisitor import SimpleSchemaVisitor                     # <Unable to import> pylint: disable = E0401

with InitRelativeImports():
    from .Item import Item, Metadata, MetadataValue, MetadataSource, ResolvedMetadata

    from ..Attributes import FUNDAMENTAL_ATTRIBUTE_INFO_MAP
    from .. import Exceptions

    from ...Plugin import ParseFlag

# ----------------------------------------------------------------------
def Populate(source_name_content_generators, parse_flags):                  # { "name" : def Func() -> content, }
    include_filenames = []

    root = Item(
        declaration_type=Item.DeclarationType.Object,
        item_type=Item.ItemType.Standard,
        parent=None,
        source="<root>",
        line=-1,
        column=-1,
        is_external=False,
    )

    root.name = "<root>"
    root.declaration_type = None
    root.metadata = ResolvedMetadata({}, [], [])

    root.config = OrderedDict()

    # ----------------------------------------------------------------------
    class Visitor(SimpleSchemaVisitor):
        # <PascalCase naming style> pylint: disable = C0103

        # ----------------------------------------------------------------------
        def __init__(self, source_name, is_external):
            self._source_name               = source_name
            self._is_external               = is_external

            self._stack                     = [root]

        # ----------------------------------------------------------------------
        def visitIdRule(self, ctx):
            assert len(ctx.children) == 1, ctx.children
            self._stack.append(ctx.children[0].symbol.text)

        # ----------------------------------------------------------------------
        def visitIntRule(self, ctx):
            assert len(ctx.children) == 1, ctx.children
            self._stack.append(int(ctx.children[0].symbol.text))

        # ----------------------------------------------------------------------
        def visitNumber(self, ctx):
            assert len(ctx.children) == 1, ctx.children
            self._stack.append(float(ctx.children[0].symbol.text))

        # ----------------------------------------------------------------------
        def visitString(self, ctx):
            return self.visitEnhancedString(ctx)

        # ----------------------------------------------------------------------
        def visitEnhancedString(self, ctx):
            while not isinstance(ctx, antlr4.tree.Tree.TerminalNode):
                assert len(ctx.children) == 1
                ctx = ctx.children[0]

            token = ctx.symbol
            value = token.text

            # At the very least, we should have a beginning and ending quote
            assert len(value) >= 2, value

            if (value.startswith('"""') and value.endswith('"""')) or (
                value.startswith("'''") and value.endswith("'''")
            ):
                initial_whitespace = token.column

                # ----------------------------------------------------------------------
                def TrimPrefix(line, line_offset):
                    index = 0
                    whitespace = 0

                    while index < len(line) and whitespace < initial_whitespace:
                        if line[index] == " ":
                            whitespace += 1
                        elif line[index] == "\t":
                            whitespace += 4
                        elif line[index] == "\r":
                            break
                        else:
                            raise Exceptions.PopulateInvalidTripleStringPrefixException(
                                self._source_name,
                                token.line + line_offset,
                                token.column + 1 + whitespace,
                            )
                        index += 1

                    return line[index:]

                # ----------------------------------------------------------------------

                lines = value.split("\n")

                initial_line = lines[0].rstrip()
                if len(initial_line) != 3:
                    raise Exceptions.PopulateInvalidTripleStringHeaderException(
                        self._source_name,
                        token.line,
                        token.column + 1,
                    )

                final_line = lines[-1]
                if len(TrimPrefix(final_line, len(lines))) != 3:
                    raise Exceptions.PopulateInvalidTripleStringFooterException(
                        self._source_name,
                        token.line,
                        token.column + 1,
                    )

                lines = [TrimPrefix(line, index + 1) for index, line in enumerate(lines[1:-1])]

                value = "\n".join(lines)

            elif value[0] == '"' and value[-1] == '"':
                value = value[1:-1].replace('\\"', '"')

            elif value[0] == "'" and value[-1] == "'":
                value = value[1:-1].replace("\\'", "'")

            else:
                assert False, value

            self._stack.append(value)

        # ----------------------------------------------------------------------
        def visitArgList(self, ctx):
            values = self._GetChildValues(ctx)
            self._stack.append(values)

        # ----------------------------------------------------------------------
        def visitMetadata(self, ctx):
            values = self._GetChildValues(ctx)
            assert len(values) == 2, values

            name, value = values

            self._stack.append(
                (
                    name,
                    MetadataValue(
                        value,
                        MetadataSource.Explicit,
                        self._source_name,
                        ctx.start.line,
                        ctx.start.column + 1,
                    ),
                ),
            )

        # ----------------------------------------------------------------------
        def visitMetadataList(self, ctx):
            values = self._GetChildValues(ctx)

            metadata = OrderedDict()

            for name, value in values:
                if name in metadata:
                    raise Exceptions.PopulateDuplicateMetadataException(
                        value.Source,
                        value.Line,
                        value.Column,
                        name=name,
                        original_source=metadata[name].Source,
                        original_line=metadata[name].Line,
                        original_column=metadata[name].Column,
                    )

                metadata[name] = value

            self._stack.append(
                Metadata(metadata, self._source_name, ctx.start.line, ctx.start.column + 1),
            )

        # ----------------------------------------------------------------------
        def visitArityOptional(self, ctx):
            self._stack.append(Arity.FromString("?"))

        # ----------------------------------------------------------------------
        def visitArityZeroOrMore(self, ctx):
            self._stack.append(Arity.FromString("*"))

        # ----------------------------------------------------------------------
        def visitArityOneOrMore(self, ctx):
            self._stack.append(Arity.FromString("+"))

        # ----------------------------------------------------------------------
        def visitArityFixed(self, ctx):
            values = self._GetChildValues(ctx)
            assert len(values) == 1, values

            value = values[0]

            if value <= 0:
                raise Exceptions.PopulateInvalidArityException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                    value=value,
                )

            self._stack.append(Arity(value, value))

        # ----------------------------------------------------------------------
        def visitArityVariable(self, ctx):
            values = self._GetChildValues(ctx)
            assert len(values) == 2, values

            min_value, max_value = values

            if min_value <= 0:
                raise Exceptions.PopulateInvalidArityException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                    value=min_value,
                )

            if max_value <= 0:
                raise Exceptions.PopulateInvalidArityException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                    value=max_value,
                )

            if max_value < min_value:
                raise Exceptions.PopulateInvalidMaxArityException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                    min=min_value,
                    max=max_value,
                )

            self._stack.append(Arity(min_value, max_value))

        # ----------------------------------------------------------------------
        def visitIncludeStatement(self, ctx):
            if not parse_flags & ParseFlag.SupportIncludeStatements:
                raise Exceptions.PopulateUnsupportedIncludeStatementsException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                )

            values = self._GetChildValues(ctx)
            assert len(values) == 1, values
            filename = values[0]

            filename = os.path.normpath(os.path.join(os.path.dirname(self._source_name), filename))
            if not os.path.isfile(filename):
                raise Exceptions.PopulateInvalidIncludeFilenameException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                    name=filename,
                )

            if filename not in source_name_content_generators and filename not in include_filenames:
                include_filenames.append(filename)

        # ----------------------------------------------------------------------
        def visitConfigStatement(self, ctx):
            if not parse_flags & ParseFlag.SupportConfigStatements:
                raise Exceptions.PopulateUnsupportedConfigStatementsException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                )
            values = self._GetChildValues(ctx)

            # There should be at least the name and 1 metadata item
            assert len(values) >= 2, len(values)

            name = values.pop(0)

            root.config.setdefault(name, []).append(
                Metadata(
                    OrderedDict(
                        [
                            (
                                k,
                                v._replace(
                                    Source=MetadataSource.Config,
                                ),
                            ) for k,
                            v in values
                        ],
                    ),
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                ),
            )

        # ----------------------------------------------------------------------
        def visitUnnamedObj(self, ctx):
            if not parse_flags & ParseFlag.SupportUnnamedObjects:
                raise Exceptions.PopulateUnsupportedUnnamedObjectsException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                )

            if len(self._stack) == 1:
                if not parse_flags & ParseFlag.SupportRootObjects:
                    raise Exceptions.PopulateUnsupportedRootObjectsException(
                        self._source_name,
                        ctx.start.line,
                        ctx.start.column + 1,
                    )
            else:
                if not parse_flags & ParseFlag.SupportChildObjects:
                    raise Exceptions.PopulateUnsupportedChildObjectsException(
                        self._source_name,
                        ctx.start.line,
                        ctx.start.column + 1,
                    )

            with self._PushNewStackItem(ctx, Item.DeclarationType.Object):
                values = self._GetChildValues(ctx)
                assert not values, values

        # ----------------------------------------------------------------------
        def visitObj(self, ctx):
            if not parse_flags & ParseFlag.SupportNamedObjects:
                raise Exceptions.PopulateUnsupportedNamedObjectsException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                )

            if len(self._stack) == 1:
                if not parse_flags & ParseFlag.SupportRootObjects:
                    raise Exceptions.PopulateUnsupportedRootObjectsException(
                        self._source_name,
                        ctx.start.line,
                        ctx.start.column + 1,
                    )
            else:
                if not parse_flags & ParseFlag.SupportChildObjects:
                    raise Exceptions.PopulateUnsupportedChildObjectsException(
                        self._source_name,
                        ctx.start.line,
                        ctx.start.column + 1,
                    )

            with self._PushNewStackItem(ctx, Item.DeclarationType.Object) as item:
                values = self._GetChildValues(ctx)

                # ( ID ID? ... )
                # < ID ID? ... >
                # [ ID ID? ... ]
                if len(values) == 2:
                    name, reference = values
                elif len(values) == 1:
                    name = values[0]
                    reference = None
                else:
                    assert False, values

                self._ValidateName(item, name)

                item.name = name
                item.BugBug_reference = reference

        # ----------------------------------------------------------------------
        def visitObjAttributes(self, ctx):
            values = self._GetChildValues(ctx)
            assert values, "Metadata is always present"

            if len(values) == 2:
                metadata, arity = values

                assert self._IsMetadata(metadata), metadata
                assert self._IsArity(arity), arity

            elif len(values) == 1:
                metadata = values[0]
                assert self._IsMetadata(values[0]), values[0]

                arity = None

            else:
                assert False, values

            parent = self._GetStackParent()

            parent.metadata = metadata
            parent.arity = arity

        # ----------------------------------------------------------------------
        def visitUnnamedDeclaration(self, ctx):
            if not parse_flags & ParseFlag.SupportUnnamedDeclarations:
                raise Exceptions.PopulateUnsupportedUnnamedDeclarationsException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                )

            if len(self._stack) == 1:
                if not parse_flags & ParseFlag.SupportRootDeclarations:
                    raise Exceptions.PopulateUnsupportedRootDeclarationsException(
                        self._source_name,
                        ctx.start.line,
                        ctx.start.column + 1,
                    )
            else:
                if not parse_flags & ParseFlag.SupportChildDeclarations:
                    raise Exceptions.PopulateUnsupportedChildDeclarationsException(
                        self._source_name,
                        ctx.start.line,
                        ctx.start.column + 1,
                    )

            with self._PushNewStackItem(ctx, Item.DeclarationType.Declaration):
                values = self._GetChildValues(ctx)
                assert not values, values

        # ----------------------------------------------------------------------
        def visitDeclaration(self, ctx):
            if not parse_flags & ParseFlag.SupportNamedDeclarations:
                raise Exceptions.PopulateUnsupportedNamedDeclarationsException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                )

            if len(self._stack) == 1:
                if not parse_flags & ParseFlag.SupportRootDeclarations:
                    raise Exceptions.PopulateUnsupportedRootDeclarationsException(
                        self._source_name,
                        ctx.start.line,
                        ctx.start.column + 1,
                    )
            else:
                if not parse_flags & ParseFlag.SupportChildDeclarations:
                    raise Exceptions.PopulateUnsupportedChildDeclarationsException(
                        self._source_name,
                        ctx.start.line,
                        ctx.start.column + 1,
                    )

            with self._PushNewStackItem(ctx, Item.DeclarationType.Declaration) as item:
                values = self._GetChildValues(ctx)

                assert len(values) == 1, values
                name = values[0]

                self._ValidateName(item, name)

                item.name = name

        # ----------------------------------------------------------------------
        def visitDeclarationAttributes(self, ctx):
            values = self._GetChildValues(ctx)
            assert values

            item = self._GetStackParent()

            # First item will always be the id or attributes list
            item.BugBug_reference = values.pop(0)

            assert values, "Metadata is always present"

            if len(values) == 1:
                metadata = values[0]
                assert self._IsMetadata(metadata), metadata

                arity = None

            elif len(values) == 2:
                metadata, arity = values

                assert self._IsMetadata(metadata), metadata
                assert self._IsArity(arity), arity

            else:
                assert False

            item.metadata = metadata
            item.arity = arity

        # ----------------------------------------------------------------------
        def visitDeclarationAttributesItems(self, ctx):
            values = self._GetChildValues(ctx)

            # Values should be alternating id, metadata list (an even number of items)
            assert not len(values) & 1, values

            result = []

            index = 0
            while index < len(values):
                result.append((values[index], values[index + 1]))
                index += 2

            self._stack.append(result)

        # ----------------------------------------------------------------------
        def visitExtension(self, ctx):
            if not parse_flags & ParseFlag.SupportExtensionsStatements:
                raise Exceptions.PopulateUnsupportedExtensionStatementException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                )

            with self._PushNewStackItem(ctx, Item.DeclarationType.Extension) as item:
                values = self._GetChildValues(ctx)
                assert len(values) in [1, 2], values

                name = values[0]
                self._ValidateName(item, name)

                item.name = name
                item.metadata = ResolvedMetadata({}, [], [])

                if len(values) > 1:
                    item.arity = values[1]

        # ----------------------------------------------------------------------
        def visitExtensionContentPositional(self, ctx):
            values = self._GetChildValues(ctx)
            assert len(values) == 1, values

            item = self._GetStackParent()

            item.positional_arguments.append(values[0])

        # ----------------------------------------------------------------------
        def visitExtensionContentKeyword(self, ctx):
            values = self._GetChildValues(ctx)

            assert len(values) == 2, values
            key, value = values

            item = self._GetStackParent()

            if key in item.keyword_arguments:
                raise Exceptions.PopulateDuplicateKeywordArgumentException(
                    self._source_name,
                    ctx.start.line,
                    ctx.start.column + 1,
                    name=key,
                    value=value,
                    original_value=item.keyword_arguments[key],
                )

            item.keyword_arguments[key] = value

        # ----------------------------------------------------------------------
        # ----------------------------------------------------------------------
        # ----------------------------------------------------------------------
        def _GetChildValues(self, ctx):
            num_elements = len(self._stack)

            self.visitChildren(ctx)

            result = self._stack[num_elements:]
            self._stack = self._stack[:num_elements]

            return result

        # ----------------------------------------------------------------------
        @contextmanager
        def _PushNewStackItem(self, ctx, declaration_type):
            if ctx.start.type == ctx.parser.LBRACK:
                item_type = Item.ItemType.Attribute
            elif ctx.start.type == ctx.parser.LPAREN:
                item_type = Item.ItemType.Definition
            else:
                item_type = Item.ItemType.Standard

            parent = self._GetStackParent()

            item = Item(
                declaration_type,
                item_type,
                parent,
                self._source_name,
                ctx.start.line,
                ctx.start.column + 1,
                is_external=self._is_external,
            )

            parent.items.append(item)

            self._stack.append(item)

            # Note that the lambda seems to be necessary;
            #
            #   with CallOnExit(self._stack.pop):
            #       ...
            #
            # didn't modify the _stack. Strange.
            with CallOnExit(lambda: self._stack.pop()):
                yield item

        # ----------------------------------------------------------------------
        def _GetStackParent(self):
            """\
            Return the parent item. The parent item won't always be the last item on the stack,
            as we may have pushed ids that have yet to be consumed.
            """

            index = -1

            while True:
                assert -index <= len(self._stack), (-index, len(self._stack))

                item = self._stack[index]

                if isinstance(item, Item):
                    return item

                index -= 1

        # ----------------------------------------------------------------------
        @staticmethod
        def _IsMetadata(value):
            return isinstance(value, Metadata)

        # ----------------------------------------------------------------------
        @staticmethod
        def _IsArity(value):
            return isinstance(value, Arity)

        # ----------------------------------------------------------------------
        @staticmethod
        def _ValidateName(item, name):
            # Validating name here rather than in Validate.py as the name is used
            # during Resolution (in Resolve.py), which happens before Validate is
            # called.
            if name in FUNDAMENTAL_ATTRIBUTE_INFO_MAP or name in ["any", "custom"]:
                raise Exceptions.PopulateReservedNameException(
                    item.Source,
                    item.Line,
                    item.Column,
                    name=name,
                )

    # ----------------------------------------------------------------------
    def Impl(name, antlr_stream, is_external):
        lexer = SimpleSchemaLexer(antlr_stream)
        tokens = antlr4.CommonTokenStream(lexer)

        tokens.fill()

        parser = SimpleSchemaParser(tokens)
        parser.addErrorListener(ErrorListener(name))

        ast = parser.statements()
        assert ast

        ast.accept(Visitor(name, is_external))

    # ----------------------------------------------------------------------

    for source_name, content_generator in six.iteritems(source_name_content_generators):
        content = content_generator()
        content += "\n"

        antlr_stream = antlr4.InputStream(content)
        antlr_stream.filename = source_name

        Impl(
            source_name,
            antlr_stream,
            is_external=False,
        )

    # Iterating via index rather than by element as processing the content may update
    # the list.
    index = 0

    while index < len(include_filenames):
        Impl(
            include_filenames[0],
            antlr4.FileStream(include_filenames[index]),
            is_external=True,
        )

        index += 1

    return root
