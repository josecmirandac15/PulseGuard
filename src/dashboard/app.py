import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title="PulseGuard Dashboard",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 PulseGuard - Emergency Alert Dashboard")

API_URL = "http://localhost:8000"

tab1, tab2, tab3 = st.tabs(["New Admission", "Audit Logs", "System Status"])

with tab1:
    st.header("Register New Emergency Admission")

    with st.form("admission_form"):
        col1, col2 = st.columns(2)

        with col1:
            admission_id = st.text_input("Admission ID", value=f"ADM-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            patient_id = st.text_input("Patient ID", value="PAT-001")
            policy_number = st.text_input("Policy Number", value="POL-2024-001")
            hospital_code = st.text_input("Hospital Code", value="HOSP-001")

        with col2:
            admission_reason = st.text_area("Admission Reason", value="Chest pain and shortness of breath")
            symptoms = st.text_input("Symptoms (comma-separated)", value="chest pain, dyspnea, diaphoresis")
            timestamp = st.datetime_input("Timestamp", value=datetime.now())

        submitted = st.form_submit_button("Process Admission")

        if submitted:
            payload = {
                "admission_id": admission_id,
                "patient_id": patient_id,
                "policy_number": policy_number,
                "timestamp": timestamp.isoformat(),
                "admission_reason": admission_reason,
                "symptoms": [s.strip() for s in symptoms.split(",")],
                "hospital_code": hospital_code
            }

            try:
                response = requests.post(f"{API_URL}/webhook/admission", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Admission processed successfully!")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status", result["status"])
                    with col2:
                        alert_level = result.get("alert_level", "N/A")
                        color = {"info": "🟢", "warning": "🟡", "critical": "🔴"}.get(alert_level, "⚪")
                        st.metric("Alert Level", f"{color} {alert_level.upper()}")
                    with col3:
                        st.metric("Admission ID", result["admission_id"])

                    st.info(result["message"])
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to PulseGuard API. Make sure the API is running on port 8000.")

with tab2:
    st.header("Audit Logs")

    if st.button("Refresh Logs"):
        try:
            response = requests.get(f"{API_URL}/audit")
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])

                if logs:
                    df = pd.DataFrame(logs)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No audit logs found.")
            else:
                st.error("Error fetching audit logs")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to PulseGuard API.")

with tab3:
    st.header("System Status")

    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            st.success("✅ PulseGuard API is running")
            st.json(response.json())
        else:
            st.warning("⚠️ API responded with error")
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to PulseGuard API")

    st.subheader("Configuration")
    st.code(f"""
API URL: {API_URL}
Hospital Webhook: Configured
Insurer Webhook: Configured
Agent Model: GPT-4
    """)
