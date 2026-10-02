import lexer
import parser

import sys
import math
import random
import re
import cmath

variables = {}
functions = {}

def add_poly(p1, p2):
    result = p1.copy()
    for k, v in p2.items():
        result[k] = result.get(k, 0) + v
    return {k: v for k, v in result.items() if abs(v) > 1e-12}

def mul_poly(p1, p2):
    result = {}
    for k1, v1 in p1.items():
        for k2, v2 in p2.items():
            result[k1 + k2] = result.get(k1 + k2, 0) + v1 * v2
    return {k: v for k, v in result.items() if abs(v) > 1e-12}

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
        if abs(v) < 1e-12: continue
        v = int(v) if isinstance(v, float) and v.is_integer() else v
        coef = "" if abs(v) == 1 and k != 0 else str(abs(v))
        if k == 0: term = f"{abs(v)}"
        elif k == 1: term = f"{coef}x"
        else: term = f"{coef}x^{k}"
        if v < 0: term = f"-{term}"
        terms.append(term)
    if not terms: return "0"
    expr = terms[0]
    for term in terms[1:]:
        if term.startswith("-"): expr += term
        else: expr += f"+{term}"
    return expr

def split_top_level(expr, sep):
    parts = []
    buf = ""
    depth = 0
    for c in expr:
        if c == "(": depth += 1
        elif c == ")": depth -= 1
        if c == sep and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += c
    if buf: parts.append(buf)
    return parts

def parse_expr(expr):
    expr = expr.strip()
    if expr.startswith("\\(") and expr.endswith(")"):
        return {0: 0}
    while expr.startswith("(") and expr.endswith(")"):
        if expr.startswith("\\("): break
        depth = 0
        for i, c in enumerate(expr):
            if c == "(": depth += 1
            elif c == ")": depth -= 1
            if depth == 0 and i < len(expr) - 1: break
        else:
            expr = expr[1:-1].strip()
            continue
        break
    parts = split_top_level(expr, "+")
    if len(parts) > 1:
        p = parse_expr(parts[0])
        for t in parts[1:]:
            p = add_poly(p, parse_expr(t))
        return p
    parts = split_top_level(expr, "-")
    if len(parts) > 1:
        p = parse_expr(parts[0])
        for t in parts[1:]:
            p = add_poly(p, {k: -v for k, v in parse_expr(t).items()})
        return p
    parts = split_top_level(expr, "*")
    if len(parts) > 1:
        p = parse_expr(parts[0])
        for f in parts[1:]:
            p = mul_poly(p, parse_expr(f))
        return p
    parts = split_top_level(expr, "^")
    if len(parts) == 2:
        base, power = parts
        try: power_val = int(power)
        except: power_val = 1
        return pow_poly(parse_expr(base), power_val)
    return parse_term(expr)

def parse_term(term):
    term = term.strip()
    if term.startswith("\\(") and term.endswith(")"):
        return {0: 0}
    if term.startswith("(") and term.endswith(")"):
        return parse_expr(term[1:-1])
    try:
        return {0: int(term)}
    except:
        try:
            return {0: float(term)}
        except:
            if term == "x": return {1: 1}
            elif term == "-x": return {1: -1}
            m = re.match(r'^(-?\d*\.?\d*)x(\^(\d+))?$', term)
            if m:
                coef_s = m.group(1)
                coef = float(coef_s) if coef_s not in ("", "-") else (-1.0 if coef_s == "-" else 1.0)
                exp = int(m.group(3)) if m.group(3) else 1
                return {exp: coef}
            raise ValueError(f"Termine non riconoscibile: '{term}'")

