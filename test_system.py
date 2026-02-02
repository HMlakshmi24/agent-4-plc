#!/usr/bin/env python3
"""
Comprehensive system test for Agent4PLC
Tests:
1. API endpoint accessibility
2. PLC code generation (all 5 languages)
3. IEC 61131-3 validation
4. Login/Register flow
5. Code review pipeline
"""

import requests
import json
import time
import sys

# Configuration
API_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:5173"

# Test data
TEST_REQUIREMENT = """
Create a PLC program that controls a traffic light with the following logic:
1. Red light is ON by default (1 second on start)
2. After 5 seconds, switch to Yellow light (2 seconds)
3. After 2 seconds, switch to Green light (5 seconds)
4. Repeat cycle
5. Emergency stop button should immediately turn all lights OFF
"""

LANGUAGES = ["ST", "IL", "LD", "FBD", "SFC"]

# =========================================================================
# TEST HELPER FUNCTIONS
# =========================================================================

def print_header(title):
    """Print formatted test section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_test(test_name, status, details=""):
    """Print test result"""
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"  # Green or Red
    reset = "\033[0m"
    print(f"{color}{symbol}{reset} {test_name}")
    if details:
        print(f"  Details: {details}")

def test_api_health():
    """Test 1: Check if backend is running"""
    print_header("TEST 1: API HEALTH CHECK")
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            data = response.json()
            print_test("Backend Running", True, f"{data.get('status')} - Version {data.get('version')}")
            return True
        else:
            print_test("Backend Running", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("Backend Running", False, str(e))
        return False

def test_plc_generation():
    """Test 2: Generate PLC code in all 5 languages"""
    print_header("TEST 2: PLC CODE GENERATION (ALL LANGUAGES)")
    
    all_passed = True
    results = {}
    
    for lang in LANGUAGES:
        print(f"\n  Testing {lang}...")
        try:
            payload = {
                "requirement": TEST_REQUIREMENT,
                "language": lang,
                "plc_brand": "generic"
            }
            
            response = requests.post(
                f"{API_URL}/plc-v2/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                code_length = len(data.get("code", ""))
                warnings = len(data.get("warnings", []))
                
                print_test(
                    f"  {lang} Code Generation",
                    True,
                    f"Generated {code_length} characters, {warnings} warnings"
                )
                
                results[lang] = {
                    "success": True,
                    "code_length": code_length,
                    "warnings": data.get("warnings", []),
                    "validated": data.get("validated", False),
                    "code_sample": data.get("code", "")[:200]
                }
            else:
                print_test(
                    f"  {lang} Code Generation",
                    False,
                    f"Status: {response.status_code}, Message: {response.text[:100]}"
                )
                all_passed = False
                results[lang] = {
                    "success": False,
                    "error": response.text
                }
        
        except requests.Timeout:
            print_test(f"  {lang} Code Generation", False, "Request timeout (30s)")
            all_passed = False
            results[lang] = {"success": False, "error": "Timeout"}
        except Exception as e:
            print_test(f"  {lang} Code Generation", False, str(e))
            all_passed = False
            results[lang] = {"success": False, "error": str(e)}
    
    return all_passed, results

def test_code_review():
    """Test 3: Code review and validation pipeline"""
    print_header("TEST 3: CODE REVIEW & VALIDATION PIPELINE")
    
    try:
        payload = {
            "requirement": TEST_REQUIREMENT,
            "language": "ST",
            "plc_brand": "generic"
        }
        
        response = requests.post(
            f"{API_URL}/plc-v2/review",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            is_ready = data.get("is_ready_to_download", False)
            warnings = data.get("warnings", [])
            feedback = data.get("detailed_feedback", [])
            
            print_test(
                "Code Review Endpoint",
                True,
                f"Status: {data.get('status')}"
            )
            
            print(f"\n  Validation Results:")
            print(f"    Ready to Download: {is_ready}")
            print(f"    Total Warnings: {len(warnings)}")
            
            if warnings:
                print(f"\n  Warnings:")
                for warn in warnings[:3]:  # Show first 3
                    print(f"    - {warn}")
                if len(warnings) > 3:
                    print(f"    ... and {len(warnings) - 3} more")
            
            if feedback:
                print(f"\n  Detailed Feedback:")
                for fb in feedback:
                    print(f"    {fb}")
            
            return True, data
        else:
            print_test("Code Review Endpoint", False, f"Status: {response.status_code}")
            return False, None
    
    except Exception as e:
        print_test("Code Review Endpoint", False, str(e))
        return False, None

def test_iec_validation():
    """Test 4: IEC 61131-3 validation directly"""
    print_header("TEST 4: IEC 61131-3 VALIDATION FRAMEWORK")
    
    try:
        from backend.iec_validator import IECValidator
        
        validator = IECValidator()
        
        # Test 1: Check requirement quality
        assessment = validator.quick_test(TEST_REQUIREMENT)
        print_test(
            "Requirement Assessment",
            assessment is not None,
            assessment if assessment else "No issues found"
        )
        
        # Test 2: Validate proper ST code
        valid_st_code = """
PROGRAM TrafficLight
VAR
    red_timer: TON;
    yellow_timer: TON;
    green_timer: TON;
    emergency_stop: BOOL := FALSE;
    current_state: INT := 0;
END_VAR

