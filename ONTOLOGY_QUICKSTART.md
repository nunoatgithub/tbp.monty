# Quick Reference: Using the Ontological Analysis

This guide provides practical examples for using the ontology analysis tools.

## Files Overview

| File | Purpose |
|------|---------|
| `extract_ontology.py` | Extracts all concepts from Python and YAML files |
| `ontology_concepts.json` | JSON output with 3,352 cataloged concepts |
| `analyze_ontology.py` | Helper script to analyze the concepts |
| `ONTOLOGY_ANALYSIS.md` | Complete documentation |

## Quick Start

### 1. Re-run the extraction (if code changes)
```bash
python extract_ontology.py
```

### 2. Run the analysis
```bash
python analyze_ontology.py
```

### 3. Use jq for custom queries
```bash
# Install jq if needed: sudo apt-get install jq

# Count total concepts
jq 'length' ontology_concepts.json

# Find all concepts related to "motor"
jq '.[] | select(.concept | contains("motor") or contains("Motor"))' ontology_concepts.json

# Count concepts by type
jq -r '.[].description | split(":")[0]' ontology_concepts.json | sort | uniq -c | sort -rn

# Find all classes
jq '.[] | select(.description | startswith("Class:"))' ontology_concepts.json

# Search in specific module
jq '.[] | select(.source | contains("evidence_matching"))' ontology_concepts.json
```

## Common Analysis Tasks

### Find Potential Duplicates

Look for concepts with similar names that might be redundant:

```bash
# Find all "match" related concepts
jq '.[] | select(.concept | test("match"; "i"))' ontology_concepts.json | jq -s 'group_by(.concept) | .[] | {concept: .[0].concept, count: length, sources: [.[].source]}'

# Find concepts that appear in multiple files
jq 'group_by(.concept) | map(select(length > 1)) | .[] | {concept: .[0].concept, count: length, locations: [.[].source]}' ontology_concepts.json
```

### Identify Ontological Overload

Find areas with too many concepts:

```bash
# Count concepts per module
jq -r '.[].source | split("/")[0:3] | join("/")' ontology_concepts.json | sort | uniq -c | sort -rn | head -20

# Find modules with most classes
jq '.[] | select(.description | startswith("Class:")) | .source' ontology_concepts.json | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -10
```

### Explore Configuration Structure

Understand YAML configuration hierarchy:

```bash
# All configuration concepts
jq '.[] | select(.description | startswith("Config:"))' ontology_concepts.json | jq -s 'length'

# Group configs by file
jq '.[] | select(.description | startswith("Config:")) | .source' ontology_concepts.json | sort | uniq -c | sort -rn | head -20

# Find experiment configurations
jq '.[] | select(.source | contains("conf/experiment"))' ontology_concepts.json | head -20
```

### Find Specific Patterns

```bash
# All learning module concepts
jq '.[] | select(.concept | contains("LM") or .concept | contains("Learning"))' ontology_concepts.json

# All motor policies
jq '.[] | select(.concept | contains("Policy") or .concept | contains("policy"))' ontology_concepts.json

# All protocols (interfaces)
jq '.[] | select(.description | contains("Protocol"))' ontology_concepts.json

# All dataclasses
jq '.[] | select(.description | startswith("Dataclass:"))' ontology_concepts.json

# All enums
jq '.[] | select(.description | contains("Enum"))' ontology_concepts.json
```

## Python API Examples

### Load and analyze in Python

```python
import json

# Load concepts
with open('ontology_concepts.json', 'r') as f:
    concepts = json.load(f)

# Find concepts by name
motor_concepts = [c for c in concepts if 'motor' in c['concept'].lower()]
print(f"Found {len(motor_concepts)} motor-related concepts")

# Group by source file
from collections import defaultdict
by_file = defaultdict(list)
for concept in concepts:
    by_file[concept.get('source', 'unknown')].append(concept['concept'])

# Files with most concepts
sorted_files = sorted(by_file.items(), key=lambda x: -len(x[1]))
for file, concept_list in sorted_files[:10]:
    print(f"{len(concept_list):3d} concepts in {file}")

# Find duplicate concept names
from collections import Counter
concept_names = [c['concept'] for c in concepts]
duplicates = {name: count for name, count in Counter(concept_names).items() if count > 1}
print(f"Found {len(duplicates)} concept names used in multiple places")
```

### Custom analysis script

```python
import json

def find_related_concepts(keyword, concepts):
    """Find all concepts related to a keyword"""
    return [
        c for c in concepts 
        if keyword.lower() in c['concept'].lower() 
        or keyword.lower() in c['description'].lower()
    ]

# Load concepts
with open('ontology_concepts.json', 'r') as f:
    concepts = json.load(f)

# Find related concepts
evidence_concepts = find_related_concepts('evidence', concepts)
print(f"\nFound {len(evidence_concepts)} evidence-related concepts:")
for c in evidence_concepts[:10]:
    print(f"  - {c['concept']}: {c['description'][:80]}")
```

## Identifying Refactoring Opportunities

### 1. Find Similar Names
```bash
# Look for variations of the same concept
jq '.[] | .concept' ontology_concepts.json | grep -i "match" | sort | uniq
```

### 2. Find Scattered Implementations
```bash
# Find concepts that appear in multiple unrelated modules
jq 'group_by(.concept) | map(select(length > 3)) | .[] | {name: .[0].concept, locations: [.[].source]}' ontology_concepts.json
```

### 3. Identify Naming Inconsistencies
```bash
# Compare naming patterns (e.g., snake_case vs camelCase)
jq -r '.[].concept' ontology_concepts.json | grep -E "^[A-Z]" | head -20  # CamelCase
jq -r '.[].concept' ontology_concepts.json | grep -E "^[a-z_]" | head -20  # snake_case
```

## Output Format

Each concept in `ontology_concepts.json` has:

```json
{
  "concept": "ConceptName",
  "description": "Type: Brief description",
  "source": "relative/path/to/file.py"
}
```

## Tips

1. **Start broad**: Use `analyze_ontology.py` for overview
2. **Drill down**: Use `jq` for specific queries
3. **Look for patterns**: Similar names, duplicate locations, scattered implementations
4. **Document findings**: Create a separate document listing refactoring opportunities
5. **Prioritize**: Focus on high-impact areas (frequently used modules, public APIs)

## Next Steps

1. Review the analysis output from `analyze_ontology.py`
2. Identify top 10 areas with potential issues
3. Create individual refactoring tasks for each issue
4. Use the JSON data to track which concepts have been addressed

---

**Questions?** See `ONTOLOGY_ANALYSIS.md` for complete documentation.
