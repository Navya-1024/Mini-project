import streamlit as st
import sqlite3
import pandas as pd

# Database Initialization
def init_db():
    conn = sqlite3.connect("blood_bank.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS donors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, 
                    age INTEGER, 
                    blood_group TEXT, 
                    contact TEXT,
                    blood_units INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, 
                    blood_group TEXT, 
                    contact TEXT,
                    units_requested INTEGER)''')
    
    conn.commit()
    conn.close()

# Add a new donor
def add_donor(name, age, blood_group, contact, units):
    conn = sqlite3.connect("blood_bank.db")
    c = conn.cursor()
    c.execute("INSERT INTO donors (name, age, blood_group, contact, blood_units) VALUES (?, ?, ?, ?, ?)", 
              (name, age, blood_group, contact, units))
    conn.commit()
    conn.close()

# Fetch all donors
def get_donors():
    conn = sqlite3.connect("blood_bank.db")
    df = pd.read_sql("SELECT * FROM donors", conn)
    conn.close()
    return df

# Request blood
def request_blood(name, blood_group, contact, units_requested):
    conn = sqlite3.connect("blood_bank.db")
    c = conn.cursor()
    
    # Check if enough blood is available
    c.execute("SELECT SUM(blood_units) FROM donors WHERE blood_group=?", (blood_group,))
    available_units = c.fetchone()[0] or 0
    
    if available_units >= units_requested:
        c.execute("INSERT INTO requests (name, blood_group, contact, units_requested) VALUES (?, ?, ?, ?)",
                  (name, blood_group, contact, units_requested))
        conn.commit()
        st.success(f"✅ Blood request placed successfully for {units_requested} units of {blood_group}!")
    else:
        st.error("❌ Not enough blood units available. Please try again later.")
    
    conn.close()

# Reduce blood units when a request is fulfilled
def fulfill_request(blood_group, units_requested):
    conn = sqlite3.connect("blood_bank.db")
    c = conn.cursor()
    
    c.execute("SELECT id, blood_units FROM donors WHERE blood_group=? AND blood_units > 0 ORDER BY blood_units DESC", 
              (blood_group,))
    donors = c.fetchall()
    
    units_needed = units_requested
    
    for donor_id, available_units in donors:
        if units_needed == 0:
            break
        if available_units >= units_needed:
            c.execute("UPDATE donors SET blood_units = blood_units - ? WHERE id = ?", (units_needed, donor_id))
            units_needed = 0
        else:
            c.execute("UPDATE donors SET blood_units = 0 WHERE id = ?", (donor_id,))
            units_needed -= available_units
    
    c.execute("DELETE FROM requests WHERE blood_group=? AND units_requested=?", (blood_group, units_requested))
    conn.commit()
    conn.close()
    st.success("🎉 Blood request fulfilled and removed from the queue!")

# Initialize database
init_db()

# Streamlit UI
st.set_page_config(page_title="Blood Bank Management", page_icon="🩸", layout="wide")

st.markdown(
    """
    <div style="text-align: center;">
        <h1 style="color: red; font-size: 50px;">🩸 Blood Bank Management System 🩸</h1>
        <h3 style="color: darkred;">Save a Life, Donate Blood ❤️</h3>
        <hr style="border: 2px solid red;">
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar Menu
menu = ["🏠 Home", "🩸 Register Donor", "📋 View Donors", "🔍 Search Blood", "🆘 Blood Requests"]
choice = st.sidebar.radio("Menu", menu)

if choice == "🏠 Home":
    st.image("https://www.redcrossblood.org/content/dam/redcrossblood/hero-images/why-give-blood-desktop.jpg", use_container_width=True)
    st.subheader("Welcome to the Blood Bank Management System")
    st.write("Find blood donors, request blood, and save lives!")

elif choice == "🩸 Register Donor":
    st.subheader("🩸 Donor Registration")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("👤 Name")
        age = st.number_input("🎂 Age", min_value=18, max_value=65, step=1)
    with col2:
        blood_group = st.selectbox("🩸 Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        contact = st.text_input("📞 Contact Number")
    
    units = st.number_input("🩸 Available Blood Units", min_value=0, max_value=10, step=1)

    if st.button("✅ Register"):
        if name and contact:
            add_donor(name, age, blood_group, contact, units)
            st.success("🎉 Donor Registered Successfully!")
        else:
            st.warning("⚠️ Please fill all fields.")

elif choice == "📋 View Donors":
    st.subheader("📋 List of Registered Donors")
    donors_df = get_donors()
    if donors_df.empty:
        st.warning("⚠️ No donors found. Please register donors.")
    else:
        st.dataframe(donors_df)

elif choice == "🔍 Search Blood":
    st.subheader("🔍 Search for Blood Donors")
    search_group = st.selectbox("Select Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
    
    if st.button("🔎 Search"):
        result_df = get_donors()
        filtered_df = result_df[result_df["blood_group"] == search_group]
        if not filtered_df.empty:
            st.dataframe(filtered_df)
        else:
            st.warning("⚠️ No donors found for this blood group.")

elif choice == "🆘 Blood Requests":
    st.subheader("🆘 Request Blood")
    req_name = st.text_input("👤 Your Name")
    req_blood_group = st.selectbox("🩸 Required Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
    req_contact = st.text_input("📞 Your Contact")
    req_units = st.number_input("🩸 Units Needed", min_value=1, max_value=5, step=1)

    if st.button("🆘 Request Blood"):
        request_blood(req_name, req_blood_group, req_contact, req_units)

    st.subheader("📋 Pending Blood Requests")
    conn = sqlite3.connect("blood_bank.db")
    df_requests = pd.read_sql("SELECT * FROM requests", conn)
    conn.close()
    
    if df_requests.empty:
        st.info("✅ No pending requests!")
    else:
        st.dataframe(df_requests)
        
        selected_request = st.selectbox("Select request to fulfill:", df_requests["id"].tolist())
        if st.button("✅ Fulfill Request"):
            req_info = df_requests[df_requests["id"] == selected_request].iloc[0]
            fulfill_request(req_info["blood_group"], req_info["units_requested"])
