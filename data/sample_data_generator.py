import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_all_data():
    """Generate fresh sample datasets"""
    
    # Product Master
    products = pd.DataFrame({
        'product_id': ['PAR001', 'PAR002', 'SVE001', 'SVE002', 'LIV001', 'LIV002', 'SET001', 'SET002', 'NVY001', 'NVY002'],
        'product_name': ['Parachute Coconut Oil', 'Parachute Advansed Oil', 'Svelte Hair Oil', 'Svelte Anti-Hairfall', 
                        'Livon Hair Serum', 'Livon Hair Serum Small', 'Set Wet Deodorant', 'Set Wet Perfume', 
                        'Navya Face Wash', 'Navya Moisturizer'],
        'brand': ['Parachute', 'Parachute', 'Svelte', 'Svelte', 'Livon', 'Livon', 'Set Wet', 'Set Wet', 'Navya', 'Navya'],
        'category': ['Hair Oil', 'Hair Oil', 'Hair Oil', 'Hair Oil', 'Serum', 'Serum', 'Deodorant', 'Perfume', 'Skincare', 'Skincare'],
        'mrp': [150, 199, 299, 249, 299, 175, 225, 299, 149, 249],
        'unit': ['ml', 'ml', 'ml', 'ml', 'ml', 'ml', 'ml', 'ml', 'ml', 'g'],
        'weight': [1000, 200, 200, 200, 100, 50, 150, 100, 100, 100]
    })
    
    # Company Data
    customers = ['Reliance Retail', 'DMart', 'Amazon India', 'Flipkart', 'Nykaa', "Spencer's"]
    channels = ['OT', 'OT', 'D2C', 'D2C', 'D2C', 'MT']
    
    company_records = []
    for i in range(50):
        cust_idx = np.random.randint(0, len(customers))
        prod = products.iloc[np.random.randint(0, len(products))]
        qty = np.random.randint(50, 1000)
        total = qty * prod['mrp']
        
        company_records.append({
            'invoice_id': f"INV{str(i+1).zfill(4)}",
            'date': (datetime.now() - timedelta(days=np.random.randint(0, 90))).strftime('%Y-%m-%d'),
            'customer_name': customers[cust_idx],
            'product_id': prod['product_id'],
            'quantity': qty,
            'unit_price': prod['mrp'],
            'total_amount': total,
            'channel': channels[cust_idx],
            'status': 'Pending'
        })
    
    company_df = pd.DataFrame(company_records)
    
    # Customer Data (with discrepancies)
    customer_records = []
    for idx, row in company_df.iterrows():
        if np.random.random() < 0.4:  # 40% have mismatches
            qty_diff = np.random.randint(-20, 20)
            reported_qty = max(0, row['quantity'] + qty_diff)
            reported_amt = reported_qty * row['unit_price']
            
            deduction_types = ['promotion', 'damage', 'logistics', 'return', 'claim', 'none']
            deduction = np.random.choice(deduction_types, p=[0.2, 0.2, 0.15, 0.15, 0.2, 0.1])
            
            if deduction != 'none':
                deduction_amt = np.random.uniform(0.01, 0.10) * reported_amt
                reported_amt -= deduction_amt
            else:
                deduction_amt = 0
            
            customer_records.append({
                'record_id': f"CR{idx+1}",
                'customer_name': row['customer_name'],
                'invoice_ref': row['invoice_id'],
                'product_id': row['product_id'],
                'reported_quantity': reported_qty,
                'reported_amount': round(reported_amt, 2),
                'deduction_type': deduction if deduction != 'none' else '',
                'deduction_amount': round(deduction_amt, 2),
                'notes': f"{deduction} adjustment" if deduction != 'none' else 'No issues'
            })
        else:
            customer_records.append({
                'record_id': f"CR{idx+1}",
                'customer_name': row['customer_name'],
                'invoice_ref': row['invoice_id'],
                'product_id': row['product_id'],
                'reported_quantity': row['quantity'],
                'reported_amount': row['total_amount'],
                'deduction_type': '',
                'deduction_amount': 0,
                'notes': 'Matched perfectly'
            })
    
    customer_df = pd.DataFrame(customer_records)
    
    # Save files
    products.to_csv('data/product_master.csv', index=False)
    company_df.to_csv('data/company_data.csv', index=False)
    customer_df.to_csv('data/customer_data.csv', index=False)
    
    print("✅ Data generated successfully!")
    print(f"- Product Master: {len(products)} products")
    print(f"- Company Records: {len(company_df)} invoices")
    print(f"- Customer Records: {len(customer_df)} records")
    
    return products, company_df, customer_df

if __name__ == "__main__":
    generate_all_data()
