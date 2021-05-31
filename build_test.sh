#!/bin/bash

echo "Building test for ${@#}"
OUTPUT_FILENAME=`python3 tests/build_template.py ${1} ${2} ${3} ${4} 2>&1 | grep -P "(OUTPUT_FILENAME:)" | cut -d' ' -f 2`
echo "Source file: ${OUTPUT_FILENAME}"
echo "Destination file: tests/${OUTPUT_FILENAME}"
mv ${OUTPUT_FILENAME} tests/${OUTPUT_FILENAME}
