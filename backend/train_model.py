#!/usr/bin/env python3
"""
ML Model Training Script
Trains attack classification models
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

# ML imports
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, classification_report, confusion_matrix
)

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("⚠️  XGBoost not installed. Install with: pip install xgboost")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import project modules
try:
    from app_models import Attack
    from app_database import get_session
    from ml_feature_extractor import FeatureExtractor
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're in the backend directory")
    sys.exit(1)


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")


def load_training_data():
    """Load attack data from database"""
    print_header("Loading Training Data")
    
    session = get_session()
    
    try:
        # Load all attacks
        attacks = session.query(Attack).all()
        
        if len(attacks) < 100:
            print_warning(f"Only {len(attacks)} attacks found")
            print_info("Recommend at least 1000 samples for good training")
            print_info("Run: python3 seed_database.py --count 1000")
        
        print_success(f"Loaded {len(attacks):,} attack records")
        
        # Filter out attacks without classification
        labeled_attacks = [a for a in attacks if a.classification]
        
        if len(labeled_attacks) < len(attacks):
            print_warning(f"Filtered to {len(labeled_attacks):,} labeled attacks")
        
        session.close()
        return labeled_attacks
        
    except Exception as e:
        print_error(f"Failed to load data: {e}")
        session.close()
        return []


def extract_features(attacks):
    """Extract features from attacks"""
    print_header("Extracting Features")
    
    extractor = FeatureExtractor()
    
    # Group attacks by IP for history
    from collections import defaultdict
    ip_histories = defaultdict(list)
    
    for attack in attacks:
        ip_histories[str(attack.ip_address)].append(attack)
    
    # Extract features
    print_info("Extracting features from attacks...")
    features_list = extractor.extract_batch(attacks, ip_histories)
    
    # Convert to DataFrame
    df = pd.DataFrame(features_list)
    
    # Extract labels
    labels = [attack.classification for attack in attacks]
    
    print_success(f"Extracted {len(extractor.get_feature_names())} features per record")
    print_info(f"Features: {', '.join(extractor.get_feature_names())}")
    
    return df, labels, extractor


def prepare_dataset(X, y):
    """Prepare train/test split"""
    print_header("Preparing Dataset")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        stratify=y,
        random_state=42
    )
    
    print_success(f"Train set: {len(X_train):,} samples")
    print_success(f"Test set: {len(X_test):,} samples")
    
    # Show class distribution
    from collections import Counter
    train_dist = Counter(y_train)
    
    print_info("Class distribution:")
    total = len(y_train)
    for class_name, count in sorted(train_dist.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"   - {class_name}: {pct:.1f}% ({count} samples)")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Encode labels
    encoder = LabelEncoder()
    y_train_encoded = encoder.fit_transform(y_train)
    y_test_encoded = encoder.transform(y_test)
    
    return (X_train_scaled, X_test_scaled, 
            y_train_encoded, y_test_encoded,
            scaler, encoder)


def train_models(X_train, y_train):
    """Train multiple models"""
    print_header("Training Models")
    
    models = {}
    
    # 1. Random Forest
    print_info("Training Random Forest...")
    start = datetime.now()
    
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    
    duration = (datetime.now() - start).total_seconds()
    print_success(f"Random Forest trained ({duration:.1f}s)")
    models['random_forest'] = rf_model
    
    # 2. XGBoost (if available)
    if HAS_XGBOOST:
        print_info("Training XGBoost...")
        start = datetime.now()
        
        xgb_model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1,
            eval_metric='mlogloss'
        )
        xgb_model.fit(X_train, y_train)
        
        duration = (datetime.now() - start).total_seconds()
        print_success(f"XGBoost trained ({duration:.1f}s)")
        models['xgboost'] = xgb_model
    
    # 3. Logistic Regression (baseline)
    print_info("Training Logistic Regression...")
    start = datetime.now()
    
    lr_model = LogisticRegression(
        max_iter=1000,
        random_state=42,
        n_jobs=-1
    )
    lr_model.fit(X_train, y_train)
    
    duration = (datetime.now() - start).total_seconds()
    print_success(f"Logistic Regression trained ({duration:.1f}s)")
    models['logistic_regression'] = lr_model
    
    return models


def evaluate_models(models, X_test, y_test, encoder):
    """Evaluate all models"""
    print_header("Evaluating Models")
    
    results = {}
    
    for name, model in models.items():
        # Predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        results[name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'model': model
        }
        
        # Print results
        model_display = name.replace('_', ' ').title()
        print(f"\n{model_display}:")
        print(f"  Accuracy:  {accuracy*100:5.1f}%")
        print(f"  Precision: {precision*100:5.1f}%")
        print(f"  Recall:    {recall*100:5.1f}%")
        print(f"  F1 Score:  {f1*100:5.1f}%")
    
    return results


def select_best_model(results):
    """Select best performing model"""
    print_header("Selecting Best Model")
    
    # Sort by F1 score
    sorted_models = sorted(
        results.items(),
        key=lambda x: x[1]['f1'],
        reverse=True
    )
    
    best_name, best_metrics = sorted_models[0]
    
    print_success(f"{best_name.replace('_', ' ').title()} selected (highest F1: {best_metrics['f1']*100:.1f}%)")
    
    return best_name, best_metrics['model']


def save_model(model, scaler, encoder, feature_names, metadata):
    """Save model and associated files"""
    print_header("Saving Model")
    
    # Create models directory
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)
    
    # Save model
    model_path = models_dir / 'attack_classifier.pkl'
    joblib.dump(model, model_path)
    print_success(f"Model saved: {model_path}")
    
    # Save scaler
    scaler_path = models_dir / 'feature_scaler.pkl'
    joblib.dump(scaler, scaler_path)
    print_success(f"Scaler saved: {scaler_path}")
    
    # Save encoder
    encoder_path = models_dir / 'label_encoder.pkl'
    joblib.dump(encoder, encoder_path)
    print_success(f"Encoder saved: {encoder_path}")
    
    # Save metadata
    metadata_path = models_dir / 'model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print_success(f"Metadata saved: {metadata_path}")
    
    return model_path


def show_feature_importance(model, feature_names):
    """Display feature importance"""
    print_header("Feature Importance")
    
    # Get feature importances
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        
        # Sort by importance
        indices = np.argsort(importances)[::-1]
        
        print_info("Top 5 most important features:")
        for i in range(min(5, len(indices))):
            idx = indices[i]
            print(f"  {i+1}. {feature_names[idx]}: {importances[idx]*100:.1f}%")
    else:
        print_info("Model does not support feature importance")


def main():
    """Main training pipeline"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  DOS ATTACK MAP - ML MODEL TRAINING")
    print("=" * 60)
    print(Colors.END)
    
    # Step 1: Load data
    attacks = load_training_data()
    if len(attacks) < 100:
        print_error("\nInsufficient training data!")
        print_info("Need at least 100 labeled attacks")
        print_info("Run: python3 seed_database.py --count 1000")
        return 1
    
    # Step 2: Extract features
    X, y, extractor = extract_features(attacks)
    feature_names = extractor.get_feature_names()
    
    # Step 3: Prepare dataset
    (X_train, X_test, y_train, y_test, 
     scaler, encoder) = prepare_dataset(X, y)
    
    # Step 4: Train models
    models = train_models(X_train, y_train)
    
    # Step 5: Evaluate models
    results = evaluate_models(models, X_test, y_test, encoder)
    
    # Step 6: Select best model
    best_name, best_model = select_best_model(results)
    
    # Step 7: Save model
    metadata = {
        'model_type': best_name,
        'training_date': datetime.now().isoformat(),
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'feature_names': feature_names,
        'classes': encoder.classes_.tolist(),
        'metrics': {
            'accuracy': float(results[best_name]['accuracy']),
            'precision': float(results[best_name]['precision']),
            'recall': float(results[best_name]['recall']),
            'f1_score': float(results[best_name]['f1'])
        }
    }
    
    model_path = save_model(best_model, scaler, encoder, feature_names, metadata)
    
    # Step 8: Show feature importance
    show_feature_importance(best_model, feature_names)
    
    # Success!
    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Model training complete!{Colors.END}")
    print(f"{Colors.GREEN}Model ready for predictions at: {model_path}{Colors.END}\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Training cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
