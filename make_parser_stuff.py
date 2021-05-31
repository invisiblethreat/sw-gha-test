
names = [
    "endmarker",
]

TEMPLATE_VISITOR = """
    def visit_{name}(self, node, ctx):
        # print("{name}: %s" % (node))
        pass"""

TEMPLATE_DICT = """'{name}': self.visit_{name},"""

TEMPLATE_WALKER = """
    def visit_{name}(self, node, ctx):
        self.visitor.visit_{name}(node, ctx)
        self.visit(node)"""

for name in names:
    print(TEMPLATE_VISITOR.format(name=name))
print("")
for i, name in enumerate(names):
    if i == 0:
        print(TEMPLATE_DICT.format(name=name))
    else:
        print("            %s" % (TEMPLATE_DICT.format(name=name)))
for name in names:
    print(TEMPLATE_WALKER.format(name=name))
