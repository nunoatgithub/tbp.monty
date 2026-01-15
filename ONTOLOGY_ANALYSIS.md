# Ontological Analysis of TBP Monty Repository

This directory contains the results of an automated ontological exploration of the TBP Monty codebase.

## Overview

The ontological analysis systematically extracts and catalogs all concepts from:
- **Python source files** (105 files in `src/`): Classes, Functions, Methods, Constants, Enums, Protocols, TypedDicts, etc.
- **YAML configuration files** (280 files in `conf/`): Configuration keys, experiment types, model configurations, parameter groups

## Files

### `extract_ontology.py`
Python script that performs the automated concept extraction. It uses:
- **AST parsing** for Python files to extract classes, functions, methods, constants, and their docstrings
- **YAML parsing** for configuration files to extract configuration hierarchies and parameters

### `ontology_concepts.json`
The output JSON file containing all extracted concepts. Each concept has:
- `concept`: The name/identifier of the concept
- `description`: A brief description of what it is and what it does
- `source`: The file path where the concept was found

## Statistics

Total concepts extracted: **3,352**

### Breakdown by Type:
- **Config**: 2,227 (YAML configuration concepts)
- **Method**: 437 (instance methods in classes)
- **Method (with params)**: 157 (methods with explicit parameter lists)
- **Function**: 147 (module-level functions)
- **Class**: 130 (standard Python classes)
- **Function (with params)**: 67 (functions with explicit parameter lists)
- **Protocol**: 35+ (runtime-checkable protocols and interfaces)
- **Constant**: 19 (module-level constants)
- **Dataclass**: 15 (dataclasses for data structures)
- **Other**: TypedDict, Enum, ABC (Abstract Base Classes)

## Usage

### Running the Extraction
```bash
python extract_ontology.py
```

This will:
1. Scan all Python files in `src/` directory
2. Scan all YAML files in `conf/` directory
3. Extract concepts from both
4. Save results to `ontology_concepts.json`

### Analyzing the Results

The JSON file can be used for:

1. **Identifying ontological overload**: Find concepts with similar names or descriptions that might represent the same thing
   ```bash
   jq '.[] | select(.concept | contains("Match"))' ontology_concepts.json
   ```

2. **Finding duplicated concepts**: Search for concepts that appear in multiple places
   ```bash
   jq 'group_by(.concept) | .[] | select(length > 1)' ontology_concepts.json
   ```

3. **Analyzing by module**: Filter concepts by source file or directory
   ```bash
   jq '.[] | select(.source | contains("evidence_matching"))' ontology_concepts.json
   ```

4. **Searching by description**: Find concepts related to specific functionality
   ```bash
   jq '.[] | select(.description | contains("graph"))' ontology_concepts.json
   ```

## Next Steps

Use this ontological inventory to:

1. **Identify redundant concepts**: Look for multiple concepts that serve the same purpose
2. **Find naming inconsistencies**: Spot similar concepts with different naming conventions
3. **Detect architectural issues**: Identify concepts that might be in the wrong module
4. **Create refactoring tasks**: Generate individual tasks to consolidate or rename concepts
5. **Build a data model**: Create a comprehensive data model showing relationships between concepts

## Example Queries

### Find all learning module related concepts:
```bash
jq '.[] | select(.description | contains("learning") or .concept | contains("LM"))' ontology_concepts.json
```

### Find all motor system concepts:
```bash
jq '.[] | select(.concept | contains("Motor") or .concept | contains("motor"))' ontology_concepts.json
```

### Find configuration concepts for a specific experiment:
```bash
jq '.[] | select(.source | contains("conf/experiment"))' ontology_concepts.json
```

### Count concepts by source directory:
```bash
jq -r '.[].source | split("/")[0:3] | join("/")' ontology_concepts.json | sort | uniq -c | sort -rn
```

## Notes

- The extraction is designed to be conservative and may miss some concepts (better to miss than to create false positives)
- Private methods (starting with `_`) are excluded unless they are special methods (`__init__`, `__call__`, etc.)
- YAML concepts are organized hierarchically using path notation (e.g., `experiment/config/motor_system/policy`)
- Some descriptions are truncated at 200 characters for readability
