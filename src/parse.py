from pathlib import Path
from lark import Lark, Tree, Token  # type: ignore


with open("src/grammar.lark", "r", encoding="utf-8") as f:
    grammar = f.read()

parser = Lark(grammar, start="start", parser="lalr", lexer="basic")


def should_parse(path: str) -> bool:
    return Path(path).suffix.lower() == ".pysc"


class Parse:
    def __init__(self):
        self.vars = {}
        self.funcs = {}
        self.max_loop_iters = 10_000

    def eval(self, node):
        return self.exec_node(node)

    def run(self, tree: Tree):
        return self.exec_node(tree)

    def exec_node(self, node):
        def _exec_stmt(stmt_node):
            if isinstance(stmt_node, Tree) and stmt_node.data == "add":
                left = stmt_node.children[0]
                if isinstance(left, Tree) and left.data == "var" and left.children:
                    name = str(left.children[0])
                    value = self.exec_node(stmt_node)
                    if name in self.vars:
                        self.vars[name]["value"] = value
                    return value
            if isinstance(stmt_node, Tree) and stmt_node.data in {"inc", "dec"}:
                self.exec_node(stmt_node)
                return None
            return self.exec_node(stmt_node)

        if isinstance(node, Token):
            if node.type == "NUMBER":
                return float(node.value)

            if node.type == "STRING":
                return node.value.strip('"')

            if node.type == "NAME":
                name = node.value
                if name in self.vars:
                    return self.vars[name]["value"]
                return name
        
        if not isinstance(node, Tree):
            return node

        if node.data == "start":
            results = []
            for child in node.children:
                results.append(_exec_stmt(child))
            return results

        if node.data == "stmt":
            return self.exec_node(node.children[0])

        if node.data == "block":
            result = None
            for child in node.children:
                result = _exec_stmt(child)
            return result

        if node.data == "num":
            return float(node.children[0].value)

        if node.data == "str":
            return str(node.children[0].value)

        if node.data == "bools":
            return bool(node.children[0].value) if node.children else bool

        if node.data == "true":
            return True

        if node.data == "false":
            return False

        if node.data == "blank":
            return None
        
        if node.data == "var":
            name = str(node.children[0])

            if name == "while":
                return None

            if name not in self.vars:
                raise ValueError(f"Undefined variable '{name}'")

            return self.vars[name]["value"]

        if node.data == "get_var":
            name = node.children[0]

            if name not in self.vars:
                raise ValueError(f"Undefined variable '{name}'")

            return self.vars[name]["value"]

        if node.data == "l_var":
            name = str(node.children[0])
            value = self.exec_node(node.children[1])
            if name in self.vars and self.vars[name].get("const"):
                raise ValueError(f"Cannot modify constant '{name}'")
            if isinstance(value, (int, float)):
                 var_type = "num"
            elif isinstance(value, str):
                var_type = "str"
            elif value is None:
                var_type = "blank"
            else:
                var_type = "unknown"

            self.vars[name] = {
                "type": var_type,
                "value": value,
                "const": False,
             }
            return None

        if node.data == "c_var":
            name = str(node.children[0])
            value = self.exec_node(node.children[1])
            if name in self.vars and self.vars[name].get("const"):
                raise ValueError(f"Cannot modify constant '{name}'")
            if isinstance(value, (int, float)):
                 var_type = "num"
            elif isinstance(value, str):
                var_type = "str"
            elif value is None:
                var_type = "blank"
            else:
                var_type = "unknown"

            self.vars[name] = {
                "type": var_type,
                "value": value,
                "const": True
             }
            return None

        if node.data == "enum":
            name = str(node.children[0])
            value = self.exec_node(node.children[1])
            self.vars[name] = {"type": "num", "value": value, "const": True}
            return None

        if node.data == "expr":
            return self.exec_node(node.children[0]) if isinstance(node.children[0], Tree) else self.exec_node(node.children[0])

        if node.data == "args":
            result = None
            for child in node.children:
                result = _exec_stmt(child)
            return result

        if node.data == "print_stmt":
            if not node.children:
                print()
                return ""

            args_node = node.children[0]
            expr_nodes = args_node.children if isinstance(args_node, Tree) else [args_node]
            parts = []
            for expr in expr_nodes:
                value = self.exec_node(expr)
                print(value, end=" ")
                parts.append(str(value))

            print()
            return " ".join(parts).strip()
        
        if node.data == "func":
            name = str(node.children[0])
            if len(node.children) == 3:
                parameters = node.children[1]
                body = node.children[2]
            else:
                parameters = None
                body = node.children[1]

            self.funcs[name] = {
                "parameters": parameters,
                "body": body,
            }
            return name

        if node.data == "parameters":
            return [self.exec_node(child) for child in node.children]

        if node.data == "param":
            # (name, type_string)
            return (str(node.children[0]), self.exec_node(node.children[1]))

        if node.data == "do_when":
            body, condition = node.children
            if self.exec_node(condition):
                return _exec_stmt(body)

            return None
        
        if node.data == "do_until":
            body, condition = node.children
            iters = 0
            last_result = None
            while not self.exec_node(condition):
                iters += 1
                if iters > self.max_loop_iters:
                    raise RuntimeError("Loop exceeded max iterations (do_until)")
                last_result = _exec_stmt(body)

            return last_result
                
        if node.data == "do_process":
            body = node.children[0]
            return _exec_stmt(body)

        # Math
        if node.data == "add":
            return self.exec_node(node.children[0]) + self.exec_node(node.children[1])

        if node.data == "sub":
            return self.exec_node(node.children[0]) - self.exec_node(node.children[1])

        if node.data == "mul":
            return self.exec_node(node.children[0]) * self.exec_node(node.children[1])

        if node.data == "div":
            return self.exec_node(node.children[0]) / self.exec_node(node.children[1])

        if node.data == "mod":
            return self.exec_node(node.children[0]) % self.exec_node(node.children[1])

        if node.data == "expo":
            return self.exec_node(node.children[0]) ** self.exec_node(node.children[1])

        if node.data == "eq":
            return self.exec_node(node.children[0]) == self.exec_node(node.children[1])

        if node.data == "ineq":
            return self.exec_node(node.children[0]) != self.exec_node(node.children[1])

        if node.data == "or_op":
            return bool(self.exec_node(node.children[0])) or bool(self.exec_node(node.children[1]))

        if node.data == "and_op":
            return bool(self.exec_node(node.children[0])) and bool(self.exec_node(node.children[1]))

        if node.data in {"check_true", "check_false"}:
            var_name = str(node.children[0])
            type_lit = self.exec_node(node.children[1])
            value = self.vars.get(var_name, {}).get("value")
            matches = False
            if type_lit == "num":
                matches = isinstance(value, (int, float))
            elif type_lit == "str":
                matches = isinstance(value, str)
            elif type_lit == "bool":
                matches = isinstance(value, bool)
            elif type_lit == "blank":
                matches = value is None
            return matches if node.data == "check_true" else (not matches)
        
        if node.data == "inc":
            name = str(node.children[0])
            self.vars[name]["value"] += 1
            return self.vars[name]["value"]

        if node.data == "dec":
            name = str(node.children[0])
            self.vars[name]["value"] -= 1
            return self.vars[name]["value"]
        
        raise ValueError(f"Unsupported Node! Check: {node.data}")



if __name__ == "__main__":
    source_path = Path("script.pysc")

    if not should_parse(str(source_path)):
        raise ValueError(f"Unsupported file type: {source_path}")

    source = source_path.read_text(encoding="utf-8")
    tree = parser.parse(source)

    import os

    # flags
    # `PYSCRIPT_TREE=1` prints the parse tree
    # `PYSCRIPT_VARS=1` prints the variable table after execution
    # - `PYSCRIPT_EXEC=0` disables execution (parse-only)
    if os.environ.get("PYSCRIPT_TREE") == "1":
        print(tree.pretty())

    if os.environ.get("PYSCRIPT_EXEC", "1") != "0":
        runtime = Parse()
        output = runtime.run(tree)

        if os.environ.get("PYSCRIPT_VARS") == "1":
            print("vars:\n", runtime.vars)

        # vertical prints
        print("PyScript:")
        if isinstance(output, list):
            for item in output:
                if item is None:
                    continue
                print(item)
        else:
            if output is not None:
                print(output)
