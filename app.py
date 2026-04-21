import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict
from enum import Enum

# ------------------------ PAGE CONFIG ---------------------------------
st.set_page_config(
    page_title="Marico - Reconciliation System",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------ CUSTOM CSS FOR PRO LOOK --------------------
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.8rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 1rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .info-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------ DATA MODELS ---------------------------------
class MismatchType(Enum):
    PRICE_DIFFERENCE = "💰 Price Difference"
    QUANTITY_DIFFERENCE = "📦 Quantity Difference"
    MISSING_INVOICE = "📄 Missing Invoice"
    CLAIM_DISPUTE = "⚖️ Claim Dispute"
    LOGISTICS_DEDUCTION = "🚚 Logistics Deduction"
    DAMAGE_CLAIM = "💔 Damage Claim"

@dataclass
class Transaction:
    invoice_no: str
    date: datetime
    customer: str
    channel: str
    amount: float
    quantity: int
    status: str

@dataclass
class Mismatch:
    invoice_no: str
    customer: str
    company_amt: float
    customer_amt: float
    diff: float
    mismatch_type: MismatchType
    severity: str
    status: str

# ------------------------ DATA GENERATOR (REALISTIC) -----------------
def generate_data():
    customers = [
        ("C001", "Reliance Retail", "OT"), ("C002", "DMart", "OT"),
        ("C003", "Amazon India", "D2C"), ("C004", "Flipkart", "D2C"),
        ("C005", "Nykaa", "D2C"), ("C006", "Spencer's", "MT")
    ]
    transactions = []
    mismatches = []
    
    start_date = datetime.now() - timedelta(days=60)
    for i in range(150):
        cust_id, cust_name, channel = customers[i % len(customers)]
        amt = np.random.uniform(50000, 500000)
        inv_date = start_date + timedelta(days=np.random.randint(0, 60))
        trans = Transaction(
            invoice_no=f"INV-{2024}{str(i+1).zfill(4)}",
            date=inv_date,
            customer=cust_name,
            channel=channel,
            amount=round(amt, 2),
            quantity=np.random.randint(100, 2000),
            status="Pending"
        )
        transactions.append(trans)
        
        # 35% chance of mismatch
        if np.random.random() < 0.35:
            mtype = np.random.choice(list(MismatchType))
            diff_percent = np.random.uniform(0.02, 0.15)
            cust_amt = amt * (1 - diff_percent)
            sev = np.random.choice(["high", "medium", "low"], p=[0.2, 0.5, 0.3])
            mismatches.append(Mismatch(
                invoice_no=trans.invoice_no,
                customer=cust_name,
                company_amt=round(amt, 2),
                customer_amt=round(cust_amt, 2),
                diff=round(amt - cust_amt, 2),
                mismatch_type=mtype,
                severity=sev,
                status=np.random.choice(["Open", "In Progress", "Resolved"])
            ))
    return transactions, mismatches

# ------------------------ ANALYTICS ENGINE ---------------------------
def calculate_metrics(transactions, mismatches):
    total_receivables = sum(t.amount for t in transactions)
    total_mismatch_value = sum(abs(m.diff) for m in mismatches)
    
    # Aging buckets
    aging = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
    today = datetime.now()
    for t in transactions:
        days = (today - t.date).days
        if days <= 30: aging["0-30"] += t.amount
        elif days <= 60: aging["31-60"] += t.amount
        elif days <= 90: aging["61-90"] += t.amount
        else: aging["90+"] += t.amount
    
    # Channel wise
    channel_data = {}
    for t in transactions:
        channel_data[t.channel] = channel_data.get(t.channel, 0) + t.amount
    
    # Severity counts
    sev_count = {"high":0, "medium":0, "low":0}
    for m in mismatches:
        sev_count[m.severity] += 1
    
    recon_rate = (1 - len(mismatches)/len(transactions)) * 100 if transactions else 0
    return {
        "total_receivables": total_receivables,
        "blocked_capital": total_mismatch_value,
        "aging": aging,
        "channel_data": channel_data,
        "severity": sev_count,
        "recon_rate": recon_rate,
        "total_invoices": len(transactions),
        "total_mismatches": len(mismatches)
    }

# ------------------------ DASHBOARD UI --------------------------------
def main():
    # Initialize session
    if "data_loaded" not in st.session_state:
        st.session_state.transactions, st.session_state.mismatches = generate_data()
        st.session_state.data_loaded = True
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🏢 MARICO")
        st.markdown("---")
        page = st.radio("📌 Navigation", ["🏠 Dashboard", "📊 Reconciliation", "⚖️ Claims", "🏢 Customer View"])
        st.markdown("---")
        channel_filter = st.multiselect("Channel", ["OT", "MT", "D2C"], default=["OT", "MT", "D2C"])
        severity_filter = st.multiselect("Severity", ["high", "medium", "low"], default=["high", "medium", "low"])
        if st.button("🔄 Refresh Data"):
            st.session_state.transactions, st.session_state.mismatches = generate_data()
            st.rerun()
    
    # Apply filters
    filtered_trans = [t for t in st.session_state.transactions if t.channel in channel_filter]
    filtered_mis = [m for m in st.session_state.mismatches if m.severity in severity_filter]
    metrics = calculate_metrics(filtered_trans, filtered_mis)
    
    # Create dataframe for display (dictionary version for easy access)
    mismatches_dict = []
    for m in filtered_mis:
        mismatches_dict.append({
            "Invoice": m.invoice_no,
            "Customer": m.customer,
            "Company (₹)": f"₹{m.company_amt:,.0f}",
            "Customer (₹)": f"₹{m.customer_amt:,.0f}",
            "Difference (₹)": f"₹{abs(m.diff):,.0f}",
            "Type": m.mismatch_type.value,
            "Severity": m.severity.upper(),
            "Status": m.status,
            "DiffValue": m.diff,  # numeric for calculations
            "CompanyNum": m.company_amt,
            "CustomerNum": m.customer_amt
        })
    df_mis = pd.DataFrame(mismatches_dict)
    
    # --------------------- PAGE: DASHBOARD -----------------------------
    if page == "🏠 Dashboard":
        st.markdown("""
        <div class="main-header">
            <h1>🔄 Marico Intelligent Reconciliation System</h1>
            <p>Organised Trade · Modern Trade · D2C Channels</p>
        </div>
        """, unsafe_allow_html=True)
        
        # KPI Row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""<div class="metric-card info-card">
            <h3>💰 Total Receivables</h3>
            <h2>₹{metrics['total_receivables']/1e5:.1f}L</h2>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card warning-card">
            <h3>⚠️ Blocked Capital</h3>
            <h2>₹{metrics['blocked_capital']/1e5:.1f}L</h2>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="metric-card success-card">
            <h3>📊 Recon Rate</h3>
            <h2>{metrics['recon_rate']:.1f}%</h2>
            </div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(f"""<div class="metric-card">
            <h3>📄 Open Mismatches</h3>
            <h2>{metrics['total_mismatches']}</h2>
            </div>""", unsafe_allow_html=True)
        
        # Charts Row
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(x=list(metrics['aging'].keys()), y=list(metrics['aging'].values()),
                         title="📈 Aging Analysis", labels={'x':'Bucket', 'y':'Amount (₹)'})
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.pie(values=list(metrics['channel_data'].values()), 
                         names=list(metrics['channel_data'].keys()), title="🏢 Channel-wise Revenue")
            st.plotly_chart(fig2, use_container_width=True)
        
        # Mismatch Table
        st.subheader("📋 Recent Mismatches")
        st.dataframe(df_mis[['Invoice', 'Customer', 'Company (₹)', 'Customer (₹)', 
                            'Difference (₹)', 'Type', 'Severity', 'Status']].head(15), 
                    use_container_width=True)
    
    # --------------------- PAGE: RECONCILIATION -------------------------
    elif page == "📊 Reconciliation":
        st.header("📊 Auto Reconciliation Engine")
        
        colA, colB = st.columns(2)
        with colA:
            st.subheader("📤 Marico Records")
            df_comp = pd.DataFrame([{
                "Invoice": t.invoice_no, 
                "Customer": t.customer,
                "Amount": f"₹{t.amount:,.0f}", 
                "Date": t.date.strftime("%Y-%m-%d"),
                "Channel": t.channel
            } for t in filtered_trans[:20]])
            st.dataframe(df_comp, use_container_width=True)
        
        with colB:
            st.subheader("📥 Customer Records")
            cust_rec = []
            for t in filtered_trans[:20]:
                reported = t.amount * np.random.uniform(0.9, 1.05)
                cust_rec.append({
                    "Invoice Ref": t.invoice_no,
                    "Customer": t.customer,
                    "Reported Amt": f"₹{reported:,.0f}",
                    "Status": "Reported"
                })
            st.dataframe(pd.DataFrame(cust_rec), use_container_width=True)
        
        if st.button("▶️ Run Reconciliation", use_container_width=True):
            progress = st.progress(0)
            for i in range(100):
                progress.progress(i+1)
            st.success(f"✅ Reconciliation complete! Found {len(filtered_mis)} mismatches.")
        
        st.subheader("🔍 Mismatch Report")
        st.dataframe(df_mis[['Invoice', 'Customer', 'Company (₹)', 'Customer (₹)', 
                            'Difference (₹)', 'Type', 'Severity', 'Status']], 
                    use_container_width=True)
        
        csv = df_mis.to_csv(index=False)
        st.download_button("📥 Download Mismatch Report (CSV)", csv, 
                          f"marico_mismatch_{datetime.now().strftime('%Y%m%d')}.csv", 
                          "text/csv")
    
    # --------------------- PAGE: CLAIMS ---------------------------------
    elif page == "⚖️ Claims":
        st.header("⚖️ Claims Resolution Workflow")
        
        # Filter open claims
        open_claims_df = df_mis[df_mis['Status'] != 'Resolved']
        
        if len(open_claims_df) == 0:
            st.success("🎉 No open claims! All issues resolved.")
        else:
            st.info(f"📋 Total open claims: {len(open_claims_df)}")
            
            for idx, claim in open_claims_df.iterrows():
                with st.expander(f"🔍 {claim['Invoice']} - {claim['Customer']} - {claim['Difference (₹)']}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Company Amount", claim['Company (₹)'])
                    with col2:
                        st.metric("Customer Amount", claim['Customer (₹)'])
                    with col3:
                        st.metric("Difference", claim['Difference (₹)'])
                    
                    st.markdown(f"**Type:** {claim['Type']}  |  **Severity:** {claim['Severity']}")
                    
                    # AI Recommendations
                    st.markdown("#### 🤖 AI-Powered Recommendations")
                    if "Price" in claim['Type']:
                        st.info("• Verify master pricing data\n• Check for active promotions/discounts\n• Review customer contract terms")
                    elif "Quantity" in claim['Type']:
                        st.info("• Verify delivery quantity from warehouse\n• Check Proof of Delivery (POD)\n• Contact logistics partner")
                    elif "Logistics" in claim['Type']:
                        st.info("• Review transit insurance claim\n• Verify delivery timeline\n• Check for damages during transit")
                    elif "Damage" in claim['Type']:
                        st.info("• Request damage assessment report\n• Verify product return status\n• Process credit note")
                    else:
                        st.info("• Request customer statement\n• Validate claim supporting documents\n• Schedule joint reconciliation meeting")
                    
                    # Action buttons
                    colA, colB, colC = st.columns(3)
                    if colA.button(f"✅ Approve & Resolve", key=f"approve_{idx}"):
                        st.success(f"Claim {claim['Invoice']} approved and resolved!")
                    if colB.button(f"📝 Raise Dispute", key=f"dispute_{idx}"):
                        st.warning(f"Dispute raised for {claim['Invoice']}")
                    if colC.button(f"🤝 Initiate Negotiation", key=f"negotiate_{idx}"):
                        st.info(f"Negotiation initiated with {claim['Customer']}")
                    st.markdown("---")
    
    # --------------------- PAGE: CUSTOMER VIEW --------------------------
    else:
        st.header("🏢 Customer Self-Service Portal")
        
        # Get unique customers
        customers = list(set(t.customer for t in filtered_trans))
        selected_customer = st.selectbox("Select Customer", customers)
        
        if selected_customer:
            # Get customer transactions
            cust_trans = [t for t in filtered_trans if t.customer == selected_customer]
            
            # Get customer mismatches from dataframe
            cust_mis_df = df_mis[df_mis['Customer'] == selected_customer]
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Invoices", len(cust_trans))
            with col2:
                total_value = sum(t.amount for t in cust_trans)
                st.metric("Total Value", f"₹{total_value:,.0f}")
            with col3:
                st.metric("Open Issues", len(cust_mis_df[cust_mis_df['Status'] != 'Resolved']))
            with col4:
                total_dispute = abs(cust_mis_df['DiffValue'].sum()) if len(cust_mis_df) > 0 else 0
                st.metric("Disputed Amount", f"₹{total_dispute:,.0f}")
            
            # Transaction History
            st.subheader("📄 Transaction History")
            trans_df = pd.DataFrame([{
                "Invoice": t.invoice_no,
                "Date": t.date.strftime("%d-%b-%Y"),
                "Amount": f"₹{t.amount:,.0f}",
                "Channel": t.channel,
                "Status": t.status
            } for t in cust_trans])
            st.dataframe(trans_df, use_container_width=True)
            
            # Open Issues
            if len(cust_mis_df) > 0:
                st.subheader("⚠️ Your Open Reconciliation Issues")
                st.dataframe(cust_mis_df[['Invoice', 'Company (₹)', 'Customer (₹)', 
                                         'Difference (₹)', 'Type', 'Severity', 'Status']], 
                            use_container_width=True)
                
                # Resolution progress
                resolved_count = len(cust_mis_df[cust_mis_df['Status'] == 'Resolved'])
                open_count = len(cust_mis_df[cust_mis_df['Status'] != 'Resolved'])
                
                fig = go.Figure(data=[go.Pie(
                    labels=['Resolved', 'Open'],
                    values=[resolved_count, open_count],
                    hole=0.4,
                    marker_colors=['#10b981', '#ef4444']
                )])
                fig.update_layout(title="Your Claims Resolution Status", height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ No open issues! All your transactions are reconciled.")

if __name__ == "__main__":
    main()
