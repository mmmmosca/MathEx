import lexer
import parser

import sys
import math
import random
import re

variables = {}
functions = {}

def add_poly(p1, p2):
    result = p1.copy()
    for k, v in p2.items():
        result[k] = result.get(k, 0) + v
    return {k: v for k, v in result.items() if v != 0}

def mul_poly(p1, p2):
    result = {}
    for k1, v1 in p1.items():
        for k2, v2 in p2.items():
            result[k1 + k2] = result.get(k1 + k2, 0) + v1 * v2
    return {k: v for k, v in result.items() if v != 0}

def pow_poly(p, n):
    if n == 0: return {0: 1}
    result = p
    for _ in range(n - 1):
        result = mul_poly(result, p)
    return result

def format_poly(p):
    if not p: return "0"
    terms = []
    for k in sorted(p.keys(), reverse=True):
        v = p[k]
        if v == 0: continue
        coef = "" if abs(v) == 1 and k != 0 else str(abs(v))
        if k == 0: term = f"{abs(v)}"
        elif k == 1: term = f"{coef}x"
        else: term = f"{coef}x^{k}"
        if v < 0: term = f"-{term}"
        terms.append(term)
    expr = terms[0]
    for term in terms[1:]:
        if term.startswith("-"): expr += term
        else: expr += f"+{term}"
    return expr

def split_top_level(expr, sep):
    parts=[]
    buf=""
    depth=0
    for c in expr:
        if c=="(": depth+=1
        elif c==")": depth-=1
        if c==sep and depth==0:
            parts.append(buf)
            buf=""
        else:
            buf+=c
    if buf: parts.append(buf)
    return parts

def parse_expr(expr):
    expr = expr.strip()
    while expr.startswith("(") and expr.endswith(")"):
        depth=0
        for i,c in enumerate(expr):
            if c=="(": depth+=1
            elif c==")": depth-=1
            if depth==0 and i<len(expr)-1: break
        else:
            expr = expr[1:-1].strip()
            continue
        break
    parts = split_top_level(expr, "+")
    if len(parts)>1:
        p = parse_expr(parts[0])
        for t in parts[1:]:
            p = add_poly(p, parse_expr(t))
        return p
    parts = split_top_level(expr, "-")
    if len(parts)>1:
        p = parse_expr(parts[0])
        for t in parts[1:]:
            p = add_poly(p, {k:-v for k,v in parse_expr(t).items()})
        return p
    parts = split_top_level(expr, "*")
    if len(parts)>1:
        p = parse_expr(parts[0])
        for f in parts[1:]:
            p = mul_poly(p, parse_expr(f))
        return p
    parts = split_top_level(expr, "^")
    if len(parts)==2:
        base, power = parts
        power_val = int(eval_ast(parser.Parser(lexer.Lexer(power).tokenize()).parseAssignment()))
        return pow_poly(parse_expr(base), power_val)
    return parse_term(expr)

def parse_term(term):
    term = term.strip()
    if term.startswith("(") and term.endswith(")"):
        return parse_expr(term)
    try:
        return {0:int(term)}
    except:
        if term=="x": return {1:1}
        elif term=="-x": return {1:-1}
        return parse_expr(term)

def substitute(node, param, value):
    if node.type == parser.NodeType.Number: return node.token.s
    elif node.type == parser.NodeType.Variable:
        if node.token.s == param: return f"({value})"
        return node.token.s
    elif node.type == parser.NodeType.BinOp:
        left = substitute(node.lhs, param, value)
        right = substitute(node.rhs, param, value)
        op = node.token.type
        if op == lexer.TokenType.PLUS: return f"({left}+{right})"
        elif op == lexer.TokenType.MINUS: return f"({left}-{right})"
        elif op == lexer.TokenType.STAR: return f"({left}*{right})"
        elif op == lexer.TokenType.FSLASH: return f"({left}/{right})"
        elif op == lexer.TokenType.POWER: return f"({left}^{right})"
    elif node.type == parser.NodeType.UnOp:
        val = substitute(node.rhs, param, value)
        if node.token.type == lexer.TokenType.MINUS: return f"(-{val})"
        elif node.token.type == lexer.TokenType.SQRT: return f"sqrt({val})"
    elif node.type == parser.NodeType.Parenthesis:
        return f"({substitute(node.expr,param,value)})"
    elif node.type == parser.NodeType.Call:
        func = functions.get(node.id)
        if func is None: raise ValueError(f"Undefined function: {node.id}")
        arg_expr = substitute(node.expr, param, value)
        return substitute(func.expr, func.param, arg_expr)
    return ""

