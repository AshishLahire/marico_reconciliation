import pandas as pd
import numpy as np
from datetime import datetime
from .ai_detector import AIMismatchDetector

class ReconciliationEngine:
    """Core reconciliation logic"""
    
    def __init__(self):
        self.ai_detector = AIMismatchDetector()
        
    def reconcile(self, company_df, customer_df, product_df):
        """Perform reconciliation between company and customer records"""
        
        mismatches = []
        
        # Merge dataframes
        merged = pd.merge(
            company_df, 
            customer_df, 
            on=['invoice_id', 'product_id'],
            how='left',
            suffixes=('_company', '_customer')
        )
        
        # Fill missing customer data
        merged['reported_quantity'] = merged['reported_quantity'].fillna(merged['quantity'])
        merged['reported_amount'] = merged['reported_amount'].fillna(merged['total_amount'])
        
        # Calculate differences
        merged['quantity_diff'] = merged['quantity'] - merged['reported_quantity']
        merged['amount_diff'] = merged['total_amount'] - merged['reported_amount']
        merged['quantity_diff_pct'] = (abs(merged['quantity_diff']) / merged['quantity']) * 100
        merged['amount_diff_pct'] = (abs(merged['amount_diff']) / merged['total_amount']) * 100
        
        # Calculate days delayed (simulated)
        merged['date_company'] = pd.to_datetime(merged['date'])
        merged['days_delayed'] = np.random.randint(0, 45, len(merged))
        
        # Detect mismatches
        for idx, row in merged.iterrows():
            if abs(row['quantity_diff']) > 0 or abs(row['amount_diff']) > 0:
                
                # Use AI to classify mismatch
                ai_result = self.ai_detector.predict_mismatch(
                    qty_diff_pct=row['quantity_diff_pct'],
                    price_diff_pct=row['amount_diff_pct'],
                    days_delayed=row['days_delayed'],
                    amount=row['total_amount']
                )
                
                # Determine severity
                if row['quantity_diff_pct'] > 15 or row['amount_diff_pct'] > 15:
                    severity = "High"
                    color = "🔴"
                elif row['quantity_diff_pct'] > 5 or row['amount_diff_pct'] > 5:
                    severity = "Medium"
                    color = "🟡"
                else:
                    severity = "Low"
                    color = "🟢"
                
                mismatches.append({
                    'invoice_id': row['invoice_id'],
                    'customer_name': row['customer_name'],
                    'product_name': product_df[product_df['product_id'] == row['product_id']]['product_name'].values[0] if len(product_df[product_df['product_id'] == row['product_id']]) > 0 else row['product_id'],
                    'company_qty': row['quantity'],
                    'customer_qty': row['reported_quantity'],
                    'qty_diff': row['quantity_diff'],
                    'company_amount': row['total_amount'],
                    'customer_amount': row['reported_amount'],
                    'amount_diff': row['amount_diff'],
                    'mismatch_type': ai_result['mismatch_type'],
                    'ai_reason': ai_result['reason'],
                    'ai_resolution': ai_result['resolution'],
                    'severity': severity,
                    'severity_icon': color,
                    'ai_confidence': ai_result['confidence'],
                    'status': 'Open',
                    'detected_date': datetime.now().strftime("%Y-%m-%d")
                })
        
        return pd.DataFrame(mismatches)
    
    def get_summary_stats(self, mismatches_df, total_invoices):
        """Generate summary statistics"""
        if len(mismatches_df) == 0:
            return {
                'total_mismatches': 0,
                'reconciliation_rate': 100,
                'total_financial_impact': 0,
                'high_severity': 0,
                'medium_severity': 0,
                'low_severity': 0,
                'by_type': {}
            }
        
        return {
            'total_mismatches': len(mismatches_df),
            'reconciliation_rate': ((total_invoices - len(mismatches_df)) / total_invoices) * 100,
            'total_financial_impact': abs(mismatches_df['amount_diff'].sum()),
            'high_severity': len(mismatches_df[mismatches_df['severity'] == 'High']),
            'medium_severity': len(mismatches_df[mismatches_df['severity'] == 'Medium']),
            'low_severity': len(mismatches_df[mismatches_df['severity'] == 'Low']),
            'by_type': mismatches_df['mismatch_type'].value_counts().to_dict()
        }
