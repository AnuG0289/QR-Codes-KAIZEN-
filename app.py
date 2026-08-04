import streamlit as st
from supabase import create_client, Client

# Initialize Supabase Connection Safely via Streamlit Secrets
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_KEY"] # Use Service Key during sandbox testing
    return create_client(url, key)

supabase: Client = init_supabase()

st.title("📱 Citizen Vehicle Alert Activation Hub")
st.write("Register your municipal QR sticker below to protect your vehicle from towing.")

with st.form("activation_form", clear_on_submit=True):
    # Form input fields mapping to Supabase structure
    token_id = st.text_input("Enter the Serial Token ID (Printed on your sticker label)")
    phone_number = st.text_input("Enter your Mobile Number (e.g., +17785551234)")
    plate_number = st.text_input("Enter your License Plate (Optional Secondary Verification)")
    
    # FOIPPA Mandatory Consent Box
    consent = st.checkbox(
        "By checking this box, I voluntarily consent to store my mobile number and plate data "
        "on secure Canadian servers for the sole purpose of receiving emergency municipal vehicle blocking alerts."
    )
    
    submit_button = st.form_submit_button("Activate Sticker Successfully")

if submit_button:
    if not token_id or not phone_number or not consent:
        st.error("❌ Error: All fields and the FOIPPA consent check are strictly required.")
    else:
        try:
            # 1. Direct Duplicate Verification Check
            # Scan the table to see if this exact number is already claimed anywhere else
            check_phone = supabase.table("sticker_registry").select("CITIZEN_PHONE").eq("CITIZEN_PHONE", phone_number).execute()
            
            # If the database returns a matching record row, intercept it and block registration
            if len(check_phone.data) > 0:
                st.error("⚠️ This phone number is already registered to an active parking profile. Please input a unique number where you would like to receive notifications.")
            
            else:
                # 2. Proceed with Update only if the phone number is 100% unique
                data = supabase.table("sticker_registry").update({
                    "CITIZEN_PHONE": phone_number,
                    "license_plate": plate_number if plate_number else "NOT-PROVIDED",
                    "status": "Active"
                }).eq("id", token_id).execute()
                
                # Verify that a row matching the serial token actually existed and changed
                if len(data.data) > 0:
                    st.success("🎉 Sticker Successfully Activated! You are now linked to the city grid.")
                else:
                    st.error("❌ Error: Invalid Serial Token ID. Please verify your sticker print.")
                    
        except Exception as e:
            st.error(f"Database Communication Error: {str(e)}")
