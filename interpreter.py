import lexer
import parser
import sys
import re
from collections import defaultdict

variables = {}
functions = {}

def parse_term(term):
    term = term.replace(" ", "")
    if "x" in term:
        coef = term.replace("*x", "").replace("x", "")
        coef = int(coef) if coef not in ("", "+", "-") else (1 if coef in ("", "+") else -1)
        return {1: coef}
    else:
        return {0: int(term)}

def add_poly(p1, p2):
    res = defaultdict(int, p1)
    for k, v in p2.items():
        res[k] += v
    return dict(res)

def mul_poly(p1, p2):
    res = defaultdict(int)
    for d1, c1 in p1.items():
        for d2, c2 in p2.items():
            res[d1 + d2] += c1 * c2
    return dict(res)

def pow_poly(p, n):
    res = {0: 1}
    for _ in range(n):
        res = mul_poly(res, p)
    return res

def parse_expr(expr):
    expr = expr.strip().replace(" ", "")
    if expr.startswith("(") and expr.endswith(")"):
        expr = expr[1:-1]
    if "^" in expr:
        base, power = expr.split("^")
        return pow_poly(parse_expr(base), int(power))
    if "*" in expr:
        parts = expr.split("*")
        p = parse_expr(parts[0])
        for part in parts[1:]:
            p = mul_poly(p, parse_expr(part))
        return p
    if "+" in expr:
        parts = expr.split("+")
        p = parse_expr(parts[0])
        for part in parts[1:]:
            p = add_poly(p, parse_expr(part))
        return p
    if "-" in expr[1:]:
        parts = re.split(r'(?<=.)(-)', expr)
        p = parse_expr(parts[0])
        i = 1
        while i < len(parts):
            sign = parts[i]
            next_part = parts[i+1]
            if sign == "-":
                p = add_poly(p, {k:-v for k,v in parse_expr(next_part).items()})
            i += 2
        return p
    return parse_term(expr)

def poly_to_str(poly):
    terms = []
    for d in sorted(poly.keys(), reverse=True):
        c = poly[d]
        if c == 0:
            continue
        if d == 0:
            terms.append(str(c))
        elif d == 1:
            if c == 1:
                terms.append("x")
            elif c == -1:
                terms.append("-x")
            else:
                terms.append(f"{c}*x")
        else:
            if c == 1:
                terms.append(f"x^{d}")
            elif c == -1:
                terms.append(f"-x^{d}")
            else:
                terms.append(f"{c}*x^{d}")
    return "+".join(terms) if terms else "0"

def substitute(node, param, value):
    if node.type == parser.NodeType.Number:
        return node.token.s
    elif node.type == parser.NodeType.Variable:
        if node.token.s == param:
            return f"({value})"
        return node.token.s
    elif node.type == parser.NodeType.BinOp:
        left = substitute(node.lhs, param, value)
        right = substitute(node.rhs, param, value)
        op = node.token.type
        return f"({left}+{right})" if op==lexer.TokenType.PLUS else \
               f"({left}-{right})" if op==lexer.TokenType.MINUS else \
               f"({left}*{right})" if op==lexer.TokenType.STAR else \
               f"({left}^{right})" if op==lexer.TokenType.POWER else f"({left}/{right})"
    elif node.type == parser.NodeType.Call:
        func = functions.get(node.id)
        arg_expr = substitute(node.expr, param, value)
        return substitute(func.expr, func.param, arg_expr)
    elif node.type == parser.NodeType.Parenthesis:
        return f"({substitute(node.expr, param, value)})"
    return ""

def eval_eq(node):
    if node.type == parser.NodeType.Call:
        func = functions[node.id]
        arg_expr = eval_eq(node.expr)
        expr = substitute(func.expr, func.param, arg_expr)
        poly = parse_expr(expr)
        return poly_to_str(poly)
    elif node.type == parser.NodeType.Function:
        functions[node.id] = node
        return None
    elif node.type == parser.NodeType.BinOp:
        left = eval_eq(node.lhs)
        right = eval_eq(node.rhs)
        op = node.token.type
        return f"({left}+{right})" if op==lexer.TokenType.PLUS else \
               f"({left}-{right})" if op==lexer.TokenType.MINUS else \
               f"({left}*{right})" if op==lexer.TokenType.STAR else f"({left}^{right})"
    elif node.type == parser.NodeType.Number:
        return node.token.s
    elif node.type == parser.NodeType.Variable:
        return node.token.s
    elif node.type == parser.NodeType.Parenthesis:
        return f"({eval_eq(node.expr)})"
    return ""

def run_line(line, eq_mode=False):
    lex = lexer.Lexer(line)
    tokens = lex.tokenize()
    p = parser.Parser(tokens)
    ast = p.parseAssignment()
    if ast.type == parser.NodeType.Function:
        functions[ast.id] = ast
        return
    if eq_mode:
        res = eval_eq(ast)
        if res:
            print(res)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Type '--ast' after an expression to view the abstract syntax tree")
        print("Type '--eq' to see symbolic expansion")
        print("Type 'exit' or press Ctrl+C to quit\n")
        while True:
            try:
                line = input(">> ").strip()
                if line == "exit":
                    break
                eq_mode = line.endswith("--eq")
                if eq_mode:
                    line = line[:-4].strip()
                run_line(line, eq_mode)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        print("\nThank you and goodbye!")
    else:
        with open(sys.argv[1], "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                eq_mode = line.endswith("--eq")
                if eq_mode:
                    line = line[:-4].strip()
                run_line(line, eq_mode)
