"""Build test data"""

import importlib
import json
import os
import re
from typing import Dict, List

ANALYZER_EXTENSION_MAPPING = {
    'py': 'PythonAnalyzer',
    'js': 'JavascriptAnalyzer',
    'jsx': 'JavascriptAnalyzer',
    'groovy': 'SimpleGroovyAnalyzer',
    'rb': 'SimpleRubyAnalyzer',
    'json': 'JsonAnalyzer',
    'yml': 'SimpleYamlAnalyzer',
    'yaml': 'SimpleYamlAnalyzer',
    'java': 'JavaAnalyzer',
    'properties': 'ApplicationPropertiesAnalyzer',
    'conf': 'ApplicationPropertiesAnalyzer',
    'cfg': 'ApplicationPropertiesAnalyzer',
    'toml': 'ApplicationPropertiesAnalyzer',
    'ini': 'ApplicationPropertiesAnalyzer',
    'sh': 'SimpleBashAnalyzer',
    'php': 'PhpAnalyzer',
    'docker-compose': 'DockerComposeAnalyzer',
    'gitlog': 'GitLogAnalyzer',
    'tf': 'Hcl2Analyzer',
    'rs': 'RustAnalyzer',
    'tsx': 'TypescriptAnalyzer',
    'ts': 'TypescriptAnalyzer',
    'scala': 'ScalaAnalyzer',
    'kt': 'KotlinAnalyzer',
    'ps1': 'PowershellAnalyzer',
    'go': 'GoAnalyzer',
    'cs': 'CSharpAnalyzer',
}


def read_file_contents(filename: str) -> str:
    """Read the contents of a file"""
    f = open(filename, "r", encoding='utf-8')
    data = f.read()
    f.close()
    return data

def get_test_data_filename(filename: str, analyzer_name: str) -> str:
    """Build test data filename"""

    # parts = filename.split('.')
    test_filename = f"{filename}.{analyzer_name}.test.json"
    return test_filename

def write_test_data(source_filename: str, analyzer_name: str, data: List[Dict]) -> Dict:
    """Writes test data to json file"""

    test_data_filename = get_test_data_filename(source_filename, analyzer_name)
    with open(test_data_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=False, indent=2)

def get_analyzer(analyzer_name: str) -> object:
    """Get analyzer for an analyzer name"""

    return getattr(importlib.import_module('ContentAnalyzer.analyzers'), analyzer_name)

def get_analyzer_name_from_filename(filename: str) -> str:
    """Get analyzer name from a filename"""

    extension = os.path.basename(filename).split('.')[-1]

    analyzer_name = ANALYZER_EXTENSION_MAPPING[extension]
    return analyzer_name

def process_file(filename: str, analyzer_name: str) -> None:
    """Process a file using an analyzer name"""

    print(f"Analyzing file {filename} with analyzer {analyzer_name}...")
    analyzer = get_analyzer(analyzer_name)()
    data = read_file_contents(filename)
    analyzer.analyze(data)

    print(f"Serializing KeyValuePairs...")
    test_data = [kvp.to_dict() for kvp in analyzer.get_kvps()]
    test_data_filename = get_test_data_filename(filename, analyzer_name)
    print(f"Serialized {len(test_data)} KeyValuePairs")

    print(f"Writing test data containg {len(test_data)} KeyValuePairs to {test_data_filename}...")
    write_test_data(filename, analyzer_name, test_data)

    print("Done!")

def process_directory(path: str, analyzer_name: str, catch: bool = True) -> None:
    """Process a directory using an analyzer"""

    _, _, files = list(os.walk(path))[0]

    for file_ in files:
        if re.match(r"^sample[0-9]+\.[\w\-\_]+$", file_):
            file_path = f"{path}/{file_}"
            if catch:
                try:
                    process_file(file_path, analyzer_name)
                except Exception as e: # pylint: disable=broad-except,unused-variable
                    print(f"ERROR: Received Exception while processing {file_path}:\n{str(e)}")
            else:
                process_file(f"{file_path}", analyzer_name)


def main():
    """Main."""

    # Do a specific file
    # import sys
    # filename = sys.argv[1]
    # filename = 'tests/data/python/sample2.py'
    # if len(sys.argv) > 2:
    #     analyzer_name = sys.argv[2]
    # else:
    #     analyzer_name = get_analyzer_name_from_filename(filename)
    # process_file(filename, analyzer_name)

    # Do an entire directory
    path = "tests/data/cs"
    analyzer_name = "CSharpAnalyzer"
    process_directory(path, analyzer_name, catch=False)

if __name__ == "__main__":
    main()
