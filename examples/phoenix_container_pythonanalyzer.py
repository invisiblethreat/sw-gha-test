import sys
# import antlr4
# from antlr4.tree.Tree import TerminalNodeImpl
from tqdm import tqdm
# from ContentAnalyzer.analyzers.python import Python3Lexer
# from ContentAnalyzer.analyzers.python import Python3Parser
# from ContentAnalyzer.analyzers.python import AnalyzerPython3Visitor
from ContentAnalyzer.analyzers.python import PythonAnalyzer
import Phoenix

def main():
    # test_filename = "./antlr/python/samples/sample5.py"

    # filename = test_filename

    blob_sum = "sha256:173d52f51227eedb7fb37472945a1e6bdf08958c0fd26fb6ec5630c16c70c549"
    container = Phoenix.db_get(Phoenix.Types.container.ContainerDocker, create=False, catch=False, blob_sum=blob_sum)

    for node in tqdm(container.files_.filter(name__endswith=".py"), desc="Parsing Python files", unit="file", miniters=1):

        tqdm.write("%s" % (node.full_path))
        # pa = PythonAnalyzer()
        # pa.analyze(node.get_content(return_as="string", decode=True))
        # tqdm.write("=" * 80)


if __name__ == "__main__":
    main()
