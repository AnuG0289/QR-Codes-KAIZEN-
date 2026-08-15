import streamlit as st
from supabase import create_client, Client

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
    # LOCK ID INTO SESSION VAULT: Prevents data loss when the webpage reloads during PIN entry
    if "scanned_id" not in st.session_state:
        st.session_state["scanned_id"] = query_params["ID"].upper().strip()
        
    scanned_serial = st.session_state["scanned_id"]
    
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
            # 🌟 FIX: Grab the first element dictionary cleanly from the data list array
            record = vehicle_lookup.data[0]
            
            # Safely support both uppercase and lowercase column lookups from database
            license_plate = record.get("LICENSE_PLATE") or record.get("license_plate") or "N/A"
            registry_status = record.get("STATUS") or record.get("status") or "N/A"
            phone = record.get("CITIZEN_PHONE") or record.get("citizen_phone")
            
            st.write(f"**License Plate:** {license_plate}")
            st.write(f"**Registry Status:** {registry_status}")
            
            st.markdown("---")
            st.warning("⚠️ Pressing the button below will open a gateway to instantly alert the citizen via an automated voice response phone call.")
            
            # Formatted HTML code payload using the locked persistent session state variables
            html_button = f"""
            <form action="https://hook.us2.make.com/vjxo5n1cvabukj7mwoh73ggfhfwvgvpy" method="POST" target="_blank" style="margin:0;padding:0;">
                <input type="hidden" name="CITIZEN_PHONE" value="{phone}">
                <input type="hidden" name="ID" value="{st.session_state['scanned_id']}">
                <input type="hidden" name="API_KEY" value="MuniSecurePass2026!xY">
                <button type="submit" style="
                    width: 100%;
                    background-color: #FF4B4B;
                    color: white;
                    border: none;
                    padding: 14px 20px;
                    font-size: 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: bold;
                    box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
                ">🚨 Dispatch Emergency Notification Call</button>
            </form>
            """
            
            # Render the secure button on the page using a native iframe component
            st.components.v1.html(html_button, height=60)
            
        else:
            st.error(f"❌ System Error: Token ID '{scanned_serial}' does not exist in the municipal asset registry.")

# ==============================================================================
# ROUTE B: THE CITIZEN REGISTRATION VIEW (Triggered via Registration Sheet)
# ==============================================================================
else:
    st.title("📱 Citizen Vehicle Alert Activation Hub")
    st.write("Register your municipal QR sticker below to protect your vehicle from being fined or towing.")

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
            st.error("❌ Error: Serial Token ID and unique mobile number, and the FOIPPA consent check are strictly required.")
        else:
            sanitized_token_id = token_id.upper().strip()
            
            # Phone Number Cleansing Engine
            digits_only = "".join(char for char in phone_number if char.isdigit())
            
            if len(digits_only) == 10:
                sanitized_phone = f"+1{digits_only}"
            elif len(digits_only) == 11 and digits_only.startswith("1"):
                sanitized_phone = f"+{digits_only}"
            else:
                sanitized_phone = None

            if not sanitized_phone:
                st.error("❌ Error: Please enter a valid 10-digit North American phone number.")
            else:
                try:
                    check_phone = supabase.table("sticker_registry").select("CITIZEN_PHONE").eq("CITIZEN_PHONE", sanitized_phone).execute()
                    
                    if len(check_phone.data) > 0:
                        st.error("⚠️ This phone number is already registered to an active parking profile. Please input a unique number.")
                    else:
                        data = supabase.table("sticker_registry").update({
                            "CITIZEN_PHONE": sanitized_phone,
                            "LICENSE_PLATE": plate_number.upper().strip() if plate_number else "NOT-PROVIDED",
                            "STATUS": "Active"
                        }).eq("ID", sanitized_token_id).execute()
                        
                        if len(data.data) > 0:
                            st.success(f"🎉 Sticker '{sanitized_token_id}' Successfully Activated with phone {sanitized_phone}! You are now linked to the city grid.")
                        else:
                            st.error(f"❌ Error: Serial Token ID '{sanitized_token_id}' does not exist in the pre-loaded inventory database.")
                        
                except Exception as e:
                    st.error(f"Database Communication Error: {str(e)}")

# ==============================================================================
# TEMPORARY MUNICIPAL DATA INSPECTOR MODULE (DELETE BEFORE PRODUCTION)
# ==============================================================================
st.markdown("---")
st.subheader("⚙️ System Diagnostic Live Inspector")
try:
    debug_dump = supabase.table("sticker_registry").select("*").execute()
    if debug_dump.data:
        st.json(debug_dump.data)
except Exception as debug_err:
    st.error(f"Diagnostic Engine Failure: {str(debug_err)}")

