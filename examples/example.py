from slimit.lexer import Lexer

# filename = "/home/terryrodery/arista/alab/bundle/src/mock/handlers/Cloud/index.js"
filename = "/home/terryrodery/arista/alab/bundle/src/mock/handlers/Cloud/cloud-status-data-azure.json"
# filename = "/home/terryrodery/arista/alab/bundle/src/constants/app.js"
with open(filename, "r", encoding='utf-8') as f:
    text = f.read()

tokens = {
    'ID': [],
    'STRING': [],
    'NUMBER': [],
}

lexer = Lexer()
lexer.input(text)
for token in lexer:
    print(token)


print("breakpoint")