red_timer(IN := NOT emergency_stop, PT := T#5s);
yellow_timer(IN := NOT emergency_stop, PT := T#2s);
green_timer(IN := NOT emergency_stop, PT := T#5s);

IF emergency_stop THEN
    current_state := 99;
END_IF;

END_PROGRAM
        """
        
        structure_errors = validator.validate_code_structure(valid_st_code)
        print_test(
            "ST Code Structure Validation",
            len(structure_errors) == 0,
            f"Found {len(structure_errors)} issues" if structure_errors else "Valid"
        )
        
        # Test 3: Validate ST specific requirements
        st_errors = validator.validate_st_code(valid_st_code)
        print_test(
            "ST Specific Validation",
            len(st_errors) == 0,
            f"Found {len(st_errors)} issues" if st_errors else "Valid"
        )
        
        return True
    
    except ImportError:
        print_test("IEC Validator Import", False, "Module not found")
        return False
    except Exception as e:
        print_test("IEC Validation Tests", False, str(e))
        return False

def test_auth_flow():
    """Test 5: Authentication flow"""
    print_header("TEST 5: AUTHENTICATION FLOW")
    
    test_email = f"testuser_{int(time.time())}@test.com"
    test_password = "TestPassword123!"
    
    try:
        # Test 1: Register new user
        register_payload = {
            "email": test_email,
            "password": test_password
        }
        
        reg_response = requests.post(
            f"{API_URL}/auth/register",
            json=register_payload,
            timeout=10
        )
        
        if reg_response.status_code == 200 or reg_response.status_code == 201:
            print_test("User Registration", True, f"User created: {test_email}")
            
            # Test 2: Login with registered user
            login_payload = {
                "username": test_email,
                "password": test_password
            }
            
            login_response = requests.post(
                f"{API_URL}/auth/login",
                data=login_payload,
                timeout=10
            )
            
            if login_response.status_code == 200:
                data = login_response.json()
                has_token = "access_token" in data
                has_user_id = "user_id" in data
                has_email = "email" in data
                
                print_test("User Login", True, f"Token received")
                print_test("User ID in Response", has_user_id, f"user_id: {data.get('user_id', 'NOT FOUND')}")
                print_test("Email in Response", has_email, f"email: {data.get('email', 'NOT FOUND')}")
                
                return True
            else:
                print_test("User Login", False, f"Status: {login_response.status_code}")
                return False
        else:
            print_test("User Registration", False, f"Status: {reg_response.status_code}")
            return False
    
    except Exception as e:
        print_test("Authentication Flow", False, str(e))
        return False

def test_api_endpoints():
    """Test 6: All API endpoints are accessible"""
    print_header("TEST 6: API ENDPOINTS ACCESSIBILITY")
    
    endpoints = [
        ("GET", "/", "Health Check"),
        ("POST", "/plc-v2/generate", "PLC Generation"),
        ("POST", "/plc-v2/review", "Code Review"),
        ("POST", "/auth/register", "Register"),
        ("POST", "/auth/login", "Login"),
    ]
    
    all_passed = True
    
    for method, endpoint, description in endpoints:
        try:
            url = f"{API_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                # Send minimal payload for POST
                response = requests.post(url, json={}, timeout=5)
            
            # 405 (Method Not Allowed) is OK - means endpoint exists
            # 422 (Validation Error) is OK - means endpoint exists but needs proper data
            # 404 (Not Found) is BAD - endpoint doesn't exist
            
            endpoint_exists = response.status_code != 404
            print_test(
                f"{method} {endpoint}",
                endpoint_exists,
                f"Status: {response.status_code}"
            )
            
            if not endpoint_exists:
                all_passed = False
        
        except Exception as e:
            print_test(f"{method} {endpoint}", False, str(e))
            all_passed = False
    
    return all_passed

# =========================================================================
# MAIN TEST RUNNER
# =========================================================================

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  AGENT4PLC COMPREHENSIVE SYSTEM TEST")
    print("="*70)
    print(f"\nAPI URL: {API_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Test Requirement: {TEST_REQUIREMENT[:100]}...")
    
    results = {
        "timestamp": time.time(),
        "tests": []
    }
    
    # Run tests
    test_results = []
    
    # Test 1: Health check
    health_ok = test_api_health()
    if not health_ok:
        print("\n" + "!"*70)
        print("  FATAL: Backend is not running!")
        print("  Please start the backend with: python backend/main.py")
        print("!"*70)
        sys.exit(1)
    
    # Test 2: PLC generation
    gen_ok, gen_results = test_plc_generation()
    test_results.append(("PLC Generation", gen_ok))
    
    # Test 3: Code review
    review_ok, review_data = test_code_review()
    test_results.append(("Code Review", review_ok))
    
    # Test 4: IEC validation
    iec_ok = test_iec_validation()
    test_results.append(("IEC Validation", iec_ok))
    
    # Test 5: Auth flow
    auth_ok = test_auth_flow()
    test_results.append(("Authentication", auth_ok))
    
    # Test 6: API endpoints
    endpoints_ok = test_api_endpoints()
    test_results.append(("API Endpoints", endpoints_ok))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, ok in test_results if ok)
    total = len(test_results)
    
    for test_name, ok in test_results:
        symbol = "✓" if ok else "✗"
        color = "\033[92m" if ok else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{symbol}{reset} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "🎉 "*10)
        print("ALL TESTS PASSED! System is ready to use.")
        print("🎉 "*10)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
