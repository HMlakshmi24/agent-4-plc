ch#!/usr/bin/env python3
"""Test the new intelligent generator"""
import sys
sys.path.insert(0, '.')

from backend.enhanced_intelligent_generator import generate_perfect_industrial_plc

print("=" * 70)
print("TESTING INTELLIGENT LLM-POWERED GENERATOR")
print("=" * 70)

# Test 1: Traffic Light
print("\n🔴 TEST 1: Traffic Light Controller")
result1 = generate_perfect_industrial_plc(
    "Design a traffic light controller with red, yellow, and green lights. The green light should be on for 10 seconds, yellow for 3 seconds.",
    program_name="TrafficLight"
)
print(f"Confidence: {result1['confidence']}")
print(f"Tokens Used: {result1.get('tokens_used', 0)}")
print(f"Program Name in Code: {'TrafficLight' if 'PROGRAM TrafficLight' in result1['code'] else 'WRONG!'}")
print("\nCode Preview:")
print(result1['code'][:800])

# Test 2: Motor Control  
print("\n\n🔴 TEST 2: Motor Control")
result2 = generate_perfect_industrial_plc(
    "Create a motor control circuit with a start button, stop button, and overload protection",
    program_name="MotorControl"
)
print(f"Confidence: {result2['confidence']}")
print(f"Tokens Used: {result2.get('tokens_used', 0)}")
print(f"Program Name in Code: {'MotorControl' if 'PROGRAM MotorControl' in result2['code'] else 'WRONG!'}")
print("\nCode Preview:")
print(result2['code'][:800])

# Test 3: Tank Level Control
print("\n\n🔴 TEST 3: Tank Level Control")
result3 = generate_perfect_industrial_plc(
    "Create a tank level control system. When level drops below 20%, turn on pump. When reaches 90%, turn off pump.",
    program_name="TankLevelControl"
)
print(f"Confidence: {result3['confidence']}")
print(f"Tokens Used: {result3.get('tokens_used', 0)}")
print(f"Program Name in Code: {'TankLevelControl' if 'PROGRAM TankLevelControl' in result3['code'] else 'WRONG!'}")
print("\nCode Preview:")
print(result3['code'][:800])

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Test 1 (Traffic):   ✅ Program name correct: {'TrafficLight' in result1['code']}")
print(f"Test 2 (Motor):     ✅ Program name correct: {'MotorControl' in result2['code']}")
print(f"Test 3 (Tank):      ✅ Program name correct: {'TankLevelControl' in result3['code']}")
print(f"\nAll tests used LLM: {all(r.get('tokens_used', 0) > 0 for r in [result1, result2, result3])}")

