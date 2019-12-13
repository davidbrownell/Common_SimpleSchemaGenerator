grammar SimpleSchema;

tokens { INDENT, DEDENT }

@lexer::members {

multiline_statement_ctr = 0

def nextToken(self):
    if not hasattr(self, "_denter"):
        from CommonEnvironmentEx.Antlr4Helpers.DenterHelper import DenterHelper
        from SimpleSchemaParser import SimpleSchemaParser

        self._denter = DenterHelper( super(SimpleSchemaLexer, self).nextToken,
                                     SimpleSchemaParser.NEWLINE,
                                     SimpleSchemaParser.INDENT,
                                     SimpleSchemaParser.DEDENT,
                                   )

    return self._denter.nextToken()

}

// ---------------------------------------------------------------------------
// |
// |  Lexer Rules
// |
// ---------------------------------------------------------------------------
MULTI_LINE_NEWLINE:                         '\r'? '\n' { SimpleSchemaLexer.multiline_statement_ctr != 0 }? -> skip;
NEWLINE:                                    '\r'? '\n' [ \t]* { SimpleSchemaLexer.multiline_statement_ctr == 0 }?;
MULTI_LINE_ESCAPE:                          '\\' '\r'? '\n' -> skip;
HORIZONTAL_WHITESPACE:                      [ \t]+ -> skip;

LPAREN:                                     '(' { SimpleSchemaLexer.multiline_statement_ctr += 1 };
RPAREN:                                     ')' { SimpleSchemaLexer.multiline_statement_ctr -= 1 };
LBRACK:                                     '[' { SimpleSchemaLexer.multiline_statement_ctr += 1 };
RBRACK:                                     ']' { SimpleSchemaLexer.multiline_statement_ctr -= 1 };
LT:                                         '<' { SimpleSchemaLexer.multiline_statement_ctr += 1 };
GT:                                         '>' { SimpleSchemaLexer.multiline_statement_ctr -= 1 };
LBRACE:                                     '{';
RBRACE:                                     '}';

MULTI_LINE_COMMENT:                         '#/' .*? '/#' -> skip;
COMMENT:                                    '#' ~[\r\n]* -> skip;

PASS:                                       'pass';
INCLUDE:                                    'simple_schema_include';
CONFIG:                                     'simple_schema_config';

SCOPE_DELIMITER:                            ':';
ASSIGNMENT:                                 '=';
COMMA:                                      ',';
PIPE:                                       '|';

INT:                                        '-'? [0-9]+;
NUMBER:                                     '-'? [0-9]* '.' [0-9]+;
ID:                                         [a-zA-Z_][a-zA-Z_0-9\-.]*;

ARITY_OPTIONAL:                             '?';
ARITY_ZERO_OR_MORE:                         '*';
ARITY_ONE_OR_MORE:                          '+';

fragment HWS:                               [ \t];

DOUBLE_QUOTE_STRING:                        '"' (('\\"' | '\\\\') | .)*? '"';
SINGLE_QUOTE_STRING:                        '\'' (('\\\'' | '\\\\') | .)*? '\'';

TRIPLE_DOUBLE_QUOTE_STRING:                 '"""' .*? '"""';
TRIPLE_SINGLE_QUOTE_STRING:                 '\'\'\'' .*? '\'\'\'';

// ---------------------------------------------------------------------------
// |
// |  Parser Rules
// |    Note that anything with a '__' suffix represents a non-binding rule
// |    (it does not have any code associated with it and is here for organizational purposes)
// |
// ---------------------------------------------------------------------------
idRule:                                     ID;
intRule:                                    INT;
number:                                     NUMBER;

string:                                     DOUBLE_QUOTE_STRING | SINGLE_QUOTE_STRING;
enhancedString:                             string | TRIPLE_DOUBLE_QUOTE_STRING | TRIPLE_SINGLE_QUOTE_STRING;

arg__:                                      idRule | intRule | number | enhancedString | argList;
argList:                                    LBRACK arg__ (COMMA arg__)* COMMA? RBRACK;

metadata:                                   idRule ASSIGNMENT arg__;
metadataList:                               metadata*;

arity__:                                    arityOptional | arityZeroOrMore | arityOneOrMore | arityFixed | arityVariable;
arityOptional:                              ARITY_OPTIONAL;
arityZeroOrMore:                            ARITY_ZERO_OR_MORE;
arityOneOrMore:                             ARITY_ONE_OR_MORE;
arityFixed:                                 LBRACE intRule RBRACE;
arityVariable:                              LBRACE intRule COMMA intRule RBRACE;

// Entry point, not decorated
statements:                                 headerStatement__* standardStatement__* NEWLINE* EOF;

headerStatement__:                          (includeStatement | configStatement) NEWLINE+;
standardStatement__:                        ( obj | unnamedObj | declaration | unnamedDeclaration | extension) NEWLINE+;

includeStatement:                           INCLUDE LPAREN string RPAREN;

configStatement:                            CONFIG LPAREN string RPAREN SCOPE_DELIMITER configStatementContent__;
configStatementContent__:                   ( PASS |
                                              NEWLINE INDENT ( PASS NEWLINE+ |
                                                               (metadata NEWLINE+)+
                                                             ) DEDENT
                                            );

obj:                                        ( LPAREN idRule objAttributes RPAREN |
                                              LT idRule objAttributes GT
                                            ) SCOPE_DELIMITER objContent__;

unnamedObj:                                 ( LPAREN objAttributes RPAREN |
                                              LT objAttributes GT
                                            ) SCOPE_DELIMITER objContent__;

objAttributes:                              ( idRule | objAttributesItems )? metadataList arity__?;
objAttributesItems:                         LPAREN idRule (COMMA idRule)* RPAREN;

objContent__:                               ( PASS |
                                              NEWLINE+ INDENT ( PASS NEWLINE+ |
                                                                standardStatement__+
                                                              ) DEDENT
                                            );

declaration:                                ( LPAREN idRule declarationAttributes RPAREN |
                                              LT idRule declarationAttributes GT |
                                              LBRACK idRule declarationAttributes RBRACK
                                            );

unnamedDeclaration:                         ( LPAREN declarationAttributes RPAREN |
                                              LT declarationAttributes GT |
                                              LBRACK declarationAttributes RBRACK

                                            );

declarationAttributes:                      ( idRule | declarationAttributesItems ) metadataList arity__?;
declarationAttributesItems:                 LPAREN declarationAttributesItem__ (PIPE declarationAttributesItem__)* RPAREN;
declarationAttributesItem__:                idRule metadataList;

extension:                                  idRule LPAREN extensionContent__? RPAREN arity__?;
extensionContent__:                         extensionContentStandard__ | extensionContentKeywords__;
extensionContentStandard__:                 extensionContentPositional (COMMA extensionContentPositional)* ( COMMA |
                                                                                                             COMMA extensionContentKeywords__
                                                                                                           )?;
extensionContentPositional:                 arg__;
extensionContentKeywords__:                 extensionContentKeyword (COMMA extensionContentKeyword)* COMMA?;
extensionContentKeyword:                    idRule ASSIGNMENT arg__;
