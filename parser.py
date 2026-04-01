import lexer
from enum import Enum

class NodeType(Enum):
    Number = 1
    BinOp = 2
    UnOp = 3
    Parenthesis = 4
    Variable = 5
    Assignment = 6
    Function = 7
    Call = 8
    Eol = 9

class Node:
    def __init__(self, 
                 type, 
                 token, 
                 lhs='',
                 rhs='', 
                 expr='', 
                 id='', 
                 param=''):
        self.type: NodeType = type
        self.token: list[lexer.Token] = token
        self.lhs: Node = lhs
        self.rhs: Node = rhs
        self.expr: Node = expr
        self.id = id
        self.param = param

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0
    
    def makeNumber(self, tok):
        return Node(NodeType.Number, tok)
    
    def makeBinOp(self, tok, lhs, rhs):
        return Node(NodeType.BinOp, tok, lhs=lhs, rhs=rhs)
    
    def makeUnOp(self, tok, rhs):
        return Node(NodeType.UnOp, tok, rhs=rhs)
    
    def makeParen(self, tok, expr):
        return Node(NodeType.Parenthesis, tok, expr=expr)
    
    def makeAssign(self, tok, id, rhs):
        return Node(NodeType.Assignment, tok, id=id, rhs=rhs)
    
    def makeVariable(self, tok, id):
        return Node(NodeType.Variable, tok, id=id)
    
    def makeFunction(self, tok, id, param, expr):
        return Node(NodeType.Function, tok, id=id, param=param, expr=expr)
    
    def makeCall(self, tok, id, expr):
        return Node(NodeType.Call, tok, id=id, expr=expr)
    
    def makeEol(self, tok):
        return Node(NodeType.Eol, tok)
    
    def isAtEnd(self):
        return self.i >= len(self.tokens)
    
    def parseExpression(self):
        node = self.parseTerm()
        while not self.isAtEnd() and (self.tokens[self.i].type in (lexer.TokenType.PLUS, lexer.TokenType.MINUS)):
            opTok = self.tokens[self.i]
            self.i += 1
            rhs = self.parseTerm()
            node = self.makeBinOp(opTok, node, rhs)
        return node
    
    def parseAssignment(self):
        if not self.isAtEnd() and self.tokens[self.i].type == lexer.TokenType.ID:
            var_tok = self.tokens[self.i]
            saved_i = self.i
            self.i += 1
            if not self.isAtEnd() and self.tokens[self.i].type == lexer.TokenType.EQUAL:
                self.i += 1
                rhs = self.parseExpression()
                return self.makeAssign(var_tok, var_tok.s, rhs)
            elif not self.isAtEnd() and self.tokens[self.i].type == lexer.TokenType.LPAREN:
                if (self.i + 3 < len(self.tokens) and
                    self.tokens[self.i + 1].type == lexer.TokenType.ID and
                    self.tokens[self.i + 2].type == lexer.TokenType.RPAREN and
                    self.tokens[self.i + 3].type == lexer.TokenType.EQUAL):
                    self.i = saved_i
                    return self.parseFunction()
                else:
                    self.i = saved_i
            else:
                self.i = saved_i
        return self.parseExpression()

    def parseTerm(self):
        node = self.parsePower()
        while not self.isAtEnd() and (self.tokens[self.i].type in (lexer.TokenType.STAR, lexer.TokenType.FSLASH, lexer.TokenType.MODULO)):
            opTok = self.tokens[self.i]
            self.i += 1
            rhs = self.parsePower()
            node = self.makeBinOp(opTok, node, rhs)
        return node

    def parsePower(self):
        node = self.parseFactor()
        while not self.isAtEnd() and self.tokens[self.i].type == (lexer.TokenType.POWER):
            opTok = self.tokens[self.i]
            self.i += 1
            rhs = self.parseFactor()
            node = self.makeBinOp(opTok, node, rhs)
        return node

    def parseFactor(self):
        return self.parseUnary()

    def parseUnary(self):
        if not self.isAtEnd() and self.tokens[self.i].type == lexer.TokenType.MINUS:
            opTok = self.tokens[self.i]
            self.i += 1
            rhs = self.parseUnary()
            return self.makeUnOp(opTok, rhs)
        elif not self.isAtEnd() and self.tokens[self.i].type == lexer.TokenType.SQRT:
            opTok = self.tokens[self.i]
            self.i += 1
            rhs = self.parseUnary()
            return self.makeUnOp(opTok, rhs)
        
        return self.parsePrimary()

    def parseFunction(self):
        tok = self.tokens[self.i]
        id = self.tokens[self.i].s
        self.i += 1
        param = ''
        if not self.isAtEnd() and self.tokens[self.i].type == lexer.TokenType.LPAREN:
            self.i += 1
            if not self.isAtEnd() and self.tokens[self.i].type == lexer.TokenType.ID:
                param = self.tokens[self.i].s
                self.i += 1
            else:
                raise Exception("Expected id for function parameter")
        else:
            raise Exception("Expected (")
        if self.isAtEnd() or self.tokens[self.i].type != lexer.TokenType.RPAREN:
            raise Exception("Expected )")
        self.i += 1
        if self.isAtEnd() or self.tokens[self.i].type != lexer.TokenType.EQUAL:
            raise Exception("Expected =")
        self.i += 1
        expr = self.parseExpression()
        return self.makeFunction(tok, id, param, expr)

    def parseCall(self, tok, id):
        self.i += 1
        expr = self.parseExpression()
        if self.isAtEnd() or self.tokens[self.i].type != lexer.TokenType.RPAREN:
            raise Exception("Expected )")
        self.i += 1
        return self.makeCall(tok, id, expr)


    def parsePrimary(self):
        tok = self.tokens[self.i]
        if tok.type == lexer.TokenType.NUMBER:
            self.i += 1
            return self.makeNumber(tok)
        elif tok.type == lexer.TokenType.LPAREN:
            self.i += 1
            expr = self.parseExpression()
            if self.isAtEnd() or self.tokens[self.i].type != lexer.TokenType.RPAREN:
                raise Exception("Expected ')'")
            self.i += 1
            return self.makeParen(tok, expr)
        elif tok.type == lexer.TokenType.ID:
            opTok = self.tokens[self.i]
            id = self.tokens[self.i].s
            self.i += 1
            if not self.isAtEnd() and self.tokens[self.i].type == lexer.TokenType.LPAREN:
                return self.parseCall(opTok, id)
            else:
                return self.makeVariable(opTok, id)
        elif tok.type == lexer.TokenType.EQUAL:
            opTok = self.tokens[self.i]
            if self.i-1 > len(self.line):
                id = self.tokens[self.i-1].s
            else:
                raise Exception("Expected id before '='")
            self.i += 1
            if self.isAtEnd():
                raise Exception("Expected expression after '='")
            rhs = self.parseExpression()
            return self.makeAssign(opTok, id, rhs)
        elif tok.type == lexer.TokenType.EOL:
            return self.makeEol(tok)
        else:
            raise Exception(f"Unexpected token: {tok.type}")

