from ast import parse
from numbers import Number
from pathlib import Path
import token
from lark import Lark, Tree, Token # type: ignore


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
        if isinstance(node, Token):
            if node.type == "NUMBER":
                return float(node)
            if node.type == "NAME":
                return str(node)
            raise ValueError(f"Unsupported token: {node.type}")

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
            return Number

        if node.data == "bools":
            return bool

        if node.data == "str":
            return str

        if node.data == "true":
            return True

        if node.data == "false":
            return False
            
        if node.data == "blank":
            return None
        
        if node.data == "var":
            name, value = str(node.children[0]), self.exec_node(node.children[1])
            self.vars[name] = value
            return value

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
            print(value)

        if node.data == "c_var":
            name = str(node.children[0])
            value = self.exec_node(node.children[1])
            print("Stored:", name, value)
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

            print(value)
        
        if node.data == "args":
            return [self.exec_node(child) for child in node.children]

        if node.data == "print_stmt":
            if not node.children:
                print()
                return None
            else:
                values = self.exec_node(node.children[0])
                print(values)
        
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
            while True:
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

        # raise ValueError(f"Unsupported node: {node.data}")


if __name__ == "__main__":
    source_path = Path("script.pysc")

    if not should_parse(str(source_path)):
        raise ValueError(f"Unsupported file type: {source_path}")

    source = source_path.read_text(encoding="utf-8")
    tree = parser.parse(source)
    # print(repr(source))
    # print(tree.pretty())
    runtime = Parse()
    runtime.run(tree)
    print("vars:","\n", runtime.vars)
    output = Parse().run(tree)
    print("PyScript:", "\n", output)
