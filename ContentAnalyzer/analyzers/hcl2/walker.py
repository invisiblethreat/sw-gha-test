"""walker"""

from typing import List, Dict, Tuple, Callable, Union, Iterable, Any
from lark.tree import Tree
from ContentAnalyzer.analyzers.hcl2 import parser

def gen_find_pred(pred):
    return lambda x: isinstance(x, Tree) and x.data == pred

# pylint: disable=no-value-for-parameter
def add_tree_methods(tree: Tree) -> Tree:

    def get_pred(self, name: str) -> Tree:
        """Get Predicate"""
        preds = [add_tree_methods(n) for n in self.find_pred(gen_find_pred(name))]
        return preds

    tree.get_pred = get_pred.__get__(tree) # type: ignore[attr-defined]

    return tree
# pylint: enable=no-value-for-parameter


def get_child(tree, kind: str, position: int, tree_kind: str = None, parent_children_count: int = None, child_children_count: int = None):
    if tree_kind is not None:
        if tree.data != tree_kind:
            raise TypeError(f"Tree is not '{tree_kind}' but is {tree.data}")
    if isinstance(parent_children_count, int):
        if len(tree.children) != parent_children_count:
            raise ValueError(f"{tree.data} has {len(tree.children)} but should have only {parent_children_count} child/children")
    child = tree.children[position]
    if child.data != kind:
        raise TypeError(f"Child at position {position} is not '{kind}' but is {child.data}")
    if isinstance(child_children_count, int):
        if len(child.children) != child_children_count:
            raise ValueError(f"{child.data} has {len(child.children)} but should have only {child_children_count} child/children")
    return child

def check_child_kind_and_position(tree: Tree, children_parameters: List[Dict]):
    allowed_children_count = len(children_parameters)
    if len(tree.children) != allowed_children_count:
        raise ValueError(f"'{tree.data}' has {len(tree.children)} but should have only {allowed_children_count} child/children")
    for child_parameter in children_parameters:
        child = tree.children[child_parameter["position"]]
        if child.data != child_parameter["kind"]:
            raise TypeError(f"Child at position {child_parameter['position']} is not '{child_parameter['kind']}' but is {child.data}")
        if "children_count" in child_parameter and len(child.children) != child_parameter["children_count"]:
            raise ValueError(f"{child.data} has {len(child.children)} but should have only {child_parameter['children_count']} child/children")
    return True

def check_attribute_for_simple_assignment(tree):
    attribute_children = [
        {
            "kind": "identifier",
            "position": 0,
            "children_count": 1,
        },
        {
            "kind": "expr_term",
            "position": 1,
            "children_count": 1,
        },
        # TODO: May need to ignore new lines or comments here?
        {
            "kind": "new_line_or_comment",
            "position": 2,
        },
    ]
    try:
        check_child_kind_and_position(tree, attribute_children)
        expr_term = get_child(tree, "expr_term", 1)
        if not check_expr_term_for_single_string_lit(expr_term):
            return False
        return True
    except:
        return False

def check_object_elem_for_simple_assignment(tree):
    object_elem_children = [
        {
            "kind": "identifier",
            "position": 0,
            "children_count": 1,
        },
        {
            "kind": "expr_term",
            "position": 1,
            "children_count": 1,
        },
    ]
    try:
        check_child_kind_and_position(tree, object_elem_children)
        expr_term = get_child(tree, "expr_term", 1)
        if not check_expr_term_for_single_string_lit(expr_term):
            return False
        return True
    except:
        return False

def check_expr_term_for_single_string_lit(tree):
    expr_term_children = [
        {
            "kind": "string_lit",
            "position": 0,
            "children_count": 1,
        },
    ]
    try:
        check_child_kind_and_position(tree, expr_term_children)
        return True
    except:
        return False

def get_key_value_pair_variable_string_assignment(tree):
    # key_value_pairs: List[Tuple[Tree, Tree]] = list()
    key_value_pairs: List[Dict] = list()

    attributes = tree.get_pred("attribute")
    for attribute in attributes:
        if check_attribute_for_simple_assignment(attribute):
            identifier = get_child(attribute, "identifier", 0, tree_kind="attribute", child_children_count=1)
            expr_term = get_child(attribute, "expr_term", 1, tree_kind="attribute", child_children_count=1)
            string_lit = get_child(expr_term, "string_lit", 0, tree_kind="expr_term", child_children_count=1)
            key_dict = make_position_dict(identifier, value=identifier.children[0])
            value_dict = make_position_dict(string_lit, value=string_lit.children[0], start_offset=1, end_offset=-1)
            key_value_pair = (key_dict, value_dict)
            key_value_pairs.append(key_value_pair)

    object_elems = tree.get_pred("object_elem")
    for object_elem in object_elems:
        if check_object_elem_for_simple_assignment(object_elem):
            identifier = get_child(object_elem, "identifier", 0, tree_kind="object_elem", child_children_count=1)
            expr_term = get_child(object_elem, "expr_term", 1, tree_kind="object_elem", child_children_count=1)
            string_lit = get_child(expr_term, "string_lit", 0, tree_kind="expr_term", child_children_count=1)
            key_dict = make_position_dict(identifier, value=identifier.children[0])
            value_dict = make_position_dict(string_lit, value=string_lit.children[0], start_offset=1, end_offset=-1)
            key_value_pair = (key_dict, value_dict)
            key_value_pairs.append(key_value_pair)

    return key_value_pairs