def substitute(node, param, value):
    if node.type == parser.NodeType.Number:
        return node.token.s
    elif node.type == parser.NodeType.Variable:
        if node.token.s == param:
            return value
        return node.token.s
    elif node.type == parser.NodeType.BinOp:
        left = substitute(node.lhs, param, value)
        right = substitute(node.rhs, param, value)
        op = node.token.type
        if op == lexer.TokenType.PLUS:   return f"{left}+{right}"
        elif op == lexer.TokenType.MINUS:  return f"{left}-{right}"
        elif op == lexer.TokenType.STAR:
            l = f"({left})" if any(c in left for c in "+-") else left
            r = f"({right})" if any(c in right for c in "+-") else right
            return f"{l}*{r}"
        elif op == lexer.TokenType.FSLASH:
            l = f"({left})" if any(c in left for c in "+-") else left
            r = f"({right})" if any(c in right for c in "+-") else right
            return f"{l}/{r}"
        elif op == lexer.TokenType.POWER:
            l = f"({left})" if any(c in left for c in "+-*/") else left
            return f"{l}^{right}"
    elif node.type == parser.NodeType.UnOp:
        val = substitute(node.rhs, param, value)
        if node.token.type == lexer.TokenType.MINUS:
            return f"-({val})" if any(c in val for c in "+-") else f"-{val}"
        elif node.token.type == lexer.TokenType.SQRT:
            if val.startswith("\\(") and val.endswith(")"): return f"\\{val[1:]}"
            return f"\\({val})"
    elif node.type == parser.NodeType.Parenthesis:
        return substitute(node.expr, param, value)
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
        if op == lexer.TokenType.PLUS:   return f"{left}+{right}"
        elif op == lexer.TokenType.MINUS:  return f"{left}-{right}"
        elif op == lexer.TokenType.STAR:
            l = f"({left})" if any(c in left for c in "+-") else left
            r = f"({right})" if any(c in right for c in "+-") else right
            return f"{l}*{r}"
        elif op == lexer.TokenType.FSLASH:
            l = f"({left})" if any(c in left for c in "+-") else left
            r = f"({right})" if any(c in right for c in "+-") else right
            return f"{l}/{r}"
        elif op == lexer.TokenType.POWER:
            l = f"({left})" if any(c in left for c in "+-*/") else left
            return f"{l}^{right}"
    elif node.type == parser.NodeType.UnOp:
        val = eval_eq(node.rhs)
        if node.token.type == lexer.TokenType.MINUS:
            return f"-({val})" if any(c in val for c in "+-") else f"-{val}"
        elif node.token.type == lexer.TokenType.SQRT:
            if val.startswith("\\(") and val.endswith(")"): return f"\\{val[1:]}"
            return f"\\({val})"
    elif node.type == parser.NodeType.Parenthesis:
        return eval_eq(node.expr)
    elif node.type == parser.NodeType.Function:
        functions[node.id] = node
        return None
    elif node.type == parser.NodeType.Call:
        func = functions.get(node.id)
        if func is None: raise ValueError(f"Undefined function: {node.id}")
        arg_expr = eval_eq(node.expr)
        substituted = substitute(func.expr, func.param, arg_expr)
        if "\\" in substituted: return substituted
        poly = parse_expr(substituted)
        return format_poly(poly)
    elif node.type == parser.NodeType.Assignment: return None
    elif node.type == parser.NodeType.Eol: return ""
    else: raise ValueError(f"Unknown node type: {node.type}")

def _format_root(r):
    if isinstance(r, complex):
        real = round(r.real, 6)
        imag = round(r.imag, 6)
        if abs(imag) < 1e-6:
            return str(real if real != -0.0 else 0.0)
        if abs(real) < 1e-6:
            return f"{imag}i"
        sign = "+" if imag > 0 else "-"
        return f"{real} {sign} {abs(imag)}i"
    else:
        val = round(r, 6)
        return str(val if val != -0.0 else 0.0)

def solve_poly(poly):
    max_deg = max(poly.keys()) if poly else 0
    if max_deg > 3:
        raise ValueError(f"Cannot solve equations of degree {max_deg} (supported up to degree 3)")

    a3 = poly.get(3, 0.0)
    a2 = poly.get(2, 0.0)
    a1 = poly.get(1, 0.0)
    a0 = poly.get(0, 0.0)

    # Degree 0: Constant
    if max_deg == 0 or (abs(a3) < 1e-12 and abs(a2) < 1e-12 and abs(a1) < 1e-12):
        if abs(a0) < 1e-12:
            return "Infinite solutions (0 = 0)"
        return "No solutions"

    # Degree 1: Linear ax + b = 0
    if abs(a3) < 1e-12 and abs(a2) < 1e-12:
        x = -a0 / a1
        return [x]

    # Degree 2: Quadratic ax^2 + bx + c = 0
    if abs(a3) < 1e-12:
        disc = a1**2 - 4 * a2 * a0
        if disc >= 0:
            x1 = (-a1 + math.sqrt(disc)) / (2 * a2)
            x2 = (-a1 - math.sqrt(disc)) / (2 * a2)
            return [x1, x2] if abs(disc) > 1e-12 else [x1]
        else:
            x1 = (-a1 + cmath.sqrt(disc)) / (2 * a2)
            x2 = (-a1 - cmath.sqrt(disc)) / (2 * a2)
            return [x1, x2]

    # Degree 3: Cubic ax^3 + bx^2 + cx + d = 0 (Cardano's Formula)
    a, b, c, d = a3, a2, a1, a0

    # Depress the cubic equation x^3 + p*x + q = 0 via substitution x = t - b/(3a)
    p = (3 * a * c - b**2) / (3 * a**2)
    q = (2 * b**3 - 9 * a * b * c + 27 * a**2 * d) / (27 * a**3)

    delta = (q / 2)**2 + (p / 3)**3

    roots = []
    w = (-1 + cmath.sqrt(-3)) / 2  # Primitive cube root of unity

    if abs(delta) < 1e-12:
        if abs(p) < 1e-12 and abs(q) < 1e-12:
            roots = [0.0, 0.0, 0.0]
        else:
            u = (-q / 2)**(1/3) if -q / 2 >= 0 else -(- -q / 2)**(1/3)
            roots = [2 * u, -u, -u]
    elif delta > 0:
        u_val = -q / 2 + math.sqrt(delta)
        v_val = -q / 2 - math.sqrt(delta)
        u = u_val**(1/3) if u_val >= 0 else -(-u_val)**(1/3)
        v = v_val**(1/3) if v_val >= 0 else -(-v_val)**(1/3)

        t1 = u + v
        t2 = -(u + v) / 2 + (u - v) * math.sqrt(3) / 2 * 1j
        t3 = -(u + v) / 2 - (u - v) * math.sqrt(3) / 2 * 1j
        roots = [t1, t2, t3]
    else:
        # 3 real roots (Casus Irreducibilis)
        r = math.sqrt(-(p / 3)**3)
        phi = math.acos(-q / (2 * r))
        t1 = 2 * (-p / 3)**0.5 * math.cos(phi / 3)
        t2 = 2 * (-p / 3)**0.5 * math.cos((phi + 2 * math.pi) / 3)
        t3 = 2 * (-p / 3)**0.5 * math.cos((phi + 4 * math.pi) / 3)
        roots = [t1, t2, t3]

    # Convert t roots back to x roots: x = t - b/(3a)
    final_roots = [r - b / (3 * a) for r in roots]
    return final_roots

