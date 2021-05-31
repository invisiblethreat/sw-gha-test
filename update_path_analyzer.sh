#!/bin/bash

cd ContentAnalyzer/analyzers/path
java -jar /usr/local/lib/antlr-4.7.2-complete.jar -Dlanguage=Python3 PathGrammar.g4
