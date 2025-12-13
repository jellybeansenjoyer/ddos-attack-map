"""
Attack Predictor Module
Loads trained model and makes real-time predictions
"""

import joblib
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import json


class AttackPredictor:
    """Real-time attack classification predictor"""
    
    def __init__(self, 
                 model_path: str = 'models/attack_classifier.pkl',
                 scaler_path: str = 'models/feature_scaler.pkl',
                 encoder_path: str = 'models/label_encoder.pkl',
                 metadata_path: str = 'models/model_metadata.json'):
        """
        Initialize predictor with trained model
        
        Args:
            model_path: Path to trained model file
            scaler_path: Path to feature scaler file
            encoder_path: Path to label encoder file
            metadata_path: Path to model metadata file
        """
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.encoder_path = Path(encoder_path)
        self.metadata_path = Path(metadata_path)
        
        # Load model components
        self.model = None
        self.scaler = None
        self.encoder = None
        self.metadata = None
        self.feature_names = None
        
        self._load_model()
    
    def _load_model(self):
        """Load all model components"""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}\n"
                f"Train a model first with: python3 train_model.py"
            )
        
        # Load model
        self.model = joblib.load(self.model_path)
        
        # Load scaler
        if self.scaler_path.exists():
            self.scaler = joblib.load(self.scaler_path)
        
        # Load encoder
        if self.encoder_path.exists():
            self.encoder = joblib.load(self.encoder_path)
        
        # Load metadata
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
                self.feature_names = self.metadata.get('feature_names', [])
    
    def predict(self, features: Dict[str, float]) -> Dict:
        """
        Predict attack classification
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Dictionary with prediction results:
            {
                'class': str,           # Predicted class name
                'class_id': int,        # Class ID
                'confidence': float,    # Confidence (0-1)
                'probabilities': dict,  # Probabilities for each class
                'is_threat': bool       # True if not legitimate
            }
        """
        # Convert features to array
        feature_array = self._features_to_array(features)
        
        # Scale features
        if self.scaler:
            feature_array = self.scaler.transform(feature_array.reshape(1, -1))
        else:
            feature_array = feature_array.reshape(1, -1)
        
        # Predict class
        prediction = self.model.predict(feature_array)[0]
        
        # Get probabilities
        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(feature_array)[0]
        else:
            # Model doesn't support probabilities
            probabilities = np.zeros(len(self.encoder.classes_))
            probabilities[prediction] = 1.0
        
        # Decode prediction
        if self.encoder:
            class_name = self.encoder.inverse_transform([prediction])[0]
        else:
            class_name = str(prediction)
        
        # Get confidence (max probability)
        confidence = float(np.max(probabilities))
        
        # Create probabilities dict
        prob_dict = {}
        if self.encoder:
            for i, class_label in enumerate(self.encoder.classes_):
                prob_dict[class_label] = float(probabilities[i])
        
        # Determine if threat
        is_threat = class_name != 'legitimate'
        
        return {
            'class': class_name,
            'class_id': int(prediction),
            'confidence': confidence,
            'probabilities': prob_dict,
            'is_threat': is_threat
        }
    
    def predict_batch(self, features_list: List[Dict]) -> List[Dict]:
        """
        Predict classifications for multiple samples
        
        Args:
            features_list: List of feature dictionaries
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        for features in features_list:
            result = self.predict(features)
            results.append(result)
        return results
    
    def _features_to_array(self, features: Dict[str, float]) -> np.ndarray:
        """Convert feature dictionary to numpy array in correct order"""
        if self.feature_names:
            # Use metadata feature order
            return np.array([
                features.get(name, 0.0) for name in self.feature_names
            ])
        else:
            # Use alphabetical order
            feature_keys = sorted(features.keys())
            return np.array([features[key] for key in feature_keys])
    
    def get_model_info(self) -> Dict:
        """Get information about loaded model"""
        info = {
            'model_loaded': self.model is not None,
            'model_path': str(self.model_path),
            'has_scaler': self.scaler is not None,
            'has_encoder': self.encoder is not None,
            'metadata': self.metadata
        }
        
        if self.encoder:
            info['classes'] = self.encoder.classes_.tolist()
        
        if self.feature_names:
            info['feature_names'] = self.feature_names
            info['num_features'] = len(self.feature_names)
        
        return info
    
    def explain_prediction(self, features: Dict[str, float], 
                          prediction: Dict) -> str:
        """
        Generate human-readable explanation of prediction
        
        Args:
            features: Input features
            prediction: Prediction result
            
        Returns:
            Explanation string
        """
        explanation = []
        
        class_name = prediction['class']
        confidence = prediction['confidence'] * 100
        
        explanation.append(
            f"Classification: {class_name.upper()} (confidence: {confidence:.1f}%)"
        )
        
        # Add key features
        if self.feature_names:
            explanation.append("\nKey indicators:")
            
            # Show top contributing features
            important_features = [
                ('cloudflare_threat_score', 'High threat score'),
                ('requests_per_minute', 'Request rate'),
                ('abuseipdb_confidence', 'IP reputation'),
                ('burst_factor', 'Traffic burstiness'),
            ]
            
            for feature_key, description in important_features:
                if feature_key in features:
                    value = features[feature_key]
                    explanation.append(f"  • {description}: {value:.1f}")
        
        # Add threat assessment
        if prediction['is_threat']:
            explanation.append(f"\n⚠️  THREAT DETECTED: {class_name}")
        else:
            explanation.append("\n✅ Traffic appears legitimate")
        
        return '\n'.join(explanation)


def load_predictor() -> AttackPredictor:
    """
    Convenience function to load predictor
    
    Returns:
        Initialized AttackPredictor instance
    """
    return AttackPredictor()


if __name__ == "__main__":
    # Test predictor
    print("Testing Attack Predictor...")
    
    try:
        predictor = load_predictor()
        info = predictor.get_model_info()
        
        print(f"\n✅ Model loaded successfully")
        print(f"Model type: {info['metadata'].get('model_type', 'unknown')}")
        print(f"Classes: {info.get('classes', [])}")
        print(f"Features: {info.get('num_features', 0)}")
        
        # Test prediction
        test_features = {
            'requests_per_minute': 500,
            'cloudflare_threat_score': 85,
            'abuseipdb_confidence': 75,
            'unique_paths_requested': 5,
            'burst_factor': 3.5,
            'country_risk_score': 0.8,
            'request_method_diversity': 0.5,
            'time_since_first_seen': 2.0
        }
        
        result = predictor.predict(test_features)
        explanation = predictor.explain_prediction(test_features, result)
        
        print(f"\nTest Prediction:")
        print(explanation)
        
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("Train a model first with: python3 train_model.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
