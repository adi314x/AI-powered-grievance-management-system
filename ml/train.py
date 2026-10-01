"""
Train the grievance classification model.
Supports: dataset validation, improved vocabulary, multilingual stop words.
"""
import pandas as pd
import joblib
import os
import sys
import warnings
import hashlib
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.utils.text_clean import clean_text, get_stop_words

# Config: increased vocabulary for better domain coverage
MAX_FEATURES = 2500
MIN_DF = 1
NGRAM_RANGE = (1, 2)


def validate_dataset(df):
    """
    Validate dataset quality and return (is_valid, warnings_list, errors_list).
    """
    errors = []
    warnings_list = []
    
    # Required columns
    if 'complaint' not in df.columns or 'department' not in df.columns:
        errors.append("Dataset must have 'complaint' and 'department' columns")
        return False, warnings_list, errors
    
    # Remove rows with missing values
    before = len(df)
    df = df.dropna(subset=['complaint', 'department'])
    if len(df) < before:
        warnings_list.append(f"Removed {before - len(df)} rows with missing complaint/department")
    
    # Check minimum samples
    if len(df) < 50:
        errors.append(f"Dataset too small: {len(df)} samples. Need at least 50 for training.")
    
    # Check complaint length
    short_complaints = df['complaint'].str.len() < 10
    if short_complaints.any():
        count = short_complaints.sum()
        warnings_list.append(f"{count} complaints are very short (<10 chars) - may affect quality")
    
    # Check for duplicates
    dupes = df.duplicated(subset=['complaint', 'department']).sum()
    if dupes > 0:
        warnings_list.append(f"{dupes} duplicate complaint-department pairs found")
    
    # Class balance check
    dept_counts = df['department'].value_counts()
    min_samples = dept_counts.min()
    if min_samples < 5:
        warnings_list.append(
            f"Some departments have very few samples (min={min_samples}). "
            "Consider adding more data for: " +
            ", ".join(dept_counts[dept_counts < 5].index.tolist())
        )
    
    # Class imbalance
    max_samples = dept_counts.max()
    if max_samples > min_samples * 5:
        warnings_list.append(
            f"Significant class imbalance: largest class has {max_samples} samples, "
            f"smallest has {min_samples}"
        )
    
    return len(errors) == 0, warnings_list, errors