# def make_key_value_pair_dicts(kvp_tuples: List[Tuple[Tree, Tree]]) -> List[Dict]:
def make_key_value_pair_dicts(kvp_dicts: List[Tuple[Dict, Dict]]) -> List[Dict]:
    kvps: List[Dict] = list()
    for key_dict, value_dict in kvp_dicts:
        kvp_dict = make_kvp_position_dict(key_dict, value_dict)
        kvps.append(kvp_dict)
    return kvps

def make_position_dict(tree: Tree, value: str = None, start_offset: int = None, end_offset: int = None) -> Dict:
    """Make position dict for a Tree"""

    if value is None:
        value = str(tree)
    else:
        value = str(value)

    start_pos = tree.meta.start_pos
    end_pos = tree.meta.end_pos
    # length = len(value)
    start_column = tree.column
    end_column = tree.end_column

    if isinstance(start_offset, int):
        start_pos += start_offset
        start_column += start_offset
    if isinstance(end_offset, int):
        end_pos += end_offset
        end_column += end_offset

    position = {
        'value': value,
        'start_pos': start_pos,
        'end_pos': end_pos,
        'start_column': start_column,
        'end_column': end_column,
        'start_line': tree.meta.line,
        'end_line': tree.meta.end_line,
    }

    return position

def make_kvp_position_dict(key_dict: Dict, value_dict: Dict) -> Dict:
    """Make kvp position dict"""

    position = {
        'key': key_dict['value'],
        'value': value_dict['value'],
        'start_pos': value_dict['start_pos'],
        'end_pos': value_dict['end_pos'],
        'start_line': value_dict['start_line'],
        'end_line': value_dict['end_line'],
        'start_column': value_dict['start_column'],
        'end_column': value_dict['end_column'],
    }
    return position

def read_pos_from_data(data: str, kvp: Dict):
    return data[kvp['start_pos']:kvp['end_pos']]

def walk(text: str) -> List[Dict]:
    tree = parser.parse(text)
    add_tree_methods(tree)
    kvp_dicts = get_key_value_pair_variable_string_assignment(tree)
    kvps = make_key_value_pair_dicts(kvp_dicts)
    return kvps

def main():
    """Main."""

    # filename = "test/helpers/terraform-config/backend.tf"
    # filename = "test/helpers/terraform-config/cloudwatch.tf"
    # filename = "test/helpers/terraform-config/data_sources.tf"
    # filename = "test/helpers/terraform-config/iam.tf"
    # filename = "test/helpers/terraform-config/route_table.tf"
    # filename = "test/helpers/terraform-config/s3.tf"
    # filename = "test/helpers/terraform-config/variables.tf"
    # filename = "test/helpers/terraform-config/vars.auto.tfvars"
    files = [
        # "test/helpers/terraform-config/backend.tf",
        # "test/helpers/terraform-config/cloudwatch.tf",
        # "test/helpers/terraform-config/data_sources.tf",
        # "test/helpers/terraform-config/iam.tf",
        # "test/helpers/terraform-config/route_table.tf",
        # "test/helpers/terraform-config/s3.tf",
        # "test/helpers/terraform-config/variables.tf",
        # "test/helpers/terraform-config/vars.auto.tfvars",
        "sample1.tf",
    ]
    for filename in files:
        with(open(filename, 'r', encoding='utf-8')) as f:
            data = f.read()

        tree = hcl2.loads(data)
        add_tree_methods(tree)
        kvp_dicts = get_key_value_pair_variable_string_assignment(tree)
        kvps = make_key_value_pair_dicts(kvp_dicts)

        for kvp in kvps:
            # print(f"{filename} - {kvp['key']} => {kvp['value']} ({read_pos_from_data(data, kvp)})")
            # print(f"{filename} - {kvp['key']} => {kvp['value']}")
            print(f"{kvp['key']} => {kvp['value']}")

        print("", end='')
    print("", end='')

if __name__ == "__main__":
    main()
