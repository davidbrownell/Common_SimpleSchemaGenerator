# Generated from C:\Code\v3\Common\SimpleSchemaGenerator\src\Schema\Grammar\BuildEnvironment\..\SimpleSchema.g4 by ANTLR 4.7.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .SimpleSchemaParser import SimpleSchemaParser
else:
    from SimpleSchemaParser import SimpleSchemaParser

# This class defines a complete generic visitor for a parse tree produced by SimpleSchemaParser.

class SimpleSchemaVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SimpleSchemaParser#idRule.
    def visitIdRule(self, ctx:SimpleSchemaParser.IdRuleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#intRule.
    def visitIntRule(self, ctx:SimpleSchemaParser.IntRuleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#number.
    def visitNumber(self, ctx:SimpleSchemaParser.NumberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#string.
    def visitString(self, ctx:SimpleSchemaParser.StringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#enhancedString.
    def visitEnhancedString(self, ctx:SimpleSchemaParser.EnhancedStringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arg__.
    def visitArg__(self, ctx:SimpleSchemaParser.Arg__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#argList.
    def visitArgList(self, ctx:SimpleSchemaParser.ArgListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#metadata.
    def visitMetadata(self, ctx:SimpleSchemaParser.MetadataContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#metadataList.
    def visitMetadataList(self, ctx:SimpleSchemaParser.MetadataListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arity__.
    def visitArity__(self, ctx:SimpleSchemaParser.Arity__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arityOptional.
    def visitArityOptional(self, ctx:SimpleSchemaParser.ArityOptionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arityZeroOrMore.
    def visitArityZeroOrMore(self, ctx:SimpleSchemaParser.ArityZeroOrMoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arityOneOrMore.
    def visitArityOneOrMore(self, ctx:SimpleSchemaParser.ArityOneOrMoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arityFixed.
    def visitArityFixed(self, ctx:SimpleSchemaParser.ArityFixedContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#arityVariable.
    def visitArityVariable(self, ctx:SimpleSchemaParser.ArityVariableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#statements.
    def visitStatements(self, ctx:SimpleSchemaParser.StatementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#headerStatement__.
    def visitHeaderStatement__(self, ctx:SimpleSchemaParser.HeaderStatement__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#standardStatement__.
    def visitStandardStatement__(self, ctx:SimpleSchemaParser.StandardStatement__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#includeStatement.
    def visitIncludeStatement(self, ctx:SimpleSchemaParser.IncludeStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#configStatement.
    def visitConfigStatement(self, ctx:SimpleSchemaParser.ConfigStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#configStatementContent__.
    def visitConfigStatementContent__(self, ctx:SimpleSchemaParser.ConfigStatementContent__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#unnamedObj.
    def visitUnnamedObj(self, ctx:SimpleSchemaParser.UnnamedObjContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#obj.
    def visitObj(self, ctx:SimpleSchemaParser.ObjContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#objAttributes.
    def visitObjAttributes(self, ctx:SimpleSchemaParser.ObjAttributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#objContent__.
    def visitObjContent__(self, ctx:SimpleSchemaParser.ObjContent__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#unnamedDeclaration.
    def visitUnnamedDeclaration(self, ctx:SimpleSchemaParser.UnnamedDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declaration.
    def visitDeclaration(self, ctx:SimpleSchemaParser.DeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declarationAttributes.
    def visitDeclarationAttributes(self, ctx:SimpleSchemaParser.DeclarationAttributesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declarationAttributesItems.
    def visitDeclarationAttributesItems(self, ctx:SimpleSchemaParser.DeclarationAttributesItemsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#declarationAttributesItem__.
    def visitDeclarationAttributesItem__(self, ctx:SimpleSchemaParser.DeclarationAttributesItem__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extension.
    def visitExtension(self, ctx:SimpleSchemaParser.ExtensionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extensionContent__.
    def visitExtensionContent__(self, ctx:SimpleSchemaParser.ExtensionContent__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extensionContentStandard__.
    def visitExtensionContentStandard__(self, ctx:SimpleSchemaParser.ExtensionContentStandard__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extensionContentPositional.
    def visitExtensionContentPositional(self, ctx:SimpleSchemaParser.ExtensionContentPositionalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extensionContentKeywords__.
    def visitExtensionContentKeywords__(self, ctx:SimpleSchemaParser.ExtensionContentKeywords__Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SimpleSchemaParser#extensionContentKeyword.
    def visitExtensionContentKeyword(self, ctx:SimpleSchemaParser.ExtensionContentKeywordContext):
        return self.visitChildren(ctx)



del SimpleSchemaParser