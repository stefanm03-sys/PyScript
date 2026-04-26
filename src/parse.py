from ast import parse
from numbers import Number
from pathlib import Path
import token
from lark import Lark, Tree, Token, Transformer # type: ignore


with open("src/grammar.lark", "r", encoding="utf-8") as f:
    grammar = f.read()
parser = Lark(grammar, start="start", parser="lalr")


def should_parse(path: str) -> bool:
    return Path(path).suffix.lower() == ".pysc"


class Parse:
    def __init__(self):
        self.vars = {}
        self.funcs = {}

    def run(self, tree: Tree):
        return self.exec_node(tree)

    def exec_node(self, node):

        if isinstance(node, Tree) and len(node.children) == 1:
                return self.exec_node(node.children[0])

        if isinstance(node, Token):
            if node.type == "NUMBER":
                return float(node.value)
            if node.type == "NAME":
                name = str(node)
                if name in self.vars:
                    return self.vars[name]["value"]
                raise ValueError(f"Undefined Variable! Check: '{name}'")
            
        
        if not isinstance(node, Tree):
            return node

        if node.data == "start":
            result = None
            for child in node.children:
                result = self.exec_node(child)
            return result

        if node.data == "stmt":
            return self.exec_node(node.children[0])

        if node.data == "block":
            result = None
            for child in node.children:
                result = self.exec_node(child)
            return result

        if node.data == "num":
            return self.exec_node(node.children[0])

        if node.data == "bools":
            return self.exec_node(node.children[0])

        if node.data == "str":
            return self.exec_node(node.children[0])

        if node.data == "true":
            return self.exec_node(node.children[0])

        if node.data == "false":
            return self.exec_node(node.children[0])
            
        if node.data == "blank":
            return self.exec_node(node.children[0])
        
        if node.data == "var":
            name, value = str(node.children[0]), self.exec_node(node.children[1])
            self.vars[name] = {
                "value": value,
            }
            print(value)

        if node.data == "get_var":
            name = str(node.children[0])
            return self.vars[name]["value"]

        if node.data == "l_var":
            name, value = str(node.children[0]), self.exec_node(node.children[1])
            
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
            print(self.vars[name]["value"])
            return True

        if node.data == "c_var":
            name = str(node.children[0])
            value = self.exec_node(node.children[1])
            print("Stored:", name, value)
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
            print(self.vars[name]["value"])
            return True

        if node.data == "expr":
            return self.exec_node(node.children[0])

        if node.data == "args":
            return [self.exec_node(node.children) for child in node.children]

        if node.data == "print_stmt":
            if not node.children:
                print()
                return None

            args_node = node.children[0]

            for expr in args_node.children:
                value = self.exec_node(expr)

                while isinstance(value, Tree):
                    value = self.exec_node(value.children[0])

                    print(value, end=" ")

            print()
            return None
        
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
            return None

        if node.data == "do_when":
            body, condition = node.children
            if self.exec_node(condition):
                return self.exec_node(body)
            return None
        
        if node.data == "do_until":
            body, condition = node.children[0], node.children[1]
            while not self.exec_node(condition):
                result = self.exec_node(body)
                if self.exec_node(condition):
                    return result
                
        if node.data == "do_process":
            body= node.children[0]
            return self.exec_node(body)

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

        if node.data == "eq":
            return self.exec_node(node.children[0]) == self.exec_node(node.children[1])

        if node.data == "ineq":
            return self.exec_node(node.children[0]) != self.exec_node(node.children[1])
        
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
    # print(repr(source))
    print(tree.pretty())

    runtime = Parse()
    output = runtime.run(tree)
    print("vars:", "\n", runtime.vars)
    print("PyScript:", "\n", output)