def solve_line(line):
    eq_str = line
    if "--solve" in eq_str:
        eq_str = eq_str.replace("--solve", "").strip()

    if "=" in eq_str:
        left_str, right_str = eq_str.split("=", 1)
        p_left = parse_expr(left_str)
        p_right = parse_expr(right_str)
        poly = add_poly(p_left, {k: -v for k, v in p_right.items()})
    else:
        poly = parse_expr(eq_str)

    roots = solve_poly(poly)
    if isinstance(roots, str):
        print(roots)
    else:
        formatted = [_format_root(r) for r in roots]
        # Remove duplicate numerical values if any
        unique_roots = list(dict.fromkeys(formatted))
        print("x =", ", ".join(unique_roots))

def eval_ast(node: parser.Node):
    if node.type == parser.NodeType.Number: return float(node.token.s)
    elif node.type == parser.NodeType.Variable:
        if node.token.s == "PI": return math.pi
        elif node.token.s == "rand": return random.randint(0, sys.maxsize)
        elif node.token.s in variables: return variables[node.token.s]
        else: raise ValueError(f"Undefined variable: {node.token.s}")
    elif node.type == parser.NodeType.BinOp:
        left = eval_ast(node.lhs)
        right = eval_ast(node.rhs)
        if node.token.type == lexer.TokenType.PLUS:   return left + right
        elif node.token.type == lexer.TokenType.MINUS:  return left - right
        elif node.token.type == lexer.TokenType.STAR:   return left * right
        elif node.token.type == lexer.TokenType.FSLASH: return left / right
        elif node.token.type == lexer.TokenType.MODULO: return left % right
        elif node.token.type == lexer.TokenType.POWER:  return left ** right
    elif node.type == parser.NodeType.UnOp:
        if node.token.type == lexer.TokenType.MINUS: return -eval_ast(node.rhs)
        elif node.token.type == lexer.TokenType.SQRT: return math.sqrt(eval_ast(node.rhs))
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
        if old_val is not None: variables[param] = old_val
        else: variables.pop(param, None)
        return result
    elif node.type == parser.NodeType.Eol: return
    else: raise ValueError(f"Unknown node type: {node.type}")

def run_line(line, eq_mode, ast_mode, solve_mode):
    if solve_mode:
        solve_line(line)
        return

    lex = lexer.Lexer(line)
    tokens = lex.tokenize()
    p = parser.Parser(tokens)
    ast = p.parseAssignment()
    if eq_mode:
        res = eval_eq(ast)
        if res: print(res)
    elif ast_mode:
        parser.print_ast(ast)
    else:
        res = eval_ast(ast)
        if res is not None and ast.type not in (parser.NodeType.Assignment, parser.NodeType.Function, parser.NodeType.Eol):
            print(res)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("MathEx REPL")
        print("Type '--ast' after an expression to see its AST")
        print("Type '--eq' after a function call to see the equation of that function")
        print("Type '--solve' after an equation to solve polynomials up to degree 3")
        print("Type 'exit' to exit from the REPL\n")
        while True:
            try:
                line = input(">> ").strip()
                if line == "exit": break
                ast_mode = False
                eq_mode = False
                solve_mode = False

                if line.endswith("--solve"):
                    solve_mode = True
                    line = line[:-7].strip()
                elif line.endswith("--eq"):
                    eq_mode = True
                    line = line[:-4].strip()
                elif line.endswith("--ast"):
                    ast_mode = True
                    line = line[:-5].strip()

                run_line(line, eq_mode, ast_mode, solve_mode)
            except KeyboardInterrupt: break
            except Exception as e: print(f"Error: {e}")
    else:
        with open(sys.argv[1], 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                eq_mode = False
                solve_mode = False
                if line.endswith("--solve"):
                    solve_mode = True
                    line = line[:-7].strip()
                elif line.endswith("--eq"):
                    eq_mode = True
                    line = line[:-4].strip()
                try: run_line(line, eq_mode, False, solve_mode)
                except Exception as e: print(f"Error: {e}")
