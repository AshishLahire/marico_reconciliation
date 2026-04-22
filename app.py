import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import io

# Page config
st.set_page_config(
    page_title="Marico Reconciliation System",
    page_icon="🔄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .upload-box {
        border: 2px dashed #667eea;
        border-radius: 1rem;
        padding: 2rem;
        text-align: center;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DEFAULT DATA (if no CSV uploaded)
# ============================================

def generate_default_data():
    """Generate sample data dynamically"""
    
    products = pd.DataFrame({
        'product_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'product_name': ['Parachute Oil', 'Svelte Oil', 'Livon Serum', 'Set Wet Spray', 'Navya Cream'],
        'price': [150, 299, 299, 225, 249]
    })
    
    customers = ['Reliance Retail', 'DMart', 'Amazon India', 'Flipkart', 'Nykaa']
    channels = ['OT', 'OT', 'D2C', 'D2C', 'D2C']
    
    invoices = []
    mismatches = []
    
    for i in range(50):
        cust_idx = random.randint(0, 4)
        prod = products.iloc[random.randint(0, 4)]
        qty = random.randint(50, 500)
        amount = qty * prod['price']
        date = datetime.now() - timedelta(days=random.randint(1, 60))
        
        invoices.append({
            'invoice_id': f'INV{i+1:04d}',
            'date': date.strftime('%Y-%m-%d'),
            'customer_name': customers[cust_idx],
            'channel': channels[cust_idx],
            'product_name': prod['product_name'],
            'quantity': qty,
            'amount': amount,
            'status': 'Pending'
        })
        
        if random.random() < 0.4:
            diff_pct = random.uniform(0.02, 0.15)
            cust_amount = amount * (1 - diff_pct)
            diff = amount - cust_amount
            
            if diff_pct > 0.1:
                severity = "High"
            elif diff_pct > 0.05:
                severity = "Medium"
            else:
                severity = "Low"
                
            mismatches.append({
                'invoice_id': f'INV{i+1:04d}',
                'customer_name': customers[cust_idx],
                'product_name': prod['product_name'],
                'company_amount': amount,
                'customer_amount': round(cust_amount, 2),
                'difference': round(diff, 2),
                'severity': severity,
                'status': 'Open'
            })
    
    return pd.DataFrame(invoices), pd.DataFrame(mismatches), products

# ============================================
# CSV VALIDATION & RECONCILIATION ENGINE
# ============================================

def validate_csv(df, file_name, required_columns):
    """Validate CSV file has required columns"""
    if df is None or df.empty:
        return False, f"{file_name} is empty"
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return False, f"Missing columns in {file_name}: {missing_cols}"
    
    return True, "Valid"

def reconcile_from_csv(company_df, customer_df):
    """Reconcile company and customer uploaded CSVs"""
    
    mismatches = []
    
    # Check if dataframes are valid
    if company_df is None or customer_df is None:
        return pd.DataFrame()
    
    if company_df.empty or customer_df.empty:
        return pd.DataFrame()
    
    # Merge on invoice_id
    merged = pd.merge(
        company_df, 
        customer_df, 
        on='invoice_id', 
        how='outer',
        suffixes=('_company', '_customer')
    )
    
    for _, row in merged.iterrows():
        company_amt = row.get('amount_company', 0)
        customer_amt = row.get('amount_customer', 0)
        
        # Handle missing values
        if pd.isna(company_amt):
            company_amt = 0
        if pd.isna(customer_amt):
            customer_amt = 0
        
        diff = company_amt - customer_amt
        
        if abs(diff) > 0.01:  # Mismatch found (ignore tiny rounding errors)
            diff_pct = abs(diff) / max(company_amt, 1) * 100
            
            if diff_pct > 10:
                severity = "High"
            elif diff_pct > 5:
                severity = "Medium"
            else:
                severity = "Low"
            
            # Get customer name from either column
            cust_name = row.get('customer_name_company', row.get('customer_name_customer', 'Unknown'))
            
            mismatches.append({
                'invoice_id': row.get('invoice_id', 'Unknown'),
                'customer_name': cust_name,
                'company_amount': round(company_amt, 2),
                'customer_amount': round(customer_amt, 2),
                'difference': round(diff, 2),
                'severity': severity,
                'status': 'Open'
            })
    
    return pd.DataFrame(mismatches)

# ============================================
# SAMPLE CSV TEMPLATES
# ============================================

def get_company_template():
    """Return sample company CSV template"""
    return pd.DataFrame({
        'invoice_id': ['INV001', 'INV002'],
        'customer_name': ['Reliance Retail', 'DMart'],
        'amount': [75000, 89700],
        'date': ['2024-01-15', '2024-01-16'],
        'product_name': ['Parachute Oil', 'Svelte Oil'],
        'quantity': [500, 300],
        'channel': ['OT', 'OT']
    })

def get_customer_template():
    """Return sample customer CSV template"""
    return pd.DataFrame({
        'invoice_id': ['INV001', 'INV002'],
        'customer_name': ['Reliance Retail', 'DMart'],
        'amount': [74250, 89100],
        'status': ['Reported', 'Reported']
    })

# ============================================
# MAIN APP
# ============================================

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔄 Marico AI Reconciliation System</h1>
        <p>Intelligent Customer Reconciliation & Claims Resolution</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'uploaded_mismatches' not in st.session_state:
        st.session_state.uploaded_mismatches = pd.DataFrame()
    if 'uploaded_company' not in st.session_state:
        st.session_state.uploaded_company = pd.DataFrame()
    if 'uploaded_customer' not in st.session_state:
        st.session_state.uploaded_customer = pd.DataFrame()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🏢 Navigation")
        page = st.radio("", ["📊 Dashboard", "📁 Upload CSV", "🔍 Reconciliation", "⚖️ Claims", "📷 Scanner"])
        
        st.markdown("---")
        st.markdown("### 📊 Data Source")
        
        # Data source selection
        data_source = st.radio(
            "Choose data source:",
            ["Use Sample Data", "Upload My CSV Files"]
        )
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.session_state.uploaded_mismatches = pd.DataFrame()
            st.rerun()
    
    # Load data based on selection
    if data_source == "Use Sample Data":
        invoices_df, mismatches_df, products_df = generate_default_data()
        st.sidebar.success("✅ Using sample data")
    else:
        # CSV Upload section - Only show if on Upload page or data exists
        if page == "📁 Upload CSV":
            pass  # Will show upload interface
        elif st.session_state.uploaded_company.empty:
            st.sidebar.warning("⚠️ Please upload CSV files in 'Upload CSV' tab")
            # Still show dashboard with empty data
            invoices_df = pd.DataFrame()
            mismatches_df = pd.DataFrame()
            products_df = pd.DataFrame()
        else:
            invoices_df = st.session_state.uploaded_company
            mismatches_df = st.session_state.uploaded_mismatches
            products_df = pd.DataFrame()
    
    # ========== DASHBOARD PAGE ==========
    if page == "📊 Dashboard":
        st.subheader("📊 Key Metrics")
        
        if data_source == "Upload My CSV Files" and invoices_df.empty:
            st.info("📁 Please go to 'Upload CSV' tab to upload your files first")
        else:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_amount = invoices_df['amount'].sum() if not invoices_df.empty and 'amount' in invoices_df.columns else 0
                st.markdown(f"""
                <div class="metric-card">
                    <h3>💰 Total Value</h3>
                    <h2>₹{total_amount/100000:.1f}L</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card warning-card">
                    <h3>⚠️ Mismatches</h3>
                    <h2>{len(mismatches_df)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                recon_rate = (1 - len(mismatches_df)/len(invoices_df)) * 100 if len(invoices_df) > 0 else 0
                st.markdown(f"""
                <div class="metric-card success-card">
                    <h3>📊 Match Rate</h3>
                    <h2>{recon_rate:.1f}%</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                total_diff = mismatches_df['difference'].sum() if len(mismatches_df) > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <h3>💸 Blocked Capital</h3>
                    <h2>₹{abs(total_diff/1000):.0f}K</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Charts
            if 'channel' in invoices_df.columns and not invoices_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📈 Channel-wise Revenue")
                    channel_data = invoices_df.groupby('channel')['amount'].sum().reset_index()
                    fig = px.pie(channel_data, values='amount', names='channel', title='Revenue by Channel')
                    st.plotly_chart(fig, use_container_width=True)
            
            # Mismatch Table
            st.subheader("📋 Detected Mismatches")
            if len(mismatches_df) > 0:
                st.dataframe(mismatches_df, use_container_width=True)
            else:
                st.success("✅ No mismatches found! All records reconciled.")
    
    # ========== UPLOAD CSV PAGE ==========
    elif page == "📁 Upload CSV":
        st.subheader("📁 Upload Your Data Files")
        
        st.markdown("""
        <div class="upload-box">
            <h3>📤 Upload Company and Customer CSV Files</h3>
            <p>The system will automatically reconcile and find mismatches</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📤 Company Records (Marico)")
            st.markdown("**Required columns:** invoice_id, customer_name, amount")
            
            # Download template button
            template_df = get_company_template()
            csv_template = template_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Company CSV Template",
                data=csv_template,
                file_name="company_template.csv",
                mime="text/csv"
            )
            
            company_file = st.file_uploader(
                "Choose Company CSV",
                type=['csv'],
                key="company_upload"
            )
            
            company_df = None
            if company_file:
                try:
                    company_df = pd.read_csv(company_file)
                    st.dataframe(company_df.head(10), use_container_width=True)
                    st.caption(f"Total rows: {len(company_df)}")
                    
                    # Validate
                    is_valid, msg = validate_csv(company_df, "Company CSV", ['invoice_id', 'customer_name', 'amount'])
                    if is_valid:
                        st.success("✅ Company CSV is valid")
                    else:
                        st.error(f"❌ {msg}")
                        company_df = None
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    company_df = None
        
        with col2:
            st.markdown("### 📥 Customer Records")
            st.markdown("**Required columns:** invoice_id, customer_name, amount")
            
            # Download template button
            cust_template_df = get_customer_template()
            cust_csv_template = cust_template_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Customer CSV Template",
                data=cust_csv_template,
                file_name="customer_template.csv",
                mime="text/csv"
            )
            
            customer_file = st.file_uploader(
                "Choose Customer CSV",
                type=['csv'],
                key="customer_upload"
            )
            
            customer_df = None
            if customer_file:
                try:
                    customer_df = pd.read_csv(customer_file)
                    st.dataframe(customer_df.head(10), use_container_width=True)
                    st.caption(f"Total rows: {len(customer_df)}")
                    
                    # Validate
                    is_valid, msg = validate_csv(customer_df, "Customer CSV", ['invoice_id', 'customer_name', 'amount'])
                    if is_valid:
                        st.success("✅ Customer CSV is valid")
                    else:
                        st.error(f"❌ {msg}")
                        customer_df = None
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    customer_df = None
        
        # Reconcile button
        if company_file and customer_file and company_df is not None and customer_df is not None:
            st.markdown("---")
            if st.button("🔄 Run Reconciliation on Uploaded Data", use_container_width=True):
                with st.spinner("Reconciling..."):
                    mismatches = reconcile_from_csv(company_df, customer_df)
                    
                    st.session_state.uploaded_mismatches = mismatches
                    st.session_state.uploaded_company = company_df
                    st.session_state.uploaded_customer = customer_df
                    
                    if len(mismatches) > 0:
                        st.success(f"✅ Reconciliation complete! Found {len(mismatches)} mismatches.")
                        
                        st.subheader("📋 Mismatch Report")
                        st.dataframe(mismatches, use_container_width=True)
                        
                        # Download button
                        csv = mismatches.to_csv(index=False)
                        st.download_button("📥 Download Mismatch Report", csv, "mismatch_report.csv", "text/csv")
                    else:
                        st.success("✅ All records reconciled! No mismatches found.")
                        st.balloons()
        elif company_file or customer_file:
            st.warning("⚠️ Please upload both Company and Customer CSV files")
    
    # ========== RECONCILIATION PAGE ==========
    elif page == "🔍 Reconciliation":
        st.subheader("🔍 Detailed Reconciliation View")
        
        if data_source == "Upload My CSV Files" and st.session_state.uploaded_company.empty:
            st.info("📁 Please upload CSV files in 'Upload CSV' tab first")
        else:
            tab1, tab2, tab3 = st.tabs(["📤 Company Records", "📥 Customer Records", "⚖️ Mismatch Report"])
            
            with tab1:
                if data_source == "Use Sample Data":
                    st.dataframe(invoices_df, use_container_width=True)
                else:
                    if not st.session_state.uploaded_company.empty:
                        st.dataframe(st.session_state.uploaded_company, use_container_width=True)
                        csv = st.session_state.uploaded_company.to_csv(index=False)
                        st.download_button("📥 Download Company Data", csv, "company_data.csv")
                    else:
                        st.info("No company data uploaded")
            
            with tab2:
                if data_source == "Use Sample Data":
                    st.info("Customer records view available in Upload CSV mode")
                else:
                    if not st.session_state.uploaded_customer.empty:
                        st.dataframe(st.session_state.uploaded_customer, use_container_width=True)
                        csv = st.session_state.uploaded_customer.to_csv(index=False)
                        st.download_button("📥 Download Customer Data", csv, "customer_data.csv")
                    else:
                        st.info("No customer data uploaded")
            
            with tab3:
                if data_source == "Use Sample Data":
                    st.dataframe(mismatches_df, use_container_width=True)
                else:
                    if not st.session_state.uploaded_mismatches.empty:
                        st.dataframe(st.session_state.uploaded_mismatches, use_container_width=True)
                        csv = st.session_state.uploaded_mismatches.to_csv(index=False)
                        st.download_button("📥 Download Mismatch Report", csv, "mismatch_report.csv")
                    else:
                        st.success("No mismatches found!")
    
    # ========== CLAIMS PAGE ==========
    elif page == "⚖️ Claims":
        st.subheader("⚖️ Claims Resolution")
        
        if data_source == "Use Sample Data":
            mismatches_to_show = mismatches_df
        else:
            mismatches_to_show = st.session_state.uploaded_mismatches
        
        if mismatches_to_show.empty:
            st.success("🎉 No open claims! All resolved.")
        else:
            open_claims = mismatches_to_show[mismatches_to_show['status'] == 'Open'] if 'status' in mismatches_to_show.columns else mismatches_to_show
            st.info(f"📋 Total open claims: {len(open_claims)}")
            
            for idx, claim in open_claims.iterrows():
                with st.expander(f"Claim: {claim['invoice_id']} - {claim['customer_name']} - ₹{abs(claim['difference']):,.0f}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Company Amount", f"₹{claim['company_amount']:,.0f}")
                        st.metric("Customer Amount", f"₹{claim['customer_amount']:,.0f}")
                    
                    with col2:
                        st.metric("Difference", f"₹{abs(claim['difference']):,.0f}")
                        st.metric("Severity", claim['severity'])
                    
                    st.markdown("---")
                    st.markdown("**🤖 AI Recommendation:**")
                    
                    if claim['severity'] == "High":
                        st.warning("🔴 HIGH PRIORITY - Escalate immediately")
                    elif claim['severity'] == "Medium":
                        st.info("🟡 MEDIUM PRIORITY - Contact customer")
                    else:
                        st.success("🟢 LOW PRIORITY - Next cycle")
                    
                    col_a, col_b, col_c = st.columns(3)
                    if col_a.button(f"✅ Approve", key=f"app_{idx}"):
                        st.success("Claim approved!")
                    if col_b.button(f"📝 Dispute", key=f"dis_{idx}"):
                        st.warning("Dispute raised!")
                    if col_c.button(f"🤝 Negotiate", key=f"neg_{idx}"):
                        st.info("Negotiation initiated!")
    
    # ========== SCANNER PAGE ==========
    elif page == "📷 Scanner":
        st.subheader("📷 Product Scanner")
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 1rem; text-align: center; color: white;">
            <h2>🔍 Scan Product Barcode</h2>
            <p>Enter product ID to simulate scanning</p>
        </div>
        """, unsafe_allow_html=True)
        
        product_id = st.text_input("Enter Product ID:", placeholder="P001, P002, etc.")
        
        if product_id:
            st.info(f"Product ID scanned: {product_id}")
            st.success("✅ Product found! You can now create transaction.")

if __name__ == "__main__":
    main()
