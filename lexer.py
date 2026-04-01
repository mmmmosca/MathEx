from enum import Enum

class TokenType(Enum):
    PLUS = 1
    MINUS = 2
    STAR = 3
    FSLASH = 4
    MODULO = 5
    POWER = 6
    SQRT = 7
    LPAREN = 8
    RPAREN = 9
    NUMBER = 10
    ID = 11
    EQUAL = 12
    EOL = 15

class Token:
    def __init__(self, type, s):
        self.type = type
        self.s = s

class Lexer:
    def __init__(self, line: str):
        self.line = line
        self.tokens = []

    def tokenize_num(self, i):
        j = i
        while j < len(self.line) and (self.line[j].isdigit() or self.line[j] == '.'):
            j += 1
        return self.line[i:j], j
    
    def tokenize_id(self, i):
        j = i
        while j < len(self.line) and (self.line[j].isalpha() or self.line[j] == '_'):
            j += 1
        return self.line[i:j], j

    def tokenize(self):
        i = 0
        self.tokens = []
        while i < len(self.line):
            match self.line[i]:
                case '+':
                    self.tokens.append(Token(TokenType.PLUS, self.line[i]))
                case '-':
                    self.tokens.append(Token(TokenType.MINUS, self.line[i]))
                    i += 1
                case '*':
                    self.tokens.append(Token(TokenType.STAR, self.line[i]))
                case '/':
                    self.tokens.append(Token(TokenType.FSLASH, self.line[i]))
                case '%':
                    self.tokens.append(Token(TokenType.MODULO, self.line[i]))
                case '^':
                    self.tokens.append(Token(TokenType.POWER, self.line[i]))
                case '\\':
                    self.tokens.append(Token(TokenType.SQRT, self.line[i]))
                case '(':
                    self.tokens.append(Token(TokenType.LPAREN, self.line[i]))
                case ')':
                    self.tokens.append(Token(TokenType.RPAREN, self.line[i]))
                case '=':
                    self.tokens.append(Token(TokenType.EQUAL, self.line[i]))
            
            if self.line[i].isdigit() or self.line[i] == '.':
                res, j = self.tokenize_num(i)
                self.tokens.append(Token(TokenType.NUMBER, res))
                i = j
                continue
            
            if self.line[i].isalpha():
                res, j = self.tokenize_id(i)
                self.tokens.append(Token(TokenType.ID, res))
                i = j
                continue
            
            i += 1
        
        self.tokens.append(Token(TokenType.EOL, ''))
        return self.tokens