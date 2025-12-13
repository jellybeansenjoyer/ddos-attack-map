"""
Feature Extraction Module
Extracts ML features from attack data
"""

import numpy as np
from datetime import datetime, timezone
from collections import Counter
from typing import Dict, List, Optional


# Country risk scores (0.0 = safe, 1.0 = high risk)
COUNTRY_RISK_SCORES = {
    'CN': 0.8,  # China
    'RU': 0.8,  # Russia
    'KP': 0.9,  # North Korea
    'IR': 0.85, # Iran
    'BY': 0.75, # Belarus
    'VN': 0.7,  # Vietnam
    'BR': 0.6,  # Brazil
    'IN': 0.5,  # India
    'TR': 0.5,  # Turkey
    'US': 0.2,  # United States
    'GB': 0.2,  # United Kingdom
    'DE': 0.2,  # Germany
    'FR': 0.2,  # France
    'JP': 0.15, # Japan
    'CA': 0.15, # Canada
    'AU': 0.15, # Australia
    'KR': 0.2,  # South Korea
}


class FeatureExtractor:
    """Extract ML features from attack records"""
    
    def __init__(self):
        self.feature_names = [
            'requests_per_minute',
            'cloudflare_threat_score',
            'abuseipdb_confidence',
            'unique_paths_requested',
            'burst_factor',
            'country_risk_score',
            'request_method_diversity',
            'time_since_first_seen'
        ]
    
    def extract(self, attack, ip_history: Optional[List] = None) -> Dict[str, float]:
        """
        Extract features from a single attack record
        
        Args:
            attack: Attack model instance
            ip_history: Optional list of previous attacks from this IP
            
        Returns:
            Dictionary of features
        """
        features = {}
        
        # Feature 1: Requests per minute
        features['requests_per_minute'] = self._calculate_rpm(attack)
        
        # Feature 2: Cloudflare threat score (0-100)
        features['cloudflare_threat_score'] = float(attack.threat_score or 0)
        
        # Feature 3: AbuseIPDB confidence score (0-100)
        features['abuseipdb_confidence'] = float(attack.confidence_score or 0)
        
        # Feature 4: Unique paths requested (simplified)
        features['unique_paths_requested'] = self._estimate_unique_paths(attack)
        
        # Feature 5: Burst factor
        features['burst_factor'] = self._calculate_burst_factor(
            attack, ip_history
        )
        
        # Feature 6: Country risk score
        features['country_risk_score'] = self._get_country_risk(
            attack.country_code
        )
        
        # Feature 7: Request method diversity (simplified)
        features['request_method_diversity'] = self._calculate_method_diversity(
            attack, ip_history
        )
        
        # Feature 8: Time since first seen (hours)
        features['time_since_first_seen'] = self._calculate_time_active(
            attack, ip_history
        )
        
        return features
    
    def extract_batch(self, attacks: List, 
                     ip_histories: Optional[Dict] = None) -> List[Dict]:
        """
        Extract features from multiple attack records
        
        Args:
            attacks: List of Attack model instances
            ip_histories: Dict mapping IP addresses to their attack history
            
        Returns:
            List of feature dictionaries
        """
        features_list = []
        
        for attack in attacks:
            # Get IP history if available
            ip_history = None
            if ip_histories and attack.ip_address in ip_histories:
                ip_history = ip_histories[attack.ip_address]
            
            features = self.extract(attack, ip_history)
            features_list.append(features)
        
        return features_list
    
    def to_array(self, features: Dict) -> np.ndarray:
        """Convert feature dict to numpy array in correct order"""
        return np.array([
            features[name] for name in self.feature_names
        ])
    
    def to_array_batch(self, features_list: List[Dict]) -> np.ndarray:
        """Convert list of feature dicts to 2D numpy array"""
        return np.array([
            self.to_array(features) for features in features_list
        ])
    
    # ==================== Feature Calculation Methods ====================
    
    def _calculate_rpm(self, attack) -> float:
        """Calculate requests per minute"""
        # Assume request_count is over 1 minute window
        return float(attack.request_count or 1)
    
    def _estimate_unique_paths(self, attack) -> float:
        """
        Estimate number of unique paths
        Simplified: use request path if available, else estimate
        """
        # In real implementation, would aggregate multiple requests
        # For now, estimate based on attack type
        if attack.request_path:
            return 1.0
        
        # Estimate based on request count
        # DOS: usually targets fewer paths
        # Scan: targets many different paths
        if attack.request_count:
            if attack.request_count > 1000:
                return min(attack.request_count * 0.01, 100)
            else:
                return min(attack.request_count * 0.1, 50)
        
        return 1.0
    
    def _calculate_burst_factor(self, attack, 
                                ip_history: Optional[List] = None) -> float:
        """
        Calculate burst factor (traffic burstiness)
        Higher = more bursty (typical of automated attacks)
        """
        if not ip_history or len(ip_history) < 2:
            # No history, use request count as proxy
            if attack.request_count and attack.request_count > 100:
                return 2.0  # Likely bursty
            return 1.0
        
        # Calculate time intervals between attacks
        timestamps = sorted([a.timestamp for a in ip_history])
        intervals = []
        
        for i in range(1, len(timestamps)):
            delta = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(delta)
        
        if not intervals:
            return 1.0
        
        # Calculate coefficient of variation (CV)
        mean = np.mean(intervals)
        std = np.std(intervals)
        
        if mean > 0:
            cv = std / mean
            # Normalize to 0-5 range
            return min(cv, 5.0)
        
        return 1.0
    
    def _get_country_risk(self, country_code: Optional[str]) -> float:
        """Get risk score for country"""
        if not country_code:
            return 0.5  # Unknown = medium risk
        
        return COUNTRY_RISK_SCORES.get(country_code, 0.5)
    
    def _calculate_method_diversity(self, attack,
                                    ip_history: Optional[List] = None) -> float:
        """
        Calculate HTTP method diversity using Shannon entropy
        Higher = more diverse methods (typical of scans)
        """
        methods = []
        
        # Add current attack method
        if attack.request_method:
            methods.append(attack.request_method)
        
        # Add methods from history
        if ip_history:
            for a in ip_history:
                if a.request_method:
                    methods.append(a.request_method)
        
        if not methods:
            return 0.0
        
        # Calculate Shannon entropy
        method_counts = Counter(methods)
        total = len(methods)
        entropy = 0.0
        
        for count in method_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * np.log2(p + 1e-10)  # Add small value to avoid log(0)
        
        # Normalize (max entropy for 4 methods = 2.0)
        return min(entropy, 2.0)
    
    def _calculate_time_active(self, attack,
                               ip_history: Optional[List] = None) -> float:
        """
        Calculate how long this IP has been active (in hours)
        """
        if not ip_history or len(ip_history) < 2:
            return 0.0  # First time seen
        
        # Get first and current timestamp
        timestamps = [a.timestamp for a in ip_history]
        timestamps.append(attack.timestamp)
        
        first_seen = min(timestamps)
        current = attack.timestamp
        
        # Calculate hours
        delta = current - first_seen
        hours = delta.total_seconds() / 3600
        
        # Cap at 168 hours (1 week)
        return min(hours, 168.0)
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names in order"""
        return self.feature_names.copy()


def extract_features_from_attack(attack, ip_history=None) -> Dict[str, float]:
    """
    Convenience function to extract features from a single attack
    
    Args:
        attack: Attack model instance
        ip_history: Optional list of previous attacks from this IP
        
    Returns:
        Dictionary of features
    """
    extractor = FeatureExtractor()
    return extractor.extract(attack, ip_history)


if __name__ == "__main__":
    # Test feature extraction
    print("Feature Extractor Module")
    print(f"Features: {FeatureExtractor().get_feature_names()}")
