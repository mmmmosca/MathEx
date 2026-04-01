import lexer
import parser

import sys
import math
import random
import re


variables = {}
functions = {}

def simplify(expr: str):
    expr = expr.replace(" ", "")

    expr = re.sub(r'\((\w+)\)', r'\1', expr)

    while True:
        new_expr = re.sub(r'\(\(([^()]+)\)\)', r'(\1)', expr)
        if new_expr == expr:
            break
        expr = new_expr

    expr = expr.replace("*(", "(")
    expr = expr.replace(")(", ")*(")

    return expr

def expand(expr: str):
    import re

    pattern = r'(\d+)\(([^()]+)\)'

    def repl(match):
        coef = int(match.group(1))
        inside = match.group(2)

        parts = re.split(r'(\+|\-)', inside)

        result = ""
        sign = "+"

        for part in parts:
            if part in "+-":
                sign = part
            else:
                part = part.strip()
                if not part:
                    continue

                if part.isdigit():
                    value = coef * int(part)
                    term = str(value)
                else:
                    term = f"{coef}{part}"

                if sign == "-":
                    result += f"-{term}"
                else:
                    result += f"+{term}"

        return result.lstrip('+')

    while re.search(pattern, expr):
        expr = re.sub(pattern, repl, expr)

    return expr

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
        if op == lexer.TokenType.PLUS:
            return f"({left}+{right})"
        elif op == lexer.TokenType.MINUS:
            return f"({left}-{right})"
        elif op == lexer.TokenType.STAR:
            return f"({left}*{right})"
        elif op == lexer.TokenType.FSLASH:
            return f"({left}/{right})"
        elif op == lexer.TokenType.POWER:
            return f"({left}^{right})"

    elif node.type == parser.NodeType.UnOp:
        val = substitute(node.rhs, param, value)
        if node.token.type == lexer.TokenType.MINUS:
            return f"(-{val})"
        elif node.token.type == lexer.TokenType.SQRT:
            return f"sqrt({val})"

    elif node.type == parser.NodeType.Parenthesis:
        return f"({substitute(node.expr, param, value)})"

    elif node.type == parser.NodeType.Call:
        func = functions.get(node.id)
        if func is None:
            raise ValueError(f"Undefined function: {node.id}")

        arg_expr = substitute(node.expr, param, value)
        return substitute(func.expr, func.param, arg_expr)

    return ""

def eval_eq(node: parser.Node):
    if node.type == parser.NodeType.Number:
        return node.token.s

    elif node.type == parser.NodeType.Variable:
        return node.token.s

    elif node.type == parser.NodeType.BinOp:
        left = eval_eq(node.lhs)
        right = eval_eq(node.rhs)

        op = node.token.type
        if op == lexer.TokenType.PLUS:
            return f"({left}+{right})"
        elif op == lexer.TokenType.MINUS:
            return f"({left}-{right})"
        elif op == lexer.TokenType.STAR:
            return f"({left}*{right})"
        elif op == lexer.TokenType.FSLASH:
            return f"({left}/{right})"
        elif op == lexer.TokenType.POWER:
            return f"({left}^{right})"

    elif node.type == parser.NodeType.UnOp:
        val = eval_eq(node.rhs)
        if node.token.type == lexer.TokenType.MINUS:
            return f"(-{val})"
        elif node.token.type == lexer.TokenType.SQRT:
            return f"sqrt({val})"

    elif node.type == parser.NodeType.Parenthesis:
        return f"({eval_eq(node.expr)})"

    elif node.type == parser.NodeType.Call:
        func = functions.get(node.id)
        if func is None:
            raise ValueError(f"Undefined function: {node.id}")

        arg_expr = eval_eq(node.expr)
        return substitute(func.expr, func.param, arg_expr)

    elif node.type == parser.NodeType.Function:
        functions[node.id] = node
        return None

    elif node.type == parser.NodeType.Assignment:
        return None

    elif node.type == parser.NodeType.Eol:
        return ""

    else:
        raise ValueError(f"Unknown node type: {node.type}")

