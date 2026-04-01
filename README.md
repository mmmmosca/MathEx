# MathEx

By not providing a file ending in `.math` you will enter the REPL.

Operations:

- +: addition
- -: subtraction
- *: multiplication
- /: division
- ^: exponentiation
- %: modulus
- \\ : square root

By using the `--ast` flag after an expression, when using the REPL, you will see the AST of the expression

## Variables

Define a variable by writing an identifier followed by an equal sign and an expression.

Example:

`var = 2+2`

calling a variable will use the value that the expression binded to it returns.
so using the previous example:

```
var

Output:
var = 4
```

There are some preexisting variables like `PI`, which returns the value of pi and `rand` which returns a positive integer from 0 to the largest practical integer (in Python).


## Functions

You can define a function by first wrting an identifier, followed by a pair of parenthesis containing the parameter of the function, then an equal sign and the expression that the function evaluates.

For example:

`f(x) = x + 2`

Then you can call a function by typing it's identifier and putting between parenthesis the argument of the function.

Both in the REPL and in the interpreter if you type `--eq` you will see what's the equation of a function.

Using the previous example:

```
f(x) --eq

Output:
x+2
```
