import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import pickle
import os

class AIMismatchDetector:
    """AI-powered mismatch detection and classification"""
    
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.is_trained = False
        
    def generate_training_data(self):
        """Generate synthetic training data for mismatch classification"""
        np.random.seed(42)
        
        data = []
        for _ in range(1000):
            # Features
            qty_diff_pct = np.random.uniform(0, 30)
            price_diff_pct = np.random.uniform(0, 25)
            days_delayed = np.random.randint(0, 45)
            amount = np.random.uniform(5000, 500000)
            
            # Determine mismatch type based on patterns
            if qty_diff_pct > 15 and price_diff_pct < 5:
                mismatch_type = "quantity_difference"
                reason = "Significant quantity mismatch detected"
                resolution = "Verify warehouse dispatch and POD"
            elif price_diff_pct > 10 and qty_diff_pct < 5:
                mismatch_type = "price_difference"
                reason = "Pricing discrepancy - check promotions"
                resolution = "Review master pricing data"
            elif days_delayed > 30:
                mismatch_type = "logistics_deduction"
                reason = "Delivery delay beyond SLA"
                resolution = "Check logistics partner performance"
            elif qty_diff_pct < 10 and price_diff_pct < 10:
                mismatch_type = "claim_dispute"
                reason = "Customer claim under review"
                resolution = "Validate claim documentation"
            else:
                mismatch_type = "damage_claim"
                reason = "Product damage reported"
                resolution = "Request damage assessment report"
            
            data.append({
                'qty_diff_pct': qty_diff_pct,
                'price_diff_pct': price_diff_pct,
                'days_delayed': days_delayed,
                'amount': amount,
                'mismatch_type': mismatch_type,
                'reason': reason,
                'resolution': resolution
            })
        
        return pd.DataFrame(data)
    
    def train_model(self):
        """Train Random Forest classifier for mismatch type prediction"""
        print("Training AI model...")
        
        # Generate training data
        df = self.generate_training_data()
        
        # Features
        feature_cols = ['qty_diff_pct', 'price_diff_pct', 'days_delayed', 'amount']
        X = df[feature_cols]
        
        # Target
        le = LabelEncoder()
        y = le.fit_transform(df['mismatch_type'])
        self.label_encoders['mismatch_type'] = le
        
        # Train model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        
        # Store feature names
        self.feature_names = feature_cols
        
        self.is_trained = True
        print("✅ AI Model trained successfully!")
        
        # Save model
        with open('models/mismatch_classifier.pkl', 'wb') as f:
            pickle.dump({
                'model': self.model,
                'encoders': self.label_encoders,
                'features': self.feature_names
            }, f)
        
        return self.model
    
    def load_model(self):
        """Load pre-trained model"""
        model_path = 'models/mismatch_classifier.pkl'
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                saved = pickle.load(f)
                self.model = saved['model']
                self.label_encoders = saved['encoders']
                self.feature_names = saved['features']
                self.is_trained = True
            return True
        return False
    
    def predict_mismatch(self, qty_diff_pct, price_diff_pct, days_delayed, amount):
        """Predict mismatch type and provide recommendations"""
        if not self.is_trained:
            self.load_model() or self.train_model()
        
        # Create feature array
        features = np.array([[qty_diff_pct, price_diff_pct, days_delayed, amount]])
        
        # Predict
        pred_class = self.model.predict(features)[0]
        mismatch_type = self.label_encoders['mismatch_type'].inverse_transform([pred_class])[0]
        
        # Get confidence score
        proba = self.model.predict_proba(features)[0]
        confidence = max(proba) * 100
        
        # Generate recommendations based on mismatch type
        recommendations = {
            "quantity_difference": {
                "reason": "Quantity mismatch between company and customer records",
                "resolution": "1. Verify warehouse dispatch records\n2. Check Proof of Delivery (POD)\n3. Contact logistics partner\n4. Conduct joint physical count",
                "priority": "High" if qty_diff_pct > 15 else "Medium"
            },
            "price_difference": {
                "reason": "Pricing discrepancy detected",
                "resolution": "1. Review master pricing data\n2. Check active promotions/discounts\n3. Verify customer contract terms\n4. Validate invoice pricing",
                "priority": "High" if price_diff_pct > 15 else "Medium"
            },
            "logistics_deduction": {
                "reason": "Logistics-related deduction claimed",
                "resolution": "1. Review delivery timeline\n2. Check SLA compliance\n3. Verify transit insurance\n4. Negotiate with logistics partner",
                "priority": "High" if days_delayed > 30 else "Medium"
            },
            "damage_claim": {
                "reason": "Product damage during transit",
                "resolution": "1. Request damage assessment report\n2. Verify return status\n3. Process credit note\n4. File insurance claim",
                "priority": "High"
            },
            "claim_dispute": {
                "reason": "Customer claim requires validation",
                "resolution": "1. Review claim documentation\n2. Verify claim submission timeline\n3. Check scheme eligibility\n4. Schedule joint review meeting",
                "priority": "Medium"
            }
        }
        
        result = recommendations.get(mismatch_type, {
            "reason": "Manual review required",
            "resolution": "Escalate to reconciliation team",
            "priority": "Medium"
        })
        
        return {
            "mismatch_type": mismatch_type.replace("_", " ").title(),
            "confidence": f"{confidence:.1f}%",
            "reason": result["reason"],
            "resolution": result["resolution"],
            "priority": result["priority"],
            "severity": "🔴 High" if result["priority"] == "High" else "🟡 Medium" if result["priority"] == "Medium" else "🟢 Low"
        }