def eval_ast(node: parser.Node):
    if node.type == parser.NodeType.Number:
        return float(node.token.s)

    elif node.type == parser.NodeType.Variable:
        if node.token.s == "PI":
            return math.pi
        elif node.token.s == "rand":
            return random.randint(0, 35999)
        else:
            if node.token.s in variables:
                return variables[node.token.s]
            else:
                raise ValueError(f"Undefined variable: {node.token.s}")

    elif node.type == parser.NodeType.BinOp:
        left = eval_ast(node.lhs)
        right = eval_ast(node.rhs)

        if node.token.type == lexer.TokenType.PLUS:
            return left + right
        elif node.token.type == lexer.TokenType.MINUS:
            return left - right
        elif node.token.type == lexer.TokenType.STAR:
            return left * right
        elif node.token.type == lexer.TokenType.FSLASH:
            return left / right
        elif node.token.type == lexer.TokenType.MODULO:
            return left % right
        elif node.token.type == lexer.TokenType.POWER:
            return left ** right

    elif node.type == parser.NodeType.UnOp:
        if node.token.type == lexer.TokenType.MINUS:
            return -eval_ast(node.rhs)
        elif node.token.type == lexer.TokenType.SQRT:
            return math.sqrt(eval_ast(node.rhs))

    elif node.type == parser.NodeType.Parenthesis:
        return eval_ast(node.expr)

    elif node.type == parser.NodeType.Assignment:
        val = eval_ast(node.rhs)
        variables[node.id] = val
        return val

    elif node.type == parser.NodeType.Function:
        functions[node.id] = node
        return None

    elif node.type == parser.NodeType.Call:
        func = functions.get(node.id)
        if func is None:
            raise ValueError(f"Undefined function: {node.id}")

        arg_val = eval_ast(node.expr)
        param = func.param

        old_val = variables.get(param)
        variables[param] = arg_val

        result = eval_ast(func.expr)

        if old_val is not None:
            variables[param] = old_val
        else:
            variables.pop(param, None)

        return result

    elif node.type == parser.NodeType.Eol:
        return

    else:
        raise ValueError(f"Unknown node type: {node.type}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Type '--ast' after an expression to view the abstract syntax tree")
        print("Type '--eq' to see symbolic expansion")
        print("Type 'exit' or press Ctrl+C to quit\n")

        while True:
            try:
                ast_to_print = False
                eq_mode = False

                line = input(">> ").strip()

                if line.endswith("--ast"):
                    ast_to_print = True
                    line = line[:-5].strip()
                elif line.endswith("--eq"):
                    eq_mode = True
                    line = line[:-4].strip()
                elif line == "exit":
                    break

                lex = lexer.Lexer(line)
                tokens = lex.tokenize()
                p = parser.Parser(tokens)
                ast = p.parseAssignment()

                if ast_to_print:
                    parser.print_ast(ast)

                elif eq_mode:
                    result = eval_eq(ast)
                    if result and ast.type not in (
                        parser.NodeType.Assignment,
                        parser.NodeType.Function,
                        parser.NodeType.Eol
                    ):
                        expr = simplify(result)
                        expr = expand(expr)
                        expr = simplify(expr)
                        print(expr)
                else:
                    result = eval_ast(ast)
                    if ast.type not in (
                        parser.NodeType.Assignment,
                        parser.NodeType.Function,
                        parser.NodeType.Eol
                    ):
                        if ast.type == parser.NodeType.Variable:
                            print(f"{ast.id} = {result}")
                        else:
                            print(f"{result}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

        print("\nThank you and goodbye!")

    else:
        if not sys.argv[1].endswith(".math"):
            raise Exception("Invalid file extension, please use '.math' files")

        with open(sys.argv[1], 'r') as f:
            for line in f:
                try:
                    line = line.strip()
                    if not line:
                        continue

                    eq_mode = False
                    if line.endswith("--eq"):
                        eq_mode = True
                        line = line[:-4].strip()

                    lex = lexer.Lexer(line)
                    tokens = lex.tokenize()
                    parse = parser.Parser(tokens)
                    ast = parse.parseAssignment()

                    if eq_mode:
                        result = eval_eq(ast)
                        if result and ast.type not in (
                            parser.NodeType.Assignment,
                            parser.NodeType.Function,
                            parser.NodeType.Eol
                        ):
                            expr = simplify(result)
                            expr = expand(expr)
                            expr = simplify(expr)
                            print(expr)
                    else:
                        result = eval_ast(ast)
                        if ast.type not in (
                            parser.NodeType.Assignment,
                            parser.NodeType.Function,
                            parser.NodeType.Eol
                        ):
                            if ast.type == parser.NodeType.Variable:
                                print(f"{ast.id} = {result}")
                            else:
                                print(f"{result}")

                except Exception as e:
                    print(f"Error: {e}")