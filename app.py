import streamlit as st
from supabase import create_client, Client
import requests

# 1. Initialize Supabase Connection Safely via Streamlit Secrets
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# 2. Track the Officer's Shift Authentication State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# 3. Read the Web URL Query Parameters to Detect the Scan Type
query_params = st.query_params

# ==============================================================================
# ROUTE A: THE OFFICER ENFORCEMENT VIEW (Triggered via Windshield QR Code)
# ==============================================================================
if "ID" in query_params:
    # Force the URL input to be uppercase and stripped of accidental spaces
    scanned_serial = query_params["ID"].upper().strip()
    
    st.title("🚓 Municipal Enforcement Action Suite")
    st.write(f"Target Vehicle Serial Token ID: **{scanned_serial}**")
    
    # Check if the officer has logged in yet today
    if not st.session_state["authenticated"]:
        st.subheader("🔒 Security Verification Required")
        st.info("Please verify your municipal officer credentials to unlock enforcement triggers.")
        
        officer_pin = st.text_input("Enter 4-Digit Officer PIN:", type="password")
        if st.button("Verify Credentials"):
            if officer_pin == "0357": 
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Invalid PIN. Access Denied. Incident logged.")
                
    else:
        # Officer is authenticated! Display the secure action console.
        st.success("✅ Authorized Officer Status Active")
        
        # Look up the vehicle record in Supabase using the sanitized uppercase serial ID
        vehicle_lookup = supabase.table("sticker_registry").select("CITIZEN_PHONE", "LICENSE_PLATE", "STATUS").eq("ID", scanned_serial).execute()
        
        if len(vehicle_lookup.data) > 0:
            record = vehicle_lookup.data[0]
            
            # Safely support both uppercase and lowercase column lookups from database
            license_plate = record.get("LICENSE_PLATE") or record.get("license_plate") or "N/A"
            registry_status = record.get("STATUS") or record.get("status") or "N/A"
            phone = record.get("CITIZEN_PHONE") or record.get("citizen_phone")
            
            st.write(f"**License Plate:** {license_plate}")
            st.write(f"**Registry Status:** {registry_status}")
            
            st.markdown("---")
            st.warning("⚠️ Pressing the button below will instantly alert the citizen via an automated interactive voice response phone call.")
            
            # The Secure Production Button
            if st.button("🚨 Dispatch Emergency Notification Call", use_container_width=True):
                with st.spinner("Communicating with telecom networks..."):
                    try:
                        make_webhook_url = "https://make.com"
                        
                        # Print database keys to the UI so we can debug structure live
                        st.write("Debug - Data keys inside record are:", list(record.keys()))
                        st.write(f"Debug - Phone targeted: {phone}")
                        
                        payload = {
                            "CITIZEN_PHONE": phone,
                            "API_KEY": "MuniSecurePass2026!xY" 
                        }
                        
                        response = requests.post(make_webhook_url, json=payload)
                        
                        # Print what Make.com explicitly responded with
                        st.write(f"Debug - Make.com Status Code: {response.status_code}")
                        st.write(f"Debug - Make.com Raw Response: {response.text}")
                        
                        if response.status_code == 200 or response.text.lower() == "accepted":
                            st.success("🎉 Notification dispatch successfully initiated! Citizen's line is ringing.")
                        else:
                            st.error(f"Network Handshake Failed: {response.text}")
                    except Exception as call_err:
                        st.exception(call_err)
        else:
            st.error(f"❌ System Error: Token ID '{scanned_serial}' does not exist in the municipal asset registry.")

# ==============================================================================
# ROUTE B: THE CITIZEN REGISTRATION VIEW (Triggered via Registration Sheet)
# ==============================================================================
else:
    st.title("📱 Citizen Vehicle Alert Activation Hub")
    st.write("Register your municipal QR sticker below to protect your vehicle from towing.")

    with st.form("activation_form", clear_on_submit=True):
        token_id = st.text_input("Enter the Serial Token ID (Printed on your sticker label)")
        phone_number = st.text_input("Enter your Mobile Number (e.g., +17785551234)")
        plate_number = st.text_input("Enter your License Plate (Optional Secondary Verification)")
        
        consent = st.checkbox(
            "By checking this box, I voluntarily consent to store my mobile number and plate data "
            "on secure Canadian servers for the sole purpose of receiving emergency municipal vehicle blocking alerts."
        )
        
        submit_button = st.form_submit_button("Activate Sticker Successfully")

    if submit_button:
        if not token_id or not phone_number or not consent:
            st.error("❌ Error: All fields and the FOIPPA consent check are strictly required.")
        else:
            sanitized_token_id = token_id.upper().strip()
            
            try:
                # 1. Pre-registration unique phone check
                check_phone = supabase.table("sticker_registry").select("CITIZEN_PHONE").eq("CITIZEN_PHONE", phone_number).execute()
                
                if len(check_phone.data) > 0:
                    st.error("⚠️ This phone number is already registered to an active parking profile. Please input a unique number.")
                else:
                    # 2. Safe registration update using the sanitized uppercase token
                    data = supabase.table("sticker_registry").update({
                        "CITIZEN_PHONE": phone_number,
                        "LICENSE_PLATE": plate_number if plate_number else "NOT-PROVIDED",
                        "STATUS": "Active"
                    }).eq("ID", sanitized_token_id).execute()
                    
                    if len(data.data) > 0:
                        st.success(f"🎉 Sticker '{sanitized_token_id}' Successfully Activated! You are now linked to the city grid.")
                    else:
                        st.error(f"❌ Error: Serial Token ID '{sanitized_token_id}' does not exist in the pre-loaded inventory database.")
                        
            except Exception as e:
                st.error(f"Database Communication Error: {str(e)}")
