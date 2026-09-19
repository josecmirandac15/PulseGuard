import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(
    page_title="PulseGuard - Emergency Alert System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .alert-critical {
        background-color: #FF4B4B;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .alert-warning {
        background-color: #FFA726;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .alert-info {
        background-color: #42A5F5;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stMetric > div {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

API_URL = st.sidebar.text_input("API URL", value=os.getenv("API_URL", "http://localhost:8000"))

def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_stats():
    try:
        response = requests.get(f"{API_URL}/api/v1/dashboard/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_admissions(skip=0, limit=50):
    try:
        response = requests.get(f"{API_URL}/api/v1/admissions?skip={skip}&limit={limit}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"total": 0, "admissions": []}

def get_alerts(level=None, skip=0, limit=50):
    try:
        params = f"?skip={skip}&limit={limit}"
        if level:
            params += f"&level={level}"
        response = requests.get(f"{API_URL}/api/v1/alerts{params}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"total": 0, "alerts": []}

def get_alert_stats():
    try:
        response = requests.get(f"{API_URL}/api/v1/alerts/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

st.sidebar.markdown("---")
if check_api_health():
    st.sidebar.success("🟢 API Connected")
else:
    st.sidebar.error("🔴 API Disconnected")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏥 PulseGuard v2.0")
st.sidebar.markdown("hackIAthon Panamá 2026")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🚨 New Admission", "📋 Admissions", "⚠️ Alerts", "🔍 Admission Detail"]
)

if page == "📊 Dashboard":
    st.markdown('<div class="main-header">🚨 PulseGuard Dashboard</div>', unsafe_allow_html=True)
    
    stats = get_stats()
    alert_stats = get_alert_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = stats.get("total_admissions", 0) if stats else 0
        st.metric("Total Admissions", total)
    
    with col2:
        today = stats.get("today_admissions", 0) if stats else 0
        st.metric("Today", today)
    
    with col3:
        alert_total = stats.get("total_alerts", 0) if stats else 0
        st.metric("Total Alerts", alert_total)
    
    with col4:
        by_level = stats.get("alerts_by_level", {}) if stats else {}
        critical = by_level.get("critical", 0)
        st.metric("Critical Alerts", critical, delta=None if critical == 0 else f"+{critical}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Alerts by Level")
        if alert_stats and "alerts_by_level" in alert_stats:
            level_data = alert_stats["alerts_by_level"]
            if level_data:
                df_levels = pd.DataFrame(
                    list(level_data.items()),
                    columns=["Level", "Count"]
                )
                st.bar_chart(df_levels.set_index("Level"))
            else:
                st.info("No alerts yet")
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("Recent Alerts")
        alerts_data = get_alerts(limit=5)
        if alerts_data.get("alerts"):
            for alert in alerts_data["alerts"][:5]:
                level = alert.get("level", "info")
                icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(level, "⚪")
                st.markdown(f"{icon} **{alert.get('admission_id', 'N/A')}** - {alert.get('message', 'N/A')}")
        else:
            st.info("No recent alerts")

elif page == "🚨 New Admission":
    st.markdown('<div class="main-header">🚨 Register Emergency Admission</div>', unsafe_allow_html=True)
    
    with st.form("admission_form"):
        st.subheader("Patient Information")
        col1, col2 = st.columns(2)
        
        with col1:
            admission_id = st.text_input(
                "Admission ID",
                value=f"ADM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            patient_id = st.selectbox(
                "Patient ID",
                ["PAT-001", "PAT-002", "PAT-003", "PAT-004", "PAT-005", "PAT-006", "PAT-007", "PAT-008"]
            )
            policy_number = st.selectbox(
                "Policy Number",
                ["POL-2024-001", "POL-2024-002", "POL-2024-003", "POL-2024-004", "POL-2024-005",
                 "POL-2024-006", "POL-2024-007", "POL-2024-008"]
            )
        
        with col2:
            hospital_code = st.selectbox(
                "Hospital Code",
                ["HOSP-001", "HOSP-002", "HOSP-003"]
            )
            timestamp = st.datetime_input("Timestamp", value=datetime.now())
        
        st.subheader("Clinical Information")
        admission_reason = st.text_area(
            "Admission Reason",
            value="",
            placeholder="Describe the reason for emergency admission..."
        )
        
        symptoms = st.text_input(
            "Symptoms (comma-separated)",
            value="",
            placeholder="chest pain, dyspnea, fever..."
        )
        
        submitted = st.form_submit_button("🚨 Process Admission", type="primary", use_container_width=True)
        
        if submitted:
            if not admission_reason:
                st.error("Please enter admission reason")
            else:
                payload = {
                    "admission_id": admission_id,
                    "patient_id": patient_id,
                    "policy_number": policy_number,
                    "timestamp": timestamp.isoformat(),
                    "admission_reason": admission_reason,
                    "symptoms": [s.strip() for s in symptoms.split(",") if s.strip()],
                    "hospital_code": hospital_code
                }
                
                try:
                    with st.spinner("Processing admission..."):
                        response = requests.post(
                            f"{API_URL}/api/v1/webhook/admission",
                            json=payload,
                            timeout=30
                        )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("✅ Admission processed successfully!")
                        
                        st.markdown("---")
                        st.subheader("Processing Results")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Status", result["status"].upper())
                        with col2:
                            level = result["alert_level"]
                            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(level, "⚪")
                            st.metric("Alert Level", f"{icon} {level.upper()}")
                        with col3:
                            st.metric("Admission ID", result["admission_id"])
                        
                        st.info(f"**Message:** {result['message']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            hospital_status = "✅ Notified" if result.get("hospital_notified") else "❌ Failed"
                            st.metric("Hospital", hospital_status)
                        with col2:
                            insurer_status = "✅ Notified" if result.get("insurer_notified") else "❌ Failed"
                            st.metric("Insurer", insurer_status)
                        
                        if result.get("ai_report"):
                            st.subheader("AI Report")
                            st.markdown(result["ai_report"])
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to PulseGuard API. Check if API is running.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

elif page == "📋 Admissions":
    st.markdown('<div class="main-header">📋 Emergency Admissions</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        page_num = st.number_input("Page", min_value=1, value=1)
    with col2:
        per_page = st.selectbox("Per page", [10, 25, 50])
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    skip = (page_num - 1) * per_page
    data = get_admissions(skip=skip, limit=per_page)
    
    st.subheader(f"Total: {data.get('total', 0)} admissions")
    
    if data.get("admissions"):
        for adm in data["admissions"]:
            with st.expander(f"🏥 {adm['admission_id']} - {adm['patient_id']} ({adm.get('status', 'unknown')})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Patient:** {adm['patient_id']}")
                    st.write(f"**Policy:** {adm['policy_number']}")
                    st.write(f"**Hospital:** {adm['hospital_code']}")
                with col2:
                    st.write(f"**Reason:** {adm.get('admission_reason', 'N/A')}")
                    st.write(f"**Timestamp:** {adm.get('timestamp', 'N/A')}")
                    st.write(f"**Symptoms:** {', '.join(adm.get('symptoms', []))}")
                
                if st.button(f"View Details", key=f"detail_{adm['admission_id']}"):
                    st.session_state.selected_admission = adm['admission_id']
                    st.rerun()
    else:
        st.info("No admissions found")

elif page == "⚠️ Alerts":
    st.markdown('<div class="main-header">⚠️ System Alerts</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        level_filter = st.selectbox(
            "Filter by Level",
            ["All", "critical", "warning", "info"]
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    level = None if level_filter == "All" else level_filter
    data = get_alerts(level=level)
    
    st.subheader(f"Total: {data.get('total', 0)} alerts")
    
    if data.get("alerts"):
        for alert in data["alerts"]:
            level = alert.get("level", "info")
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(level, "⚪")
            
            with st.expander(f"{icon} {alert['admission_id']} - {level.upper()}"):
                st.write(f"**Message:** {alert.get('message', 'N/A')}")
                st.write(f"**Analysis:** {alert.get('agent_analysis', 'N/A')}")
                
                if alert.get("recommendations"):
                    st.write("**Recommendations:**")
                    for rec in alert["recommendations"]:
                        st.write(f"  - {rec}")
                
                col1, col2 = st.columns(2)
                with col1:
                    hosp = "✅" if alert.get("hospital_notified") else "❌"
                    st.write(f"**Hospital Notified:** {hosp}")
                with col2:
                    ins = "✅" if alert.get("insurer_notified") else "❌"
                    st.write(f"**Insurer Notified:** {ins}")
                
                if alert.get("ai_report"):
                    st.subheader("AI Report")
                    st.markdown(alert["ai_report"])
    else:
        st.info("No alerts found")

elif page == "🔍 Admission Detail":
    st.markdown('<div class="main-header">🔍 Admission Detail</div>', unsafe_allow_html=True)
    
    admission_id = st.text_input(
        "Admission ID",
        value=st.session_state.get("selected_admission", "")
    )
    
    if admission_id:
        try:
            response = requests.get(f"{API_URL}/api/v1/admissions/{admission_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                adm = data.get("admission", {})
                alerts = data.get("alerts", [])
                
                st.subheader("Admission Information")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Admission ID", adm.get("admission_id", "N/A"))
                    st.metric("Patient ID", adm.get("patient_id", "N/A"))
                with col2:
                    st.metric("Policy Number", adm.get("policy_number", "N/A"))
                    st.metric("Hospital Code", adm.get("hospital_code", "N/A"))
                with col3:
                    st.metric("Status", adm.get("status", "N/A").upper())
                    st.metric("Timestamp", adm.get("timestamp", "N/A"))
                
                st.subheader("Clinical Information")
                st.write(f"**Reason:** {adm.get('admission_reason', 'N/A')}")
                st.write(f"**Symptoms:** {', '.join(adm.get('symptoms', []))}")
                
                if adm.get("vital_signs"):
                    st.subheader("Vital Signs")
                    st.json(adm["vital_signs"])
                
                if alerts:
                    st.subheader(f"Alerts ({len(alerts)})")
                    for alert in alerts:
                        level = alert.get("level", "info")
                        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(level, "⚪")
                        
                        with st.expander(f"{icon} Alert: {level.upper()}"):
                            st.write(f"**Message:** {alert.get('message', 'N/A')}")
                            st.write(f"**Analysis:** {alert.get('agent_analysis', 'N/A')}")
                            
                            if alert.get("recommendations"):
                                st.write("**Recommendations:**")
                                for rec in alert["recommendations"]:
                                    st.write(f"  - {rec}")
                            
                            if alert.get("ai_report"):
                                st.subheader("AI Report")
                                st.markdown(alert["ai_report"])
                else:
                    st.info("No alerts for this admission")
            else:
                st.error(f"Admission not found: {admission_id}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to PulseGuard API")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>PulseGuard v2.0 - hackIAthon Panamá 2026 - Reto 4</div>",
    unsafe_allow_html=True
)
