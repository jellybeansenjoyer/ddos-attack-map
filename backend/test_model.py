#!/usr/bin/env python3
"""
Test Model Script
Tests the trained ML model with sample predictions
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ml_predictor import AttackPredictor
    from ml_feature_extractor import FeatureExtractor
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")


def test_dos_attack():
    """Test DOS attack classification"""
    print_header("Test 1: DOS Attack")
    
    features = {
        'requests_per_minute': 5000,  # Very high RPM
        'cloudflare_threat_score': 95,  # High threat
        'abuseipdb_confidence': 85,  # High confidence
        'unique_paths_requested': 3,  # Few paths (typical DOS)
        'burst_factor': 4.5,  # Very bursty
        'country_risk_score': 0.8,  # High risk country
        'request_method_diversity': 0.2,  # Low diversity (same method)
        'time_since_first_seen': 0.5  # Recent first appearance
    }
    
    return features


def test_brute_force():
    """Test brute force attack classification"""
    print_header("Test 2: Brute Force Attack")
    
    features = {
        'requests_per_minute': 200,  # Moderate RPM
        'cloudflare_threat_score': 65,  # Medium threat
        'abuseipdb_confidence': 70,  # Medium-high confidence
        'unique_paths_requested': 1,  # Single path (/login)
        'burst_factor': 2.5,  # Moderately bursty
        'country_risk_score': 0.6,  # Medium risk
        'request_method_diversity': 0.0,  # All POST requests
        'time_since_first_seen': 12.0  # Active for 12 hours
    }
    
    return features


def test_port_scan():
    """Test port scan classification"""
    print_header("Test 3: Port Scan")
    
    features = {
        'requests_per_minute': 50,  # Lower RPM
        'cloudflare_threat_score': 45,  # Medium threat
        'abuseipdb_confidence': 55,  # Medium confidence
        'unique_paths_requested': 100,  # Many different paths
        'burst_factor': 1.5,  # Less bursty (systematic)
        'country_risk_score': 0.5,  # Medium risk
        'request_method_diversity': 1.8,  # High diversity (many methods)
        'time_since_first_seen': 2.0  # Active for 2 hours
    }
    
    return features


def test_legitimate():
    """Test legitimate traffic classification"""
    print_header("Test 4: Legitimate Traffic")
    
    features = {
        'requests_per_minute': 10,  # Low RPM
        'cloudflare_threat_score': 5,  # Very low threat
        'abuseipdb_confidence': 0,  # No abuse reports
        'unique_paths_requested': 8,  # Normal browsing
        'burst_factor': 1.0,  # Not bursty
        'country_risk_score': 0.2,  # Low risk country
        'request_method_diversity': 0.8,  # Normal diversity
        'time_since_first_seen': 48.0  # Long-time visitor
    }
    
    return features


def display_prediction(features, result, predictor):
    """Display prediction results"""
    # Show input features
    print(f"\n{Colors.BOLD}Input Features:{Colors.END}")
    for key, value in features.items():
        print(f"  {key:30s} {value:8.1f}")
    
    # Show prediction
    print(f"\n{Colors.BOLD}Prediction:{Colors.END}")
    class_name = result['class']
    confidence = result['confidence'] * 100
    
    if result['is_threat']:
        color = Colors.RED
        icon = "⚠️ "
    else:
        color = Colors.GREEN
        icon = "✅ "
    
    print(f"{color}{icon}Classification: {class_name.upper()}{Colors.END}")
    print(f"  Confidence: {confidence:.1f}%")
    
    # Show probabilities
    print(f"\n{Colors.BOLD}Class Probabilities:{Colors.END}")
    for class_label, prob in sorted(result['probabilities'].items(), 
                                    key=lambda x: -x[1]):
        prob_pct = prob * 100
        bar_length = int(prob_pct / 2)
        bar = '█' * bar_length
        print(f"  {class_label:15s} {prob_pct:5.1f}% {bar}")
    
    # Show explanation
    print(f"\n{Colors.BOLD}Explanation:{Colors.END}")
    explanation = predictor.explain_prediction(features, result)
    for line in explanation.split('\n'):
        if line:
            print(f"  {line}")


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  DOS ATTACK MAP - MODEL TESTING")
    print("=" * 60)
    print(Colors.END)
    
    # Load predictor
    try:
        predictor = AttackPredictor()
        info = predictor.get_model_info()
        
        print(f"\n{Colors.GREEN}✅ Model loaded successfully{Colors.END}")
        print(f"  Model type: {info['metadata'].get('model_type', 'unknown')}")
        print(f"  Trained on: {info['metadata'].get('training_date', 'unknown')}")
        print(f"  Accuracy: {info['metadata'].get('metrics', {}).get('accuracy', 0)*100:.1f}%")
        
    except FileNotFoundError:
        print(f"\n{Colors.RED}❌ Model not found!{Colors.END}")
        print(f"{Colors.YELLOW}Train a model first with: python3 train_model.py{Colors.END}\n")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error loading model: {e}{Colors.END}")
        return 1
    
    # Run tests
    test_cases = [
        ("DOS Attack", test_dos_attack()),
        ("Brute Force", test_brute_force()),
        ("Port Scan", test_port_scan()),
        ("Legitimate Traffic", test_legitimate())
    ]
    
    correct = 0
    total = len(test_cases)
    
    for test_name, features in test_cases:
        # Make prediction
        result = predictor.predict(features)
        
        # Display results
        display_prediction(features, result, predictor)
        
        # Check if correct (based on test name)
        expected_class = test_name.lower().replace(' ', '_').replace('_attack', '').replace('_traffic', '')
        
        # Map test names to actual class names
        class_mapping = {
            'dos': 'dos',
            'brute_force': 'brute_force',
            'port_scan': 'scan',  # Port scan is labeled as 'scan' in model
            'legitimate': 'legitimate'
        }
        
        expected_class = class_mapping.get(expected_class, expected_class)
        
        if result['class'] == expected_class:
            correct += 1
        
        print()  # Spacing
    
    # Summary
    print_header("Test Summary")
    print(f"Tests passed: {correct}/{total}")
    
    if correct == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.END}")
        print(f"{Colors.GREEN}Model is working correctly{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some tests failed{Colors.END}")
        print(f"{Colors.YELLOW}Model may need retraining or more data{Colors.END}\n")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Testing cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