def print_ast(node, indent=0): 
    spaces = "  " * indent 
    if node.type == NodeType.Number: 
        print(f"{spaces}Number: {node.token.s}") 
    elif node.type == NodeType.BinOp: 
        print(f"{spaces}BinOp: {node.token.type.name}") 
        print_ast(node.lhs, indent + 1) 
        print_ast(node.rhs, indent + 1) 
    elif node.type == NodeType.UnOp: 
        print(f"{spaces}UnOp: {node.token.type.name}") 
        print_ast(node.rhs, indent + 1) 
    elif node.type == NodeType.Parenthesis: 
        print(f"{spaces}Paren:") 
        print_ast(node.expr, indent + 1)
    elif node.type == NodeType.Assignment:
        print(f"{spaces}Assign:")
        print(f"{spaces}  Id: {node.id}")
        print_ast(node.rhs, indent+1)    
    elif node.type == NodeType.Function:
        print(f"{spaces}Function:")
        print(f"{spaces}  Id: {node.id}")
        print(f"{spaces}  Param: {node.param}")
        print_ast(node.expr, indent+1)
    elif node.type == NodeType.Call:
        print(f"{spaces}Call:")
        print(f"{spaces}  Id: {node.id}")
        print_ast(node.expr, indent+1)
    elif node.type == NodeType.Variable:
        print(f"{spaces}Var: {node.token.s}")