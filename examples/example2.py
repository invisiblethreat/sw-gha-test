from slimit.lexer import Lexer

KEY_WORDS = {
    'user': 'credential',
    'pass': 'credential',
    'host': 'enumeration',
    '_ip': 'enumeration',
    'ip_': 'enumeration',
    'secret': 'credential',
    'key': 'credential',
    # '_id': 'credential',
    'token': 'credential',
    'code': 'credential',
    'auth': 'credential',
    'root': 'credential',
    'endpoint': 'enumeration',
    'url': 'enumeration',
    'uri': 'enumeration',
    'connection': 'enumeration',
    'slack': 'credential',
    'secure': 'credential',
}

# filename = "/home/terryrodery/arista/alab/bundle/src/mock/handlers/Cloud/index.js"
# filename = "/home/terryrodery/arista/alab/bundle/src/mock/handlers/Cloud/cloud-status-data-azure.json"
filename = "/home/terryrodery/arista/alab/bundle/src/constants/app.js"
with open(filename, "r", encoding='utf-8') as f:
    text = f.read()

tokens = {
    'ID': [],
    'STRING': [],
    'NUMBER': [],
}

lexer = Lexer()
lexer.input(text)
# grab_next = False
for token in lexer:
    # if grab_next:
    #     if token.type not in tokens:
    #         tokens[token.type] = []
    #     tokens[token.type].append(token)
    #     grab_next = False
    #     continue
    if token.type in ('ID', 'STRING', 'NUMBER'):
        tokens[token.type].append(token)
        # if token.type == "ID":
        #     grab_next = True

# for k, v in tokens.items():
#     print("=" * 80)
#     print(k)
#     for token in v:
#         print(token)

print("=" * 80)
print("=" * 80)
for k, v in tokens.items():
    print("=" * 80)
    print(k)
    for token in v:
        for word in KEY_WORDS:
            if word in token.value.lower():
                print(token)
                continue

print("breakpoint")
