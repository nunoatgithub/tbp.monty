#!/usr/bin/env python3
"""
Ontological Analysis Helper

This script provides utilities to analyze the ontology_concepts.json file
and identify potential issues like:
- Duplicate or similar concept names
- Ontological overload (too many concepts in one area)
- Potential redundancies
"""

import json
from collections import defaultdict, Counter
from pathlib import Path
import difflib


def load_concepts(file_path='ontology_concepts.json'):
    """Load concepts from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_similar_concepts(concepts, similarity_threshold=0.8):
    """Find concepts with similar names"""
    print("=" * 80)
    print("Similar Concept Names (potential duplicates/redundancies)")
    print("=" * 80)
    
    concept_names = [c['concept'] for c in concepts]
    similar_groups = []
    
    for i, name1 in enumerate(concept_names):
        similar = []
        for j, name2 in enumerate(concept_names[i+1:], start=i+1):
            ratio = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            if ratio > similarity_threshold:
                similar.append((name2, ratio))
        
        if similar:
            similar_groups.append((name1, similar))
    
    # Show top 20 groups
    for name, similars in similar_groups[:20]:
        print(f"\n'{name}'")
        for sim_name, ratio in similars[:3]:
            print(f"  -> '{sim_name}' (similarity: {ratio:.2f})")
    
    if len(similar_groups) > 20:
        print(f"\n... and {len(similar_groups) - 20} more similar groups")


def analyze_by_module(concepts):
    """Analyze concept distribution by module/directory"""
    print("\n" + "=" * 80)
    print("Concept Distribution by Module")
    print("=" * 80)
    
    module_counts = defaultdict(int)
    
    for concept in concepts:
        source = concept.get('source', '')
        if source:
            # Extract module path
            parts = Path(source).parts
            if len(parts) >= 2:
                module = '/'.join(parts[:3])  # First 3 levels
                module_counts[module] += 1
    
    # Sort by count
    sorted_modules = sorted(module_counts.items(), key=lambda x: -x[1])
    
    print("\nTop 20 modules by concept count:")
    for module, count in sorted_modules[:20]:
        print(f"  {count:4d} concepts in {module}")
    
    return sorted_modules


def analyze_by_type(concepts):
    """Analyze concepts by type"""
    print("\n" + "=" * 80)
    print("Concept Distribution by Type")
    print("=" * 80)
    
    type_counts = defaultdict(int)
    
    for concept in concepts:
        desc = concept['description']
        if ':' in desc:
            concept_type = desc.split(':')[0]
            type_counts[concept_type] += 1
    
    sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
    
    print("\nConcepts by type:")
    for ctype, count in sorted_types:
        print(f"  {count:4d} {ctype}")


def find_overloaded_names(concepts):
    """Find concept names that appear multiple times"""
    print("\n" + "=" * 80)
    print("Overloaded Concept Names (same name, different locations)")
    print("=" * 80)
    
    name_locations = defaultdict(list)
    
    for concept in concepts:
        name = concept['concept']
        source = concept.get('source', 'unknown')
        name_locations[name].append(source)
    
    # Find names that appear in multiple locations
    overloaded = {name: locs for name, locs in name_locations.items() if len(locs) > 1}
    
    if overloaded:
        # Sort by number of occurrences
        sorted_overloaded = sorted(overloaded.items(), key=lambda x: -len(x[1]))
        
        print(f"\nFound {len(overloaded)} overloaded concept names")
        print("\nTop 20 most overloaded:")
        for name, locations in sorted_overloaded[:20]:
            print(f"\n'{name}' appears in {len(locations)} locations:")
            for loc in locations[:5]:
                print(f"  - {loc}")
            if len(locations) > 5:
                print(f"  ... and {len(locations) - 5} more")
    else:
        print("\nNo overloaded concept names found.")


def analyze_config_concepts(concepts):
    """Analyze YAML configuration concepts"""
    print("\n" + "=" * 80)
    print("YAML Configuration Analysis")
    print("=" * 80)
    
    config_concepts = [c for c in concepts if c['description'].startswith('Config:')]
    
    print(f"\nTotal configuration concepts: {len(config_concepts)}")
    
    # Group by configuration file
    config_files = defaultdict(int)
    for concept in config_concepts:
        source = concept.get('source', '')
        if source:
            config_files[source] += 1
    
    sorted_files = sorted(config_files.items(), key=lambda x: -x[1])
    
    print("\nTop 15 configuration files by concept count:")
    for file, count in sorted_files[:15]:
        print(f"  {count:3d} concepts in {Path(file).name}")


def search_concepts(concepts, keyword):
    """Search for concepts containing a keyword"""
    print(f"\n{'=' * 80}")
    print(f"Concepts containing '{keyword}'")
    print(f"{'=' * 80}\n")
    
    matches = [
        c for c in concepts
        if keyword.lower() in c['concept'].lower() or keyword.lower() in c['description'].lower()
    ]
    
    print(f"Found {len(matches)} matches\n")
    
    for concept in matches[:20]:
        print(f"Concept: {concept['concept']}")
        print(f"  Description: {concept['description'][:150]}")
        print(f"  Source: {concept.get('source', 'unknown')}")
        print()
    
    if len(matches) > 20:
        print(f"... and {len(matches) - 20} more matches")


def main():
    """Main analysis function"""
    concepts = load_concepts()
    
    print("=" * 80)
    print("TBP Monty Ontological Analysis")
    print("=" * 80)
    print(f"\nTotal concepts loaded: {len(concepts)}\n")
    
    # Run analyses
    analyze_by_type(concepts)
    analyze_by_module(concepts)
    analyze_config_concepts(concepts)
    find_overloaded_names(concepts)
    find_similar_concepts(concepts, similarity_threshold=0.85)
    
    # Example searches
    print("\n" + "=" * 80)
    print("Example: Concepts related to 'evidence'")
    print("=" * 80)
    search_concepts(concepts, 'evidence')


if __name__ == '__main__':
    main()
