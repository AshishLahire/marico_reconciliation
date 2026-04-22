import streamlit as st
import pandas as pd

class BarcodeScanner:
    """QR/Barcode Scanner Module - Simulated & Real options"""
    
    def __init__(self):
        self.product_master = None
        
    def load_product_master(self, df):
        """Load product master database"""
        self.product_master = df
        
    def get_product_by_id(self, product_id):
        """Fetch product details by ID/SKU"""
        if self.product_master is not None:
            product = self.product_master[self.product_master['product_id'] == product_id]
            if not product.empty:
                return product.iloc[0].to_dict()
        return None
    
    def simulate_scan(self):
        """Simulate QR scan with input field (for demo)"""
        st.markdown("### 📷 Scan Product QR/Barcode")
        
        product_id = st.text_input(
            "Enter Scanned Product ID/SKU:",
            placeholder="e.g., PAR001, SVE001"
        )
        
        if product_id:
            product = self.get_product_by_id(product_id)
            if product:
                st.success(f"✅ Scanned: {product['product_name']} - ₹{product['mrp']}")
                return product
            else:
                st.error(f"❌ Product ID '{product_id}' not found in master database")
                return None
        return None
    
    def display_scan_instructions(self):
        """Show instructions for real camera scanning"""
        with st.expander("📱 How to scan using mobile camera"):
            st.write("**Option 1:** Use Python with OpenCV and pyzbar")
            st.write("**Option 2:** Use JavaScript with html5-qrcode")
            st.write("**For this demo:** Use the manual input field above")
    
    def generate_barcode_sample(self):
        """Generate sample barcode data for testing"""
        sample_barcodes = {
            "PAR001": "Parachute Coconut Oil",
            "SVE001": "Svelte Hair Oil", 
            "LIV001": "Livon Hair Serum",
            "SET001": "Set Wet Deodorant"
        }
        
        st.markdown("#### 🧪 Test Barcodes (for simulation)")
        
        cols = st.columns(4)
        idx = 0
        for code, name in sample_barcodes.items():
            with cols[idx % 4]:
                st.code(code)
                st.caption(name)
            idx += 1