def train_classifier():
    """Train the grievance classification model."""
    print("=" * 60)
    print("Training Grievance Classification Model")
    print("=" * 60)
    
    # Load dataset
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'indian_grievance_dataset.csv'
    )
    
    if not os.path.exists(data_path):
        print(f"✗ Dataset not found at {data_path}")
        return False
    
    df = pd.read_csv(data_path)
    
    # Validate dataset
    print("\n--- Dataset Validation ---")
    is_valid, warnings_list, errors = validate_dataset(df)
    
    for w in warnings_list:
        print(f"⚠ {w}")
    for e in errors:
        print(f"✗ {e}")
    
    if not is_valid:
        print("\n✗ Dataset validation failed. Fix errors before training.")
        return False
    
    df = df.dropna(subset=['complaint', 'department'])
    print(f"✓ Loaded dataset with {len(df)} samples")

    # Incorporate correction supplement (from admin manual triage feedback loop)
    supplement_path = os.environ.get('CORRECTION_SUPPLEMENT_PATH')
    if supplement_path and os.path.exists(supplement_path):
        try:
            supplement_df = pd.read_csv(supplement_path)
            supplement_df = supplement_df.dropna(subset=['complaint', 'department'])
            if len(supplement_df) > 0:
                df = pd.concat([df, supplement_df], ignore_index=True)
                print(f"✓ Added {len(supplement_df)} correction samples from admin triage feedback")
        except Exception as supplement_error:
            print(f"⚠ Could not load supplement data: {supplement_error}")

    print(f"✓ Total training samples: {len(df)}")
    print(f"✓ Departments: {df['department'].nunique()}")
    print("\nDepartment distribution:")
    print(df['department'].value_counts())
    
    # Clean text
    print("\n" + "=" * 60)
    print("Cleaning text (multilingual-aware)...")
    df['cleaned_complaint'] = df['complaint'].apply(clean_text)
    print("✓ Text cleaning completed")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df['cleaned_complaint'],
        df['department'],
        test_size=0.2,
        random_state=42,
        stratify=df['department']
    )
    
    print(f"✓ Train set: {len(X_train)} samples")
    print(f"✓ Test set: {len(X_test)} samples")
    
    # Create TF-IDF vectorizer with improved settings
    print("\n" + "=" * 60)
    print(f"Creating TF-IDF vectorizer (max_features={MAX_FEATURES}, multilingual stop words)...")
    custom_stop_words = get_stop_words()
    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES,
        stop_words=custom_stop_words,
        ngram_range=NGRAM_RANGE,
        min_df=MIN_DF
    )
    
    X_train_vectorized = vectorizer.fit_transform(X_train)
    X_test_vectorized = vectorizer.transform(X_test)
    print(f"✓ Vocabulary size: {len(vectorizer.vocabulary_)}")
    
    # Train Logistic Regression
    print("\n" + "=" * 60)
    print("Training Logistic Regression model...")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning)
        model = LogisticRegression(
            max_iter=2000,
            random_state=42,
            solver='lbfgs'
        )
    
    model.fit(X_train_vectorized, y_train)
    print("✓ Model training completed")
    
    # Evaluate
    print("\n" + "=" * 60)
    print("Evaluating model...")
    y_pred = model.predict(X_test_vectorized)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n✓ Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print("\nClassification Report:")
    report_text = classification_report(y_test, y_pred, zero_division=0)
    print(report_text)
    report_dict = classification_report(y_test, y_pred, zero_division=0, output_dict=True)
    
    # Confusion Matrix
    unique_labels = sorted(list(model.classes_))
    cm = confusion_matrix(y_test, y_pred, labels=unique_labels)
    print("\nConfusion Matrix:")
    print("Labels order: " + ", ".join(unique_labels))
    for idx, row in enumerate(cm):
        print(f"  {unique_labels[idx]:<32}: {list(row)}")

    # Save model and vectorizer
    print("\n" + "=" * 60)
    print("Saving model and vectorizer...")
    
    artifacts_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)
    
    model_path = os.path.join(artifacts_dir, 'model.joblib')
    vectorizer_path = os.path.join(artifacts_dir, 'vectorizer.joblib')
    
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    
    print(f"✓ Model saved to: {model_path}")
    print(f"✓ Vectorizer saved to: {vectorizer_path}")
    
    # Save training metadata for retraining logic
    metadata_path = os.path.join(artifacts_dir, 'train_metadata.json')
    import json
    with open(data_path, 'rb') as dataset_file:
        dataset_sha256 = hashlib.sha256(dataset_file.read()).hexdigest()

    metadata = {
        'trained_at_utc': datetime.utcnow().isoformat(),
        'dataset': {
            'path': os.path.relpath(data_path, os.path.dirname(os.path.dirname(__file__))),
            'version_sha256': dataset_sha256,
            'samples': len(df),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'department_count': int(df['department'].nunique()),
        },
        'model': {
            'algorithm': 'LogisticRegression',
            'vectorizer': 'TfidfVectorizer',
            'max_features': MAX_FEATURES,
            'min_df': MIN_DF,
            'ngram_range': list(NGRAM_RANGE),
            'vocabulary_size': len(vectorizer.vocabulary_),
        },
        'metrics': {
            'accuracy': float(accuracy),
            'macro_avg_precision': float(report_dict.get('macro avg', {}).get('precision', 0.0)),
            'macro_avg_recall': float(report_dict.get('macro avg', {}).get('recall', 0.0)),
            'macro_avg_f1': float(report_dict.get('macro avg', {}).get('f1-score', 0.0)),
            'weighted_avg_f1': float(report_dict.get('weighted avg', {}).get('f1-score', 0.0)),
            'confusion_matrix': {
                'labels': unique_labels,
                'matrix': cm.tolist(),
            }
        },
        'label_classes': [str(label) for label in unique_labels],
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata saved to: {metadata_path}")
    
    # Test predictions
    print("\n" + "=" * 60)
    print("Testing predictions on sample complaints (5 Departments):")
    print("=" * 60)
    
    test_complaints = [
        "Big potholes on main road causing severe traffic jam and accidents",
        "Water pipeline leaking underground and tap water is contaminated",
        "Frequent power outage and voltage fluctuation burning home appliances",
        "Garbage not collected from open dumping spot and drains are overflowing",
        "School teacher is absent and classroom roof is leaking during rain",
        "Transformer is sparking and electric poles on street have exposed wires",
        "Sewer manhole cover is missing and sewage is overflowing on the road",
    ]
    
    for complaint in test_complaints:
        cleaned = clean_text(complaint)
        vectorized = vectorizer.transform([cleaned])
        prediction = model.predict(vectorized)[0]
        prob = max(model.predict_proba(vectorized)[0]) if hasattr(model, 'predict_proba') else 1.0
        print(f"\nComplaint: {complaint}")
        print(f"Predicted Department: {prediction} (Confidence: {prob * 100:.1f}%)")
    
    print("\n" + "=" * 60)
    print("✓ Training completed successfully!")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = train_classifier()
    sys.exit(0 if success else 1)
