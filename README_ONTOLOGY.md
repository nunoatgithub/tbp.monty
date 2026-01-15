# 🗺️ Ontology Analysis Tools - README

Complete toolkit for analyzing the conceptual structure of the TBP Monty codebase.

## 🎯 What This Is

An automated ontological explorer that systematically extracts and catalogs **all concepts** from Python source files and YAML configuration files, enabling identification of:
- Ontological overload (too many concepts)
- Duplicated or redundant concepts
- Naming inconsistencies
- Areas needing refactoring

## 📦 What You Get

### 🛠️ Tools (4 scripts)
| Tool | Purpose | Size |
|------|---------|------|
| `extract_ontology.py` | Main extraction script (AST + YAML parsing) | 15 KB |
| `analyze_ontology.py` | Automated analysis and duplicate detection | 6.3 KB |
| `example_insights.py` | Quick insights generator | 2.4 KB |
| `test_ontology_tools.sh` | Validation test suite | 1.8 KB |

### 📊 Data
| File | Content | Size |
|------|---------|------|
| `ontology_concepts.json` | **3,352 concepts** from 385 files | 867 KB |

### 📖 Documentation (3 guides)
| Guide | Purpose | Size |
|-------|---------|------|
| `ONTOLOGY_SUMMARY.md` | Executive summary & key findings | 6.7 KB |
| `ONTOLOGY_ANALYSIS.md` | Complete technical documentation | 4.4 KB |
| `ONTOLOGY_QUICKSTART.md` | Quick reference with examples | 6.5 KB |
| `README_ONTOLOGY.md` | This file - overview & quick start | - |

## 🚀 Quick Start

### 1. Run the Analysis
```bash
# Full automated analysis
python analyze_ontology.py

# Quick insights (< 10 seconds)
python example_insights.py

# Validate everything works
./test_ontology_tools.sh
```

### 2. Explore the Data
```bash
# View sample concepts
head -100 ontology_concepts.json | jq

# Find motor-related concepts
jq '.[] | select(.concept | contains("Motor"))' ontology_concepts.json

# Count concepts by type
jq -r '.[].description | split(":")[0]' ontology_concepts.json | sort | uniq -c | sort -rn
```

### 3. Use Python API
```python
import json

# Load concepts
with open('ontology_concepts.json', 'r') as f:
    concepts = json.load(f)

print(f"Total concepts: {len(concepts)}")

# Find concepts by keyword
matching = [c for c in concepts if 'matching' in c['concept'].lower()]
print(f"Matching-related: {len(matching)}")

# Group by source file
from collections import defaultdict
by_file = defaultdict(list)
for c in concepts:
    by_file[c.get('source', 'unknown')].append(c)

# Most complex files
for file, concepts_list in sorted(by_file.items(), key=lambda x: -len(x[1]))[:5]:
    print(f"{len(concepts_list):3d} concepts in {file}")
```

## 📈 What Was Found

### Extraction Scope
- ✅ **385 files analyzed** (105 Python + 280 YAML)
- ✅ **3,352 concepts extracted**
  - 2,227 Configuration concepts (66.5%)
  - 1,125 Code concepts (33.5%)

### Key Statistics
**Code Concepts:**
- 437 Methods
- 147 Functions
- 130 Classes
- 40 Protocols
- 19 Constants
- 15 Dataclasses

**Top Complexity Hotspots:**
1. `motor_policies.py` (77 concepts)
2. `actions.py` (76 concepts)
3. `graph_matching.py` (58 concepts)

**Overloaded Names:**
- `__init__`: 85 locations
- `__call__`: 18 locations
- `step`: 16 locations

**Standardization Opportunities:**
- 500 "Module"-related concepts
- 356 "Logger"-related concepts
- 173 "Motor"-related concepts

## 🔍 Common Use Cases

### Find Duplicate Concepts
```bash
jq 'group_by(.concept) | map(select(length > 1)) | .[] | {name: .[0].concept, count: length, files: [.[].source]}' ontology_concepts.json
```

### Find Complex Modules
```bash
jq -r '.[].source | split("/")[0:3] | join("/")' ontology_concepts.json | sort | uniq -c | sort -rn | head -20
```

### Search by Keyword
```bash
# All evidence-related concepts
jq '.[] | select(.description | contains("evidence"))' ontology_concepts.json

# All dataclasses
jq '.[] | select(.description | startswith("Dataclass:"))' ontology_concepts.json

# All protocols (interfaces)
jq '.[] | select(.description | contains("Protocol"))' ontology_concepts.json
```

### Find Naming Patterns
```bash
# CamelCase concepts
jq -r '.[].concept' ontology_concepts.json | grep -E "^[A-Z][a-z]+[A-Z]"

# snake_case concepts
jq -r '.[].concept' ontology_concepts.json | grep -E "^[a-z_]+"
```

## 📚 Documentation

### For Quick Start
👉 Read **ONTOLOGY_QUICKSTART.md** - Practical examples and common queries

### For Complete Details
👉 Read **ONTOLOGY_ANALYSIS.md** - Full technical documentation

### For Overview & Findings
👉 Read **ONTOLOGY_SUMMARY.md** - Executive summary with key insights

## 🔄 Re-running the Extraction

If the codebase changes:

```bash
# Re-extract all concepts
python extract_ontology.py

# This will:
# - Scan all Python files in src/
# - Scan all YAML files in conf/
# - Generate new ontology_concepts.json
# - Takes ~2 minutes
```

## 🎯 Next Steps

Use the ontology catalog to:

1. **Identify redundancies** - Run analyze_ontology.py to find duplicates
2. **Create refactoring tasks** - Based on overloaded names and complexity hotspots
3. **Build data model** - Map relationships between concepts
4. **Standardize naming** - Address areas with many similar concepts
5. **Consolidate interfaces** - Review Protocol usage patterns
6. **Simplify configuration** - Analyze complex YAML files

## ✅ Validation

All tools are tested and validated:

```bash
./test_ontology_tools.sh
```

Expected output:
```
✅ JSON valid with 3352 concepts
✅ Found 173 motor-related concepts
✅ extract_ontology.py dependencies available
✅ analyze_ontology.py can load concepts
✅ All Tests Passed - Tools Ready to Use!
```

## 🤝 Contributing

If you find concepts that should be excluded or want to improve the extraction:

1. Edit the filtering logic in `extract_ontology.py`
2. Re-run the extraction
3. Verify with `test_ontology_tools.sh`
4. Update documentation as needed

## 📝 Notes

- The extraction is conservative - better to miss some concepts than to create false positives
- Private methods (starting with `_`) are excluded unless they're special methods (`__init__`, etc.)
- YAML concepts use hierarchical path notation (e.g., `experiment/config/motor_system`)
- Descriptions are truncated at 200 characters for readability
- All tools use Python standard library only (except PyYAML)

## 🆘 Troubleshooting

**Issue**: "module 'yaml' not found"
```bash
pip install pyyaml
```

**Issue**: "jq: command not found" (optional)
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

**Issue**: Concepts missing after extraction
- Check that files are in `src/` or `conf/` directories
- Verify file extensions (`.py`, `.yaml`, `.yml`)
- Review filtering logic in `extract_ontology.py`

## 📞 Support

- See documentation files for detailed usage
- Run test suite to verify setup: `./test_ontology_tools.sh`
- Check example scripts for usage patterns

---

**Status**: ✅ All tools tested and validated  
**Version**: 1.0  
**Last Updated**: 2026-01-15  
**Total Concepts**: 3,352 from 385 files
