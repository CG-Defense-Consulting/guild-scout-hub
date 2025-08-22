#!/usr/bin/env python3
"""
Debug path calculations for .env file location
"""

from pathlib import Path

print("🔍 Debugging Path Calculations...")
print()

# Current file location
current_file = Path(__file__)
print(f"Current file: {current_file}")
print(f"Current file absolute: {current_file.absolute()}")
print()

# Parent directories
parent1 = current_file.parent
parent2 = parent1.parent
parent3 = parent2.parent
parent4 = parent3.parent

print(f"Parent 1 (etl/): {parent1}")
print(f"Parent 2 (etl/core/): {parent2}")
print(f"Parent 3 (etl/core/uploaders/): {parent3}")
print(f"Parent 4 (project root): {parent4}")
print()

# Check if .env exists at each level
for i, path in enumerate([parent1, parent2, parent3, parent4], 1):
    env_file = path / '.env'
    exists = env_file.exists()
    print(f"Level {i}: {env_file} - {'✓ Exists' if exists else '✗ Missing'}")
    
    if exists:
        print(f"  Full path: {env_file.absolute()}")
        print(f"  Contents preview:")
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()[:3]  # First 3 lines
                for line in lines:
                    print(f"    {line.strip()}")
        except Exception as e:
            print(f"    Error reading: {e}")
    print()
