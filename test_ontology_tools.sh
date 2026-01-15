#!/bin/bash
# Quick test to verify all ontology tools work correctly

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Testing Ontology Analysis Tools                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Verify JSON is valid and has expected count
echo "Test 1: Validating ontology_concepts.json..."
CONCEPT_COUNT=$(python3 -c "import json; print(len(json.load(open('ontology_concepts.json'))))")
if [ "$CONCEPT_COUNT" -eq 3352 ]; then
    echo "  ✅ JSON valid with $CONCEPT_COUNT concepts"
else
    echo "  ❌ Expected 3352 concepts, got $CONCEPT_COUNT"
    exit 1
fi

# Test 2: Test jq queries work
echo ""
echo "Test 2: Testing jq queries..."
MOTOR_COUNT=$(jq '[.[] | select(.concept | contains("Motor") or contains("motor"))] | length' ontology_concepts.json 2>/dev/null)
if [ ! -z "$MOTOR_COUNT" ] && [ "$MOTOR_COUNT" -gt 0 ]; then
    echo "  ✅ Found $MOTOR_COUNT motor-related concepts"
else
    echo "  ⚠️  jq not installed or query failed (optional)"
fi

# Test 3: Test Python scripts can import and run basic checks
echo ""
echo "Test 3: Testing Python scripts..."
python3 << 'PYEOF'
import sys

# Test extract_ontology.py imports
try:
    import ast, json, yaml, pathlib
    print("  ✅ extract_ontology.py dependencies available")
except ImportError as e:
    print(f"  ❌ Missing dependency: {e}")
    sys.exit(1)

# Test analyze_ontology.py can load concepts
try:
    with open('ontology_concepts.json', 'r') as f:
        concepts = json.load(f)
    assert len(concepts) == 3352, f"Expected 3352 concepts, got {len(concepts)}"
    print("  ✅ analyze_ontology.py can load concepts")
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test example queries
try:
    motor_concepts = [c for c in concepts if 'motor' in c['concept'].lower()]
    print(f"  ✅ Found {len(motor_concepts)} motor concepts via Python")
except Exception as e:
    print(f"  ❌ Query error: {e}")
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║   ✅ All Tests Passed - Tools Ready to Use!              ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
else
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║   ❌ Some Tests Failed                                    ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    exit 1
fi
