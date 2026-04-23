from lark import Lark, Transformer

with open("src/parser.lark", "r", encoding="utf-8") as f:
    grammar = f.read()

from pathlib import Path

def should_parse(path: str) -> bool:
    return Path(path).suffix.lower() == ".pysc"

class Run(Transformer):
    def __init__(self):
        self.vars = {}
    
    def number(self, items):
        return int(items[0])

    def var(self, items):
        name = str(items[0])
        return self.vars[name]

    def assign(self, items):
        name = str(items[0])
        value = items[1]
        self.vars[name] = value
        return value
    
    def print_stmt(self, items):
        value = items[0]
        print(value)
        return value
    
    def do_when(self, items):
        body, condition = items
        if condition:
            for stmt in body:
                

        
