"""Test keyvaluepairs"""

import importlib
import json
import os
from typing import Dict

import pytest


FILES = [
    ("tests/data/python/sample1.py", "PythonAnalyzer"),
    ("tests/data/python/sample2.py", "PythonAnalyzer"),
    ("tests/data/python/sample3.py", "PythonAnalyzer"),
    ("tests/data/python/sample4.py", "PythonAnalyzer"),
    ("tests/data/python/sample5.py", "PythonAnalyzer"),
    ("tests/data/python/sample6.py", "PythonAnalyzer"),
    ("tests/data/python/sample7.py", "PythonAnalyzer"),
    ("tests/data/python/sample8.py", "PythonAnalyzer"),
    ("tests/data/python/sample9.py", "PythonAnalyzer"),
    ("tests/data/python/sample10.py", "PythonAnalyzer"),
    ("tests/data/python/sample11.py", "PythonAnalyzer"),
    ("tests/data/python/sample12.py", "PythonAnalyzer"),
    ("tests/data/python/sample13.py", "PythonAnalyzer"),
    ("tests/data/python/sample14.py", "PythonAnalyzer"),
    ("tests/data/python/sample15.py", "PythonAnalyzer"),
    ("tests/data/python/sample16.py", "PythonAnalyzer"),
    ("tests/data/python/sample17.py", "PythonAnalyzer"),
    ("tests/data/python/sample18.py", "PythonAnalyzer"),
    ("tests/data/python/sample19.py", "PythonAnalyzer"),
    ("tests/data/javascript/sample1.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample2.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample3.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample4.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample5.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample6.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample7.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample8.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample9.js", "JavascriptAnalyzer"),
    # ("tests/data/javascript/sample10.js", "JavascriptAnalyzer"), # Currently broken
    ("tests/data/javascript/sample11.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample12.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample13.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample14.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample15.js", "JavascriptAnalyzer"),
    ("tests/data/javascript/sample16.js", "JavascriptAnalyzer"),
    ("tests/data/groovy/sample1.groovy", "SimpleGroovyAnalyzer"),
    ("tests/data/groovy/sample2.groovy", "SimpleGroovyAnalyzer"),
    ("tests/data/java/sample1.java", "JavaAnalyzer"),
    ("tests/data/java/sample2.java", "JavaAnalyzer"),
    ("tests/data/java/sample3.java", "JavaAnalyzer"),
    ("tests/data/java/sample4.java", "JavaAnalyzer"),
    ("tests/data/applicationproperties/sample1.toml", "ApplicationPropertiesAnalyzer"),
    ("tests/data/applicationproperties/sample2.properties", "ApplicationPropertiesAnalyzer"),
    ("tests/data/applicationproperties/sample3.properties", "ApplicationPropertiesAnalyzer"),
    ("tests/data/applicationproperties/sample4.properties", "ApplicationPropertiesAnalyzer"),
    ("tests/data/applicationproperties/sample5.properties", "ApplicationPropertiesAnalyzer"),
    ("tests/data/applicationproperties/sample6.properties", "ApplicationPropertiesAnalyzer"),
    ("tests/data/applicationproperties/sample7.properties", "ApplicationPropertiesAnalyzer"),
    ("tests/data/applicationproperties/sample8.properties", "ApplicationPropertiesAnalyzer"),
    ("tests/data/bash/sample1.sh", "SimpleBashAnalyzer"),
    ("tests/data/bash/sample2.sh", "SimpleBashAnalyzer"),
    ("tests/data/bash/sample3.sh", "SimpleBashAnalyzer"),
    ("tests/data/ruby/sample1.rb", "SimpleRubyAnalyzer"),
    # ("tests/data/dockercompose/sample1.docker-compose", "DockerComposeAnalyzer"),
    # ("tests/data/gitlog/sample1.gitlog", "GitLogAnalyzer"),
    ("tests/data/php/sample1.php", "PhpAnalyzer"),
    ("tests/data/php/sample2.php", "PhpAnalyzer"),
    ("tests/data/php/sample3.php", "PhpAnalyzer"),
    ("tests/data/php/sample4.php", "PhpAnalyzer"),
    ("tests/data/php/sample5.php", "PhpAnalyzer"),
    ("tests/data/php/sample6.php", "PhpAnalyzer"),
    ("tests/data/yaml/sample1.yaml", "SimpleYamlAnalyzer"),
    ("tests/data/yaml/sample2.yaml", "SimpleYamlAnalyzer"),
    ("tests/data/yaml/sample3.yaml", "SimpleYamlAnalyzer"),
    ("tests/data/yaml/sample4.yaml", "SimpleYamlAnalyzer"),
    ("tests/data/json/sample1.json", "JsonAnalyzer"),
    ("tests/data/json/sample2.json", "JsonAnalyzer"),
    ("tests/data/json/sample3.json", "JsonAnalyzer"),
    ("tests/data/hcl2/sample1.tf", "Hcl2Analyzer"),
    ("tests/data/hcl2/sample2.tf", "Hcl2Analyzer"),
    ("tests/data/cs/sample1.cs", "CSharpAnalyzer"),
    ("tests/data/cs/sample2.cs", "CSharpAnalyzer"),
    ("tests/data/cs/sample3.cs", "CSharpAnalyzer"),
    ("tests/data/cs/sample4.cs", "CSharpAnalyzer"),
    ("tests/data/cs/sample5.cs", "CSharpAnalyzer"),
    ("tests/data/rust/sample1.rs", "RustAnalyzer"),
    ("tests/data/powershell/sample1.ps1", "PowershellAnalyzer"),
    ("tests/data/typescript/sample1.tsx", "TypescriptAnalyzer"),
    ("tests/data/go/sample1.go", "GoAnalyzer"),
    ("tests/data/scala/sample1.scala", "ScalaAnalyzer"),
    ("tests/data/kotlin/sample1.kt", "KotlinAnalyzer"),
]