def eval_eq(node: parser.Node):
    if node.type == parser.NodeType.Number: return node.token.s
    elif node.type == parser.NodeType.Variable: return node.token.s
    elif node.type == parser.NodeType.BinOp:
        left = eval_eq(node.lhs)
        right = eval_eq(node.rhs)
        op = node.token.type
        if op == lexer.TokenType.PLUS: return f"({left}+{right})"
        elif op == lexer.TokenType.MINUS: return f"({left}-{right})"
        elif op == lexer.TokenType.STAR: return f"({left}*{right})"
        elif op == lexer.TokenType.FSLASH: return f"({left}/{right})"
        elif op == lexer.TokenType.POWER: return f"({left}^{right})"
    elif node.type == parser.NodeType.UnOp:
        val = eval_eq(node.rhs)
        if node.token.type == lexer.TokenType.MINUS: return f"(-{val})"
        elif node.token.type == lexer.TokenType.SQRT: return f"sqrt({val})"
    elif node.type == parser.NodeType.Parenthesis:
        return f"({eval_eq(node.expr)})"
    elif node.type == parser.NodeType.Function:
        functions[node.id] = node
        return None
    elif node.type == parser.NodeType.Call:
        func = functions.get(node.id)
        if func is None: raise ValueError(f"Undefined function: {node.id}")
        arg_expr = eval_eq(node.expr)
        substituted = substitute(func.expr, func.param, arg_expr)
        poly = parse_expr(substituted)
        return format_poly(poly)
    elif node.type == parser.NodeType.Assignment: return None
    elif node.type == parser.NodeType.Eol: return ""
    else: raise ValueError(f"Unknown node type: {node.type}")

def eval_ast(node: parser.Node):
    if node.type == parser.NodeType.Number: return float(node.token.s)
    elif node.type == parser.NodeType.Variable:
        if node.token.s=="PI": return math.pi
        elif node.token.s=="rand": return random.randint(0,sys.maxsize)
        elif node.token.s in variables: return variables[node.token.s]
        else: raise ValueError(f"Undefined variable: {node.token.s}")
    elif node.type == parser.NodeType.BinOp:
        left = eval_ast(node.lhs)
        right = eval_ast(node.rhs)
        if node.token.type==lexer.TokenType.PLUS: return left+right
        elif node.token.type==lexer.TokenType.MINUS: return left-right
        elif node.token.type==lexer.TokenType.STAR: return left*right
        elif node.token.type==lexer.TokenType.FSLASH: return left/right
        elif node.token.type==lexer.TokenType.MODULO: return left%right
        elif node.token.type==lexer.TokenType.POWER: return left**right
    elif node.type == parser.NodeType.UnOp:
        if node.token.type==lexer.TokenType.MINUS: return -eval_ast(node.rhs)
        elif node.token.type==lexer.TokenType.SQRT: return math.sqrt(eval_ast(node.rhs))
    elif node.type == parser.NodeType.Parenthesis: return eval_ast(node.expr)
    elif node.type == parser.NodeType.Assignment:
        val = eval_ast(node.rhs)
        variables[node.id] = val
        return val
    elif node.type == parser.NodeType.Function:
        functions[node.id] = node
        return None
    elif node.type == parser.NodeType.Call:
        func = functions.get(node.id)
        if func is None: raise ValueError(f"Undefined function: {node.id}")
        arg_val = eval_ast(node.expr)
        param = func.param
        old_val = variables.get(param)
        variables[param] = arg_val
        result = eval_ast(func.expr)
        if old_val is not None: variables[param]=old_val
        else: variables.pop(param,None)
        return result
    elif node.type == parser.NodeType.Eol: return
    else: raise ValueError(f"Unknown node type: {node.type}")

def run_line(line, eq_mode):
    lex = lexer.Lexer(line)
    tokens = lex.tokenize()
    p = parser.Parser(tokens)
    ast = p.parseAssignment()
    if eq_mode:
        res = eval_eq(ast)
        if res: print(res)
    else:
        res = eval_ast(ast)
        if res is not None and ast.type not in (parser.NodeType.Assignment, parser.NodeType.Function, parser.NodeType.Eol):
            print(res)

if __name__=="__main__":
    if len(sys.argv)<2:
        while True:
            try:
                line = input(">> ").strip()
                if line=="exit": break
                eq_mode = False
                if line.endswith("--eq"):
                    eq_mode=True
                    line = line[:-4].strip()
                run_line(line, eq_mode)
            except KeyboardInterrupt: break
            except Exception as e: print(f"Error: {e}")
    else:
        with open(sys.argv[1],'r') as f:
            for line in f:
                line=line.strip()
                if not line: continue
                eq_mode=False
                if line.endswith("--eq"):
                    eq_mode=True
                    line=line[:-4].strip()
                try: run_line(line, eq_mode)
                except Exception as e: print(f"Error: {e}")
