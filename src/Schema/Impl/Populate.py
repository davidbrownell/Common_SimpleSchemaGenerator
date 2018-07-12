# ----------------------------------------------------------------------
# |  
# |  Populate.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 13:19:21
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
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

from CommonEnvironment import Nonlocals
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment.TypeInfo import Arity

from CommonEnvironmentEx.Antlr4Helpers.ErrorListener import ErrorListener
from CommonEnvironmentEx.Package import ApplyRelativePackage

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, "..", "Grammar", "GeneratedCode"))
with CallOnExit(lambda: sys.path.pop(0)):
    from SimpleSchemaLexer import SimpleSchemaLexer                         # <Unable to import> pylint: disable = E0401
    from SimpleSchemaParser import SimpleSchemaParser                       # <Unable to import> pylint: disable = E0401
    from SimpleSchemaVisitor import SimpleSchemaVisitor                     # <Unable to import> pylint: disable = E0401

with ApplyRelativePackage():
    from .Item import Item
    from ..Exceptions import *
    from ...Plugin import ParseFlag

# ----------------------------------------------------------------------
def Populate( source_name_content_generators,           # { "name" : def Func() -> content, }
              parse_flags,
            ):
    include_filenames = []

    root = Item( declaration_type=Item.DeclarationType.Object,
                 item_type=Item.ItemType.Standard,
                 parent=None,
                 source="<root>",
                 line=-1,
                 column=-1,
                 is_external=False,
               )

    root.name = "<root>"
    root.declaration_type = -SimpleSchemaParser.RULE_obj
    root.config = OrderedDict()

    # ----------------------------------------------------------------------
    class Visitor(SimpleSchemaVisitor):
        # <PascalCase naming style> pylint: disable = C0103

        # ----------------------------------------------------------------------
        def __init__(self, source_name, is_external):
            self._source_name               = source_name
            self._is_external               = is_external

            self._stack                     = [ root, ]

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
        
            if ( (value.startswith('"""') and value.endswith('"""')) or
                 (value.startswith("'''") and value.endswith("'''"))
               ):
                initial_whitespace = token.column

                # ----------------------------------------------------------------------
                def TrimPrefix(line, line_offset):
                    index = 0
                    whitespace = 0

                    while index < len(line) and whitespace < initial_whitespace:
                        if line[index] == ' ':
                            whitespace += 1
                        elif line[index] == '\t':
                            whitespace += 4
                        elif line[index] == '\r':
                            break
                        else:
                            raise PopulateInvalidTripleStringPrefixException( self._source_name,
                                                                              token.line + line_offset,
                                                                              token.column + 1 + whitespace,
                                                                            )
                        index += 1

                    return line[index:]

                # ----------------------------------------------------------------------

                lines = value.split('\n')

                initial_line = lines[0].rstrip()
                if lines(initial_line) != 3:
                    raise PopulateInvalidTripleStringHeaderException( self._source_name,
                                                                      token.line,
                                                                      token.column + 1,
                                                                    )

                final_line = lines[-1]
                if len(TrimPrefix(final_line, len(lines))) != 3:
                    raise PopulateInvalidTripleStringFooterException( self._source_name,
                                                                      token.line,
                                                                      token.column + 1,
                                                                    )

                lines = [ TrimPrefix(line, index + 1) for index, line in enumerate(lines[1:-1]) ]

                value = '\n'.join(lines)

            elif value[0] == '"' and value[-1] == '"':
                value = value[1:-1].replace('\\"', '"')

            elif value[0] == "'" and value[-1] == "'":
                value = value[1:-1].replace("\\'", "'")

            else:
                assert False, value

            self._stack.append(value)

        # ----------------------------------------------------------------------
        def visitStringList(self, ctx):
            values = self._GetChildValues(ctx)
            self._stack.append(values)

        # ----------------------------------------------------------------------
        def visitArgList(self, ctx):
            values = self._GetChildValues(ctx)
            self._stack.append(values)

        # ----------------------------------------------------------------------
        def visitMetadata(self, ctx):
            values = self._GetChildValues(ctx)
            assert len(values) == 2, values
            
            name, value = values

            self._stack.append(( name,
                                 Item.MetadataValue( value,
                                                     Item.MetadataSource.Explicit,
                                                     self._source_name,
                                                     ctx.start.line,
                                                     ctx.start.column + 1,
                                                   ),
                               ))

        # ----------------------------------------------------------------------
        def visitMetadataList(self, ctx):
            values = self._GetChildValues(ctx)
            self._stack.append(Item.Metadata( OrderedDict(values),
                                              self._source_name,
                                              ctx.start.line,
                                              ctx.start.column + 1,
                                            ))

        # ----------------------------------------------------------------------
        def visitArityOptional(self, ctx):
            self._stack.append(Arity.FromString('?'))

        # ----------------------------------------------------------------------
        def visitArityZeroOrMore(self, ctx):
            self._stack.append(Arity.FromString('*'))

        # ----------------------------------------------------------------------
        def visitArityOneOrMore(self, ctx):
            self._stack.append(Arity.FromString('+'))

        # ----------------------------------------------------------------------
        def visitArityFixed(self, ctx):
            values = self._GetChildValues(ctx)
            assert len(values) == 1, values

            value = values[0]

            if value <= 0:
                raise PopulateInvalidArityException( self._source_name,
                                                     ctx.start.line,
                                                     ctx.start.column + 1,
                                                     value=value,
                                                   )

            self._stack.append(Arity(value, None))

        # ----------------------------------------------------------------------
        def visitArityVariable(self, ctx):
            values = self._GetChildValues(ctx)
            assert len(values) == 2, values

            min_value, max_value = values

            if min_value <= 0:
                raise PopulateInvalidArityException( self._source_name,
                                                     ctx.start.line,
                                                     ctx.start.column + 1,
                                                     value=min_value,
                                                   )

            if max_value <= 0:
                raise PopulateInvalidArityException( self._source_name,
                                                     ctx.start.line,
                                                     ctx.start.column + 1,
                                                     value=max_value,
                                                   )

            if max_value < min_value:
                raise PopulateInvalidMaxArityException( self._source_name,
                                                        ctx.start.line,
                                                        ctx.start.column + 1,
                                                        min=min_value,
                                                        max=max_value,
                                                      )

            self._stack.append(Arity(min_value, max_value))

        # ----------------------------------------------------------------------
        def visitIncludeStatement(self, ctx):
            if not parse_flags & ParseFlag.SupportIncludeStatements:
                raise PopulateUnsupportedIncludeStatementsException( self._source_name,
                                                                     ctx.start.line,
                                                                     ctx.start.column + 1,
                                                                   )

            values = self._GetChildValues(ctx)
            assert len(values) == 1, values
            filename = values[0]
            
            filename = os.path.normpath(os.path.join(os.path.dirname(self._source_name), filename))
            if not os.path.isfile(filename):
                raise PopulateInvalidIncludeFilenameException( self._source_name,
                                                               ctx.start.line,
                                                               ctx.start.column + 1,
                                                               name=filename,
                                                             )

            if ( filename not in source_name_content_generators and
                 filename not in include_filenames
               ):
                include_filenames.append(filename)

        # ----------------------------------------------------------------------
        def visitConfigStatement(self, ctx):
            if not parse_flags & ParseFlag.SupportConfigStatements:
                raise PopulateUnsupportedConfigStatementsException( self._source_name,
                                                                    ctx.start.line,
                                                                    ctx.start.column + 1,
                                                                  )
            values = self._GetChildValues(ctx)

            # There should be at least the name and 1 metadata item
            assert len(values) >= 2, len(values)

            name = values.pop(0)

            assert isinstance(values, list) and all(isinstance(v, Item.MetadataValue) for k, v in values)
            
            root.config.setdefault(name, []).append(Item.Metadata( OrderedDict(values),
                                                                   self._source_name,
                                                                   ctx.start.line,
                                                                   ctx.start.column + 1,
                                                                 ))

        # ----------------------------------------------------------------------
        def visitUnnamedObj(self, ctx):
            if not parse_flags & ParseFlag.SupportUnnamedObjects:
                raise PopulateUnsupportedUnnamedObjectsException( self._source_name,
                                                                  ctx.start.line,
                                                                  ctx.start.column + 1,
                                                                )

            if len(self._stack) == 1:
                if not parse_flags & ParseFlag.SupportRootObjects:
                    raise PopulateUnsupportedRootObjectsException( self._source_name,
                                                                   ctx.start.line,
                                                                   ctx.start.column + 1,
                                                                 )
            else:
                if not parse_flags & ParseFlag.SupportChildObjects:
                    raise PopulateUnsupportedChildObjectsException( self._source_name,
                                                                    ctx.start.line,
                                                                    ctx.start.column + 1,
                                                                  )

            with self._PushNewStackItem(ctx, Item.DeclarationType.Object) as item:
                values = self._GetChildValues(ctx)
                assert not values, values

        # ----------------------------------------------------------------------
        def visitObj(self, ctx):
            if not parse_flags & ParseFlag.SupportNamedObjects:
                raise PopulateUnsupportedNamedObjectsException( self._source_name,
                                                                ctx.start.line,
                                                                ctx.start.column + 1,
                                                              )

            if len(self._stack) == 1:
                if not parse_flags & ParseFlag.SupportRootObjects:
                    raise PopulateUnsupportedRootObjectsException( self._source_name,
                                                                   ctx.start.line,
                                                                   ctx.start.column + 1,
                                                                 )
            else:
                if not parse_flags & ParseFlag.SupportChildObjects:
                    raise PopulateUnsupportedChildObjectsException( self._source_name,
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

                item.name = name
                item.reference = reference

        # ----------------------------------------------------------------------
        def visitObjAttributes(self, ctx):
            values = self._GetChildValues(ctx)
            if not values:
                return

            if len(values) == 1:
                metadata = None
                arity = None

                if self._IsMetadata(values[0]):
                    metadata = values[0]
                elif self._IsArity(values[0]):
                    arity = values[0]
                else:
                    assert False, values[0]

            elif len(values) == 2:
                metadata, arity = values

                assert self._IsMetadata(metadata), metadata
                assert self._IsArity(arity), arity

            else:
                assert False, values

            item = self._GetStackParent()
            
            item.metadata = metadata
            item.arity = arity

        # ----------------------------------------------------------------------
        def visitUnnamedDeclaration(self, ctx):
            if not parse_flags & ParseFlag.SupportUnnamedDeclarations:
                raise PopulateUnsupportedUnnamedDeclarationsException( self._source_name,
                                                                       ctx.start.line,
                                                                       ctx.start.column + 1,
                                                                     )

            if len(self._stack) == 1:
                if not parse_flags & ParseFlag.SupportRootDeclarations:
                    raise PopulateUnsupportedRootDeclarationsException( self._source_name,
                                                                        ctx.start.line,
                                                                        ctx.start.column + 1,
                                                                      )
            else:
                if not parse_flags & ParseFlag.SupportChildDeclarations:
                    raise PopulateUnsupportedChildDeclarationsException( self._source_name,
                                                                         ctx.start.line,
                                                                         ctx.start.column + 1,
                                                                       )

            with self._PushNewStackItem(ctx, Item.DeclarationType.Declaration) as item:
                values = self._GetChildValues(ctx)
                assert not values, values

        # ----------------------------------------------------------------------
        def visitDeclaration(self, ctx):
            if not parse_flags & ParseFlag.SupportNamedDeclarations:
                raise PopulateUnsupportedNamedDeclarationsException( self._source_name,
                                                                     ctx.start.line,
                                                                     ctx.start.column + 1,
                                                                   )

            if len(self._stack) == 1:
                if not parse_flags & ParseFlag.SupportRootDeclarations:
                    raise PopulateUnsupportedRootDeclarationsException( self._source_name,
                                                                        ctx.start.line,
                                                                        ctx.start.column + 1,
                                                                      )
            else:
                if not parse_flags & ParseFlag.SupportChildDeclarations:
                    raise PopulateUnsupportedChildDeclarationsException( self._source_name,
                                                                         ctx.start.line,
                                                                         ctx.start.column + 1,
                                                                       )

            with self._PushNewStackItem(ctx, Item.DeclarationType.Declaration) as item:
                values = self._GetChildValues(ctx)
                
                assert len(values) == 1, values
                name = values[0]

                item.name = name

        # ----------------------------------------------------------------------
        def visitDeclarationAttributes(self, ctx):
            values = self._GetChildValues(ctx)
            assert values

            item = self._GetStackParent()

            # First item will always be the id or attributes list
            item.reference = values.pop(0)
            
            if not values:
                return

            if len(values) == 1:
                metadata = None
                arity = None

                if self._IsMetadata(values[0]):
                    metadata = values[0]
                elif self._IsArity(values[0]):
                    arity = values[0]
                else:
                    assert False, values[0]

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
                result.append(( values[index], values[index + 1] ))
                index += 2

            self._stack.append(result)

        # ----------------------------------------------------------------------
        # BugBug: Process extensions

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

            item = Item( declaration_type,
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
            return isinstance(value, Item.Metadata)

        # ----------------------------------------------------------------------
        @staticmethod
        def _IsArity(value):
            return isinstance(value, Arity)

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

        Impl( source_name,
              antlr_stream,
              is_external=False,
            )

    # Iterating via index rather than by element as processing the content may update
    # the list.
    index = 0

    while index < len(include_filenames):
        Impl( include_filenames[0],
              antlr4.FileStream(include_filenames[index]),
              is_external=True,
            )

        index += 1

    return root
