#!/usr/bin/env python3
"""
Example insights from the ontology analysis
Run this to see some interesting patterns in the codebase
"""

import json
from collections import Counter, defaultdict

with open('ontology_concepts.json', 'r') as f:
    concepts = json.load(f)

print("=" * 80)
print("INTERESTING INSIGHTS FROM ONTOLOGY ANALYSIS")
print("=" * 80)

# 1. Most common words in concept names
print("\n1. Most common words in concept names:")
words = []
for c in concepts:
    name = c['concept'].split('/')[-1]  # Get last part for config paths
    # Split camelCase and snake_case
    import re
    parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', name)
    words.extend([p.lower() for p in parts if len(p) > 3])

word_counts = Counter(words).most_common(20)
for word, count in word_counts:
    print(f"   {word:20s} appears {count:3d} times")

# 2. Classes with most methods
print("\n2. Files with most concepts (potential complexity hotspots):")
file_concepts = defaultdict(list)
for c in concepts:
    source = c.get('source', '')
    if source:
        file_concepts[source].append(c['concept'])

top_files = sorted(file_concepts.items(), key=lambda x: -len(x[1]))[:10]
for file, concept_list in top_files:
    print(f"   {len(concept_list):3d} concepts in {file.split('/')[-1]}")

# 3. Configuration complexity
print("\n3. Most complex configuration files:")
config_concepts = defaultdict(int)
for c in concepts:
    if c['description'].startswith('Config:'):
        source = c.get('source', '')
        if source:
            config_concepts[source] += 1

top_configs = sorted(config_concepts.items(), key=lambda x: -x[1])[:10]
for file, count in top_configs:
    print(f"   {count:3d} config keys in {file.split('/')[-1]}")

# 4. Potential naming patterns to investigate
print("\n4. Concepts that might benefit from standardization:")
patterns = {
    'Matching': [c['concept'] for c in concepts if 'match' in c['concept'].lower()],
    'Logger/Logging': [c['concept'] for c in concepts if 'log' in c['concept'].lower()],
    'Module': [c['concept'] for c in concepts if 'module' in c['concept'].lower()],
    'Handler': [c['concept'] for c in concepts if 'handler' in c['concept'].lower()],
}

for pattern, concept_list in patterns.items():
    print(f"   {len(concept_list):3d} concepts related to '{pattern}'")

print("\n" + "=" * 80)
print("Run 'python analyze_ontology.py' for more detailed analysis")
print("=" * 80)