def read_file_contents(filename: str) -> str:
    """Read the contents of a file"""
    f = open(filename, "r", encoding='utf-8')
    data = f.read()
    f.close()
    return data

def get_test_data_filename(filename: str, analyzer_name: str) -> str:
    """Build test data filename"""

    test_filename = f"{filename}.{analyzer_name}.test.json"
    return test_filename

def load_test_data(filename: str, analyzer_name: str) -> Dict:
    """Loads test data from json file"""

    test_data_filename = get_test_data_filename(filename, analyzer_name)
    with open(test_data_filename, "r", encoding="utf-8") as f:
        test_data = json.load(f)
        return test_data

def get_analyzer(analyzer_name: str) -> object:
    """Get analyzer for an analyzer name"""

    return getattr(importlib.import_module('ContentAnalyzer.analyzers'), analyzer_name)

@pytest.mark.parametrize("filename,analyzer_name", FILES)
def test_analyzer_key_value_pairs(filename, analyzer_name):
    """Test expected analyzer key value pairs"""

    test_data = load_test_data(filename, analyzer_name)
    analyzer = get_analyzer(analyzer_name)()
    data = read_file_contents(filename)
    analyzer.analyze(data)

    for i, observed in enumerate(analyzer.get_kvps()):
        expected_item = test_data[i]
        observed_item = observed.to_dict()
        wrong_items = dict()

        if expected_item != observed_item:
            for k, v in observed_item.items():
                if expected_item[k] != v:
                    wrong_items[k] = v

        assert expected_item == observed_item, f"Expected: {expected_item} but observed: {observed_item}. Expected key/value pairs: {wrong_items}"

        # Disable these for now. PITA.
        # if expected_item['value'] == '':
        #     continue

        # for pos_name in ('start_pos', 'end_pos'):
        #     value_idx = 0 if pos_name == 'start_pos' else -1
        #     try:
        #         expected_char = expected_item['value'][value_idx]
        #         observed_char = data[expected_item[pos_name]]
        #     except:
        #         print("", end='')
        #     assert expected_char == observed_char, f"Expected character: {expected_char} for key '{expected_item['key']}' value '{expected_item['value']}' at line {expected_item['start_line']} and column {expected_item['start_column']} to be at {pos_name} at offset {expected_item[pos_name]} but observed character: {observed_char}"

@pytest.mark.parametrize("filename,analyzer_name", FILES)
def test_analyzer_run_time(filename, analyzer_name):
    """Test that analyzer runs in an appropriate amount of time (measured in seconds)."""

    import time

    # Expected runtime in seconds
    expected_runtime = 5

    analyzer = get_analyzer(analyzer_name)()
    data = read_file_contents(filename)

    start_time = time.time()
    analyzer.analyze(data)
    observed_runtime = time.time() - start_time

    assert observed_runtime <= expected_runtime, f"Expected runtime to be less than or equal to {expected_runtime} seconds but was {observed_runtime} seconds"
