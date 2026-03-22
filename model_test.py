"""
Comprehensive Model Test Suite
Tests the Industrial PLC Code Generator with multiple prompts and domains
"""
import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from backend.functional_state_generator import generate_perfect_industrial_plc

# Test prompts covering different domains
TEST_PROMPTS = [
    # Process Control
    "Process control regulating temperature using feedback loops and mathematical functions",
    "Control a motor with start and stop buttons and emergency stop",
    "Elevator control with floor sensors and door control",
    "Industrial conveyor with start stop and safety sensors",
    "Traffic light control with pedestrian crossing",
    "Pump station with pressure control and safety interlocks",
    "Car wash system with pre-wash wash rinse and dry states",
    "Parking garage gate control with vehicle counting",
    "Industrial door control with safety sensors",
    "Bottling line filling control with sensors",
]

def test_model():
    """Run comprehensive tests on the model"""
    print("=" * 80)
    print("MODEL TEST: Industrial PLC Code Generator")
    print("=" * 80)
    
    results = []
    
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {prompt[:50]}...")
        print(f"{'='*60}")
        
        try:
            result = generate_perfect_industrial_plc(prompt)
            
            # Extract domain from model
            domain = result.get('model', {}).get('domain', 'unknown')
            
            test_result = {
                'prompt': prompt,
                'domain': domain,
                'iec_compliant': result.get('iec_compliant', False),
                'confidence': result.get('confidence', 0),
                'code_length': len(result.get('code', '')),
                'errors': result.get('errors', []),
                'warnings': result.get('warnings', []),
                'success': result.get('code', '') != '' and not result.get('errors', [])
            }
            
            print(f"  Domain: {domain}")
            print(f"  IEC Compliant: {test_result['iec_compliant']}")
            print(f"  Confidence: {test_result['confidence']}%")
            print(f"  Code Length: {test_result['code_length']} chars")
            print(f"  Errors: {len(test_result['errors'])}")
            print(f"  Success: {test_result['success']}")
            
            if test_result['errors']:
                print(f"  Error Details: {test_result['errors'][:2]}")  # Show first 2 errors
            
            results.append(test_result)
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'prompt': prompt,
                'domain': 'error',
                'iec_compliant': False,
                'confidence': 0,
                'code_length': 0,
                'errors': [str(e)],
                'warnings': [],
                'success': False
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    print(f"Total Tests: {total}")
    print(f"Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    # Domain breakdown
    domains = {}
    for r in results:
        d = r['domain']
        if d not in domains:
            domains[d] = {'total': 0, 'success': 0}
        domains[d]['total'] += 1
        if r['success']:
            domains[d]['success'] += 1
    
    print("\nDomain Breakdown:")
    for domain, stats in sorted(domains.items()):
        pct = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {domain}: {stats['success']}/{stats['total']} ({pct:.1f}%)")
    
    # Average confidence
    avg_conf = sum(r['confidence'] for r in results) / total if total > 0 else 0
    print(f"\nAverage Confidence: {avg_conf:.1f}%")
    
    return results


if __name__ == "__main__":
    results = test_model()

