# import json
import esprima

from ContentAnalyzer import KeyValuePair, LineColumnLocation

def is_Identifier(node):
    if node is None:
        return False
    return node.type == "Identifier"

def is_VariableDeclarator(node):
    if node is None:
        return False
    return node.type == "VariableDeclarator"

def is_Property(node):
    if node is None:
        return False
    return node.type == "Property"

def is_ExpressionStatement(node):
    if node is None:
        return False
    return node.type == "ExpressionStatement"

def is_AssignmentExpression(node):
    if node is None:
        return False
    return node.type == "AssignmentExpression"

def is_MemberExpression(node):
    if node is None:
        return False
    return node.type == "MemberExpression"

def is_Literal(node):
    if node is None:
        return False
    return node.type == "Literal"

def is_LiteralStr(node):
    if is_Literal(node):
        return isinstance(node.value, str)
    return False

class Visitor(esprima.NodeVisitor):

    def __init__(self, line_positions=None):
        super(Visitor, self).__init__()
        self.matches = []
        self.line_positions = line_positions

    def get_matches(self):
        return self.matches.copy()

    def make_node_key_value_pair(self, node):
        if is_VariableDeclarator(node):
            key = node.id
            value = node.init
        elif is_Property(node):
            key = node.key
            value = node.value
        elif is_AssignmentExpression(node):
            value = node.right
            if is_MemberExpression(node.left):
                key = node.left.property
            elif is_Identifier(node.left):
                key = node.left
            else:
                raise TypeError("Could not determine left side node type!")
        else:
            raise TypeError("Could not determine node type!")
        return self.make_key_value_pair(key, value)

    def make_key_value_pair(self, key_node, value_node):
        key = LineColumnLocation(esprima_node=key_node, line_positions=self.line_positions)
        value = LineColumnLocation(esprima_node=value_node, line_positions=self.line_positions)
        kvp = KeyValuePair(key=key, value=value)
        self.matches.append(kvp)
        return kvp

    def visit_BlockStatement(self, node):
        # Make sure everything else gets visited:
        self.generic_visit(node)

    def visit_AssignmentExpression(self, node):
        if is_LiteralStr(node.right):
            self.make_node_key_value_pair(node)
        else:
            print("", end='')
        self.generic_visit(node)

    # def visit_ExpressionStatement(self, node):
    #     if is_AssignmentExpression(node.expression) and is_LiteralStr(node.expression.right):
    #         self.make_node_key_value_pair(node)
    #     else:
    #         print("", end='')
    #     self.generic_visit(node)

    def visit_VariableDeclarator(self, node):
        if is_LiteralStr(node.init):
            self.make_node_key_value_pair(node)
        else:
            print("", end='')
        self.generic_visit(node)

    def visit_Property(self, node):
        # print(node)
        if is_LiteralStr(node.value):
            self.make_node_key_value_pair(node)
        else:
            print("", end='')
        self.generic_visit(node)

def main():
    """Main."""

    # sample1
    # 'name' => 'netsil-very-unique-bucket-name-for-backup-tests'
    # 'accessKey' => 'AKIAIDATIAGYOVGBZVWA'
    # 'secretKey' => 'aC2gJ/Nvs3JkvldmNvwIxx7e6RCHiAN2/JqlbvlI'
    # 'NETSIL_BUILD_BRANCH' => 'master'
    # 'NETSIL_COMMIT_HASH' => 'e2d90fc'
    # 'NETSIL_VERSION_NUMBER' => '1.0.8'
    # 'template' => '{database}_{NETSIL_BUILD_BRANCH}_{NETSIL_VERSION_NUMBER}'

    # sample2
    # 'message' => 'Invalid email address.'
    # 'message' => 'This field is required.'
    # 'message' => 'Passwords do not match.'
    # 'storageBaseKey' => 'druid-segments'
    # 'unit' => 'days'
    # 'type' => 'post'
    # 'url' => 'auth-api/settings/storage'
    # 'content-type' => 'application/json'
    # 'message' => 'reconfigure'
    # 'type' => 'post'
    # 'url' => 'auth-api/settings/feedback'
    # 'content-type' => 'application/json'
    # 'method' => 'POST'
    # 'url' => 'license/register'
    # 'dataType' => 'json'
    # 'msg' => 'Request timed out.'
    # 'msg' => 'You have an existing Epoch account.<br>Please <a href="https://lm.epoch.nutanix.com" target="_blank">login</a> to generate your license key.'

    # sample3
    # 'API' => 'api_key'
    # 'APPLICATION' => 'app_key'

    # sample4
    # 'CLOUD_PROVIDER_ACCOUNTS_URL' => '/up-api/cloud-provider-accounts'
    # 'CLOUD_ACCOUNT_RESOURCES' => '/up-api/cloud-account-resources'
    # 'CLOUD_ACCOUNT_COUNTS_RESOURCES' => '/amazon/resources'

    # sample5
    # 'runtime' => 'server'
    # 'name' => 'epoch.frontend'
    # 'secret' => 'q0fpgi3dkcm79Dk'
    # 'x-forwarded-proto' => 'https'
    # 'connType' => ''
    # 'connType' => 'query'
    # 'connType' => 'live'
    # 'connType' => 'messages'
    # 'connType' => 'api/vx/query'
    # 'Content-Type' => 'application/json'
    # 'host' => '127.0.0.1'

    # sample6
    # 'heh' => 'hah'
    # 'password' => 'hunter2'

    import sys
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "./experimental/samples/sample6.js"
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Will generate line number to starting offset for content
    positions = []
    total = 0
    for n in content.split('\n'):
        # We add 1 here to accomodate for the '\n' that we
        # removed by splitting
        # print(i + 1, total, len(n) + 1)
        positions.append(total)
        total += len(n) + 1

    visitor = Visitor(line_positions=positions)

    tree = esprima.parse(content, delegate=visitor, options={'loc': True, 'tolerant': True})

    visitor.visit(tree)

    for n in visitor.get_matches():
        print("'%s' => '%s'" % (n.get_key(), n.get_value()))

    print("breakpoint")

if __name__ == "__main__":
    main()


