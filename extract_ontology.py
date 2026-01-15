#!/usr/bin/env python3
"""
Ontological Explorer for TBP Monty Repository

This script systematically extracts all concepts from Python source files and YAML
configuration files to create a comprehensive ontological inventory of the codebase.

It extracts:
- From Python files: Classes, Functions, Methods, Constants, Enums, Protocols, TypedDicts, etc.
- From YAML files: Configuration keys, experiment types, component configurations, parameters
"""

import ast
import json
import os
from pathlib import Path
from typing import List, Dict, Set, Any
import yaml
import re


class ConceptCollector:
    """Collects and catalogs concepts from the codebase"""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.concepts: List[Dict[str, str]] = []
        self.seen_concepts: Set[str] = set()
        
    def add_concept(self, name: str, description: str, source_file: str = None):
        """Add a concept if not already seen"""
        # Create a unique key for deduplication
        key = f"{name}::{description[:100]}"
        if key not in self.seen_concepts:
            self.seen_concepts.add(key)
            concept = {
                "concept": name,
                "description": description
            }
            if source_file:
                concept["source"] = source_file
            self.concepts.append(concept)
    
    def extract_from_python_file(self, file_path: Path):
        """Extract concepts from a Python file using AST parsing"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            relative_path = str(file_path.relative_to(self.repo_root))
            
            # Extract module-level docstring
            module_doc = ast.get_docstring(tree)
            if module_doc:
                module_name = file_path.stem
                self.add_concept(
                    f"Module: {module_name}",
                    f"Python module: {module_doc[:200].strip()}",
                    relative_path
                )
            
            # Visit all nodes in the AST
            for node in ast.walk(tree):
                self._process_ast_node(node, relative_path)
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    def _process_ast_node(self, node: ast.AST, source_file: str):
        """Process an AST node and extract concept information"""
        
        # Class definitions
        if isinstance(node, ast.ClassDef):
            class_type = self._get_class_type(node)
            docstring = ast.get_docstring(node) or ""
            description = f"{class_type}: {docstring[:200].strip()}" if docstring else class_type
            
            # Add base classes info if relevant
            if node.bases:
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_names.append(base.attr)
                if base_names:
                    description += f" (inherits from: {', '.join(base_names)})"
            
            self.add_concept(node.name, description, source_file)
            
        # Function/Method definitions
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Skip private methods unless they're special methods
            if not node.name.startswith('_') or node.name.startswith('__') and node.name.endswith('__'):
                docstring = ast.get_docstring(node) or ""
                func_type = "Function" if not self._is_method(node) else "Method"
                description = f"{func_type}: {docstring[:200].strip()}" if docstring else func_type
                
                # Add parameter info
                args = [arg.arg for arg in node.args.args if arg.arg != 'self' and arg.arg != 'cls']
                if args:
                    description += f" (params: {', '.join(args[:5])}{'...' if len(args) > 5 else ''})"
                
                self.add_concept(node.name, description, source_file)
        
        # Constant assignments (module-level ALL_CAPS variables)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper() and len(target.id) > 1:
                    value_desc = self._get_value_description(node.value)
                    self.add_concept(
                        target.id,
                        f"Constant: {value_desc}",
                        source_file
                    )
    
    def _get_class_type(self, node: ast.ClassDef) -> str:
        """Determine the type of class (Enum, Protocol, ABC, dataclass, etc.)"""
        # Check decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == 'dataclass':
                    return "Dataclass"
                elif decorator.id == 'runtime_checkable':
                    return "Protocol"
        
        # Check base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in ['Enum', 'IntEnum', 'Flag', 'IntFlag']:
                    return "Enum"
                elif base.id == 'Protocol':
                    return "Protocol"
                elif base.id == 'TypedDict':
                    return "TypedDict"
                elif base.id in ['ABC', 'ABCMeta']:
                    return "Abstract Base Class"
            elif isinstance(base, ast.Attribute):
                if base.attr in ['Enum', 'Protocol', 'TypedDict', 'ABC']:
                    return f"{base.attr}"
        
        return "Class"
    
    def _is_method(self, node) -> bool:
        """Check if a function is a method (has 'self' or 'cls' as first param)"""
        if node.args.args:
            first_arg = node.args.args[0].arg
            return first_arg in ['self', 'cls']
        return False
    
    def _get_value_description(self, node: ast.AST) -> str:
        """Get a description of a value from an AST node"""
        if isinstance(node, ast.Constant):
            return f"{type(node.value).__name__} = {repr(node.value)[:50]}"
        elif isinstance(node, ast.List):
            return f"List with {len(node.elts)} elements"
        elif isinstance(node, ast.Dict):
            return f"Dict with {len(node.keys)} keys"
        elif isinstance(node, ast.Tuple):
            return f"Tuple with {len(node.elts)} elements"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"Result of {node.func.id}()"
        return "Value"
    
    def extract_from_yaml_file(self, file_path: Path):
        """Extract concepts from a YAML configuration file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML
            data = yaml.safe_load(content)
            if not data:
                return
            
            relative_path = str(file_path.relative_to(self.repo_root))
            
            # Extract configuration name from path
            config_name = self._get_config_name_from_path(file_path)
            
            # Process the YAML structure
            self._process_yaml_structure(data, config_name, relative_path)
            
        except Exception as e:
            print(f"Error parsing YAML {file_path}: {e}")
    
    def _get_config_name_from_path(self, file_path: Path) -> str:
        """Extract a meaningful configuration name from the file path"""
        # Get path relative to conf directory
        parts = file_path.parts
        if 'conf' in parts:
            conf_idx = parts.index('conf')
            relevant_parts = parts[conf_idx+1:]
            # Remove .yaml extension
            name_parts = list(relevant_parts[:-1]) + [relevant_parts[-1].replace('.yaml', '').replace('.yml', '')]
            return '/'.join(name_parts)
        return file_path.stem
    
    def _process_yaml_structure(self, data: Any, prefix: str, source_file: str, depth: int = 0):
        """Recursively process YAML structure to extract concepts"""
        if depth > 4:  # Limit recursion depth
            return
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Create concept for this configuration key
                concept_name = f"{prefix}/{key}" if prefix else key
                description = self._describe_yaml_value(key, value, depth)
                
                # Only add if it seems like a significant concept
                if self._is_significant_yaml_concept(key, value, depth):
                    self.add_concept(
                        concept_name,
                        f"Config: {description}",
                        source_file
                    )
                
                # Recurse for nested structures
                if isinstance(value, (dict, list)) and depth < 3:
                    self._process_yaml_structure(value, concept_name, source_file, depth + 1)
        
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # Process list of dicts
            for idx, item in enumerate(data[:3]):  # Limit to first 3 items
                self._process_yaml_structure(item, f"{prefix}[{idx}]", source_file, depth + 1)
    
    def _describe_yaml_value(self, key: str, value: Any, depth: int) -> str:
        """Create a description for a YAML configuration value"""
        if isinstance(value, dict):
            keys = list(value.keys())[:5]
            return f"Configuration group with keys: {', '.join(keys)}"
        elif isinstance(value, list):
            if not value:
                return "Empty list"
            elif isinstance(value[0], dict):
                return f"List of {len(value)} configuration objects"
            else:
                return f"List of {len(value)} values: {value[:3]}"
        elif isinstance(value, str):
            # Check for special patterns
            if value.startswith('_target_'):
                return f"Target class/function specification"
            elif '.' in value and len(value) < 100:
                return f"String value: {value}"
            else:
                return f"String parameter"
        elif isinstance(value, (int, float)):
            return f"Numeric parameter = {value}"
        elif isinstance(value, bool):
            return f"Boolean flag = {value}"
        else:
            return f"{type(value).__name__} value"
    
    def _is_significant_yaml_concept(self, key: str, value: Any, depth: int) -> bool:
        """Determine if a YAML key represents a significant concept"""
        # Skip very generic keys at deep levels
        generic_keys = {'name', 'value', 'type', 'id', 'label'}
        if depth > 2 and key.lower() in generic_keys:
            return False
        
        # Include if it's a dict (configuration group)
        if isinstance(value, dict):
            return True
        
        # Include if it's a list of dicts (multiple configurations)
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return True
        
        # Include important configuration parameters at reasonable depth
        if depth <= 2:
            return True
        
        # Include _target_ keys (Hydra instantiation)
        if key == '_target_':
            return True
        
        return False
    
    def collect_all_concepts(self):
        """Main method to collect all concepts from the repository"""
        print("Collecting concepts from Python files...")
        
        # Find all Python files in src/
        src_dir = self.repo_root / 'src'
        if src_dir.exists():
            python_files = list(src_dir.rglob('*.py'))
            print(f"Found {len(python_files)} Python files")
            
            for idx, py_file in enumerate(python_files, 1):
                if idx % 20 == 0:
                    print(f"  Processing Python file {idx}/{len(python_files)}")
                self.extract_from_python_file(py_file)
        
        print("\nCollecting concepts from YAML configuration files...")
        
        # Find all YAML files in conf/
        conf_dir = self.repo_root / 'conf'
        if conf_dir.exists():
            yaml_files = list(conf_dir.rglob('*.yaml')) + list(conf_dir.rglob('*.yml'))
            print(f"Found {len(yaml_files)} YAML files")
            
            for idx, yaml_file in enumerate(yaml_files, 1):
                if idx % 50 == 0:
                    print(f"  Processing YAML file {idx}/{len(yaml_files)}")
                self.extract_from_yaml_file(yaml_file)
        
        print(f"\nTotal concepts collected: {len(self.concepts)}")
        return self.concepts
    
    def save_to_json(self, output_path: str):
        """Save collected concepts to a JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.concepts, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(self.concepts)} concepts to {output_path}")


def main():
    """Main execution function"""
    repo_root = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 80)
    print("TBP Monty Ontological Explorer")
    print("=" * 80)
    print(f"\nRepository root: {repo_root}\n")
    
    collector = ConceptCollector(repo_root)
    concepts = collector.collect_all_concepts()
    
    # Save to JSON file
    output_file = os.path.join(repo_root, 'ontology_concepts.json')
    collector.save_to_json(output_file)
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    
    # Count by type
    type_counts = {}
    for concept in concepts:
        desc = concept['description']
        if ':' in desc:
            concept_type = desc.split(':')[0]
            type_counts[concept_type] = type_counts.get(concept_type, 0) + 1
    
    print("\nConcepts by type:")
    for concept_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {concept_type}: {count}")
    
    print("\n" + "=" * 80)
    print(f"Output file: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()
