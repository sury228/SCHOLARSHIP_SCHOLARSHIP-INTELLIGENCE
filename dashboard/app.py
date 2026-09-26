import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Ensure root package imports work
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import load_config
from database.db_manager import DBManager
from dashboard.components import (
    render_confidence_badge,
    render_evidence_card,
    render_change_timeline,
    get_confidence_badge_html
)
from crawler.source_classifier import classify_source_domain

st.set_page_config(
    page_title="Scholarship Intelligence | Premium Portal",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom Black & Gold Premium Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Dark Theme Background */
    .stApp {
        background-color: #0A0A0C !important;
        color: #E5E7EB !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Playfair Display', serif !important;
        color: #D4AF37 !important;
        letter-spacing: 0.5px;
    }

    /* Sidebar Background & Gold Border */
    section[data-testid="stSidebar"] {
        background-color: #111115 !important;
        border-right: 1px solid rgba(212, 175, 55, 0.25) !important;
    }

    /* Metric Cards - Black & Gold Glassmorphism */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #141418 0%, #0D0D10 100%) !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6) !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #D4AF37 !important;
        transform: translateY(-2px);
    }
    div[data-testid="stMetricValue"] {
        color: #FFD700 !important;
        font-family: 'Playfair Display', serif !important;
        font-weight: 700 !important;
        font-size: 28px !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #AA771C !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Buttons - Metallic Gold Gradient */
    div.stButton > button {
        background: linear-gradient(135deg, #BF953F 0%, #FCF6BA 50%, #B38728 100%) !important;
        color: #0A0A0C !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        border: 1px solid #FFD700 !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2) !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #FCF6BA 0%, #BF953F 50%, #F3E5AB 100%) !important;
        color: #000000 !important;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4) !important;
        transform: scale(1.02);
    }

    /* Input Controls & Selectboxes */
    div[data-baseweb="select"] > div {
        background-color: #141418 !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        color: #F3E5AB !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] span {
        color: #F3E5AB !important;
    }

    /* Bordered Container Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(145deg, #141419 0%, #0D0D12 100%) !important;
        border: 1px solid rgba(212, 175, 55, 0.25) !important;
        border-radius: 12px !important;
        padding: 6px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
        transition: all 0.25s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(212, 175, 55, 0.6) !important;
        box-shadow: 0 6px 25px rgba(212, 175, 55, 0.15) !important;
    }

    /* Tabs Styling */
    button[data-baseweb="tab"] {
        color: #9CA3AF !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
    }
    button[aria-selected="true"] {
        color: #FFD700 !important;
        border-bottom-color: #D4AF37 !important;
    }

    /* Dividers */
    hr {
        border-color: rgba(212, 175, 55, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Load configuration and DB manager
config = load_config()
db_manager = DBManager(config["database"]["db_path"])

# Header Section
st.markdown("<h1 style='text-align: center; font-size: 38px; margin-bottom: 4px;'>👑 SCHOLARSHIP INTELLIGENCE</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #AA771C; font-size: 15px; font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 30px;'>Automated Verification & Anti-Hallucination Monitoring System</p>", unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.markdown("<h3 style='font-size: 20px;'>👑 CONTROL PANEL</h3>", unsafe_allow_html=True)

all_scholarships = db_manager.get_all_scholarships()

# Filter Options
status_options = ["ALL", "VERIFIED", "REVIEW_REQUIRED", "EXPIRING_SOON", "EXPIRED", "NO_LONGER_VERIFIABLE"]
selected_status = st.sidebar.selectbox("Filter Status", status_options)

source_options = ["ALL", "Government", "University", "Corporate CSR", "Trust / NGO", "Aggregator"]
selected_source = st.sidebar.selectbox("Filter Category", source_options)

min_score = st.sidebar.slider("Min Confidence Score (%)", 0.0, 100.0, 0.0)

# Filter Data
filtered = list(all_scholarships)

if selected_status != "ALL":
    filtered = [s for s in filtered if s["status"] == selected_status]

if selected_source != "ALL":
    filtered = [s for s in filtered if classify_source_domain(s["official_source_url"]) == selected_source]

filtered = [s for s in filtered if (s["confidence_score"] or 0) >= min_score]

# Top Metrics Overview
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Listings", len(all_scholarships))
m2.metric("Verified (≥95%)", sum(1 for s in all_scholarships if s["status"] == "VERIFIED"))
m3.metric("Review Required", sum(1 for s in all_scholarships if s["status"] == "REVIEW_REQUIRED"))
m4.metric("Expiring Soon", sum(1 for s in all_scholarships if s["status"] == "EXPIRING_SOON"))

st.markdown("<br/>", unsafe_allow_html=True)

# Main Dashboard Content
if not filtered:
    st.info("No scholarship records match the active gold filter criteria.")
else:
    col_list, col_divider, col_detail = st.columns([1.15, 0.05, 1.8], gap="medium")
    
    selected_id = st.session_state.get("selected_id", filtered[0]["id"] if filtered else None)
    
    with col_list:
        st.markdown("<h3 style='font-size: 22px; border-bottom: 2px solid #D4AF37; padding-bottom: 6px; margin-bottom: 16px;'>📋 Listings</h3>", unsafe_allow_html=True)
        for sch in filtered:
            badge_html = get_confidence_badge_html(sch['confidence_score'] or 0.0, sch['status'])
            is_active = (selected_id == sch['id'])
            
            with st.container(border=True):
                active_chip = "<span style='color: #FFD700; font-size: 11px; font-weight: 700; background: rgba(212,175,55,0.15); border: 1px solid #D4AF37; padding: 2px 8px; border-radius: 10px;'>SELECTED</span>" if is_active else ""
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                    <h4 style="margin: 0; font-size: 17px; color: #FFFFFF; font-weight: 600; line-height: 1.35;">{sch['name']}</h4>
                    {active_chip}
                </div>
                <div style="margin-bottom: 8px;">
                    {badge_html}
                </div>
                <p style="margin: 0 0 8px 0; font-size: 13px; color: #AA771C;">
                    🏛️ Provider: <strong style="color: #F3E5AB;">{sch['provider']}</strong> | 🌐 <span style="color: #D4AF37;">{classify_source_domain(sch['official_source_url'])}</span>
                </p>
                <div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(212, 175, 55, 0.15); border-radius: 8px; padding: 8px 12px; margin-bottom: 10px; font-size: 13px; color: #D1D5DB;">
                    💰 Amount: <strong style="color: #FFD700;">{sch['amount'] or 'N/A'}</strong> &nbsp;|&nbsp; 📅 Deadline: <strong style="color: #FFD700;">{sch['deadline'] or 'N/A'}</strong>
                </div>
                <div style="margin-bottom: 12px; word-break: break-all;">
                    <a href="{sch['official_source_url']}" target="_blank" style="color: #D4AF37; text-decoration: none; font-weight: 600; font-size: 12.5px;">
                        🔗 <span style="text-decoration: underline; color: #FCF6BA;">{sch['official_source_url']}</span> ➔
                    </a>
                </div>
                """, unsafe_allow_html=True)
                
                btn_label = "👉 Currently Inspecting" if is_active else "🔍 Inspect Details"
                if st.button(btn_label, key=f"btn_{sch['id']}", use_container_width=True, disabled=is_active):
                    st.session_state["selected_id"] = sch["id"]
                    st.rerun()

    with col_divider:
        st.markdown("""
        <div style="display: flex; justify-content: center; height: 100%; min-height: 700px; padding-top: 20px;">
            <div style="border-left: 2px solid rgba(212, 175, 55, 0.3); height: 100%; width: 1px;"></div>
        </div>
        """, unsafe_allow_html=True)

    with col_detail:
        if selected_id:
            sch_detail = db_manager.get_scholarship_by_id(selected_id)
            if sch_detail:
                st.markdown(f"<h3 style='font-size: 22px; border-bottom: 2px solid #D4AF37; padding-bottom: 6px; margin-bottom: 16px;'>📌 Inspection: {sch_detail['name']}</h3>", unsafe_allow_html=True)
                
                tab_info, tab_evidence, tab_history = st.tabs(["💎 Attributes", "✨ Evidence Quotes", "📜 Audit Log"])
                
                with tab_info:
                    st.markdown(f"""
                    <div style="background:#141418; border:1px solid rgba(212,175,55,0.2); padding:18px; border-radius:10px; margin-top:10px;">
                        <p><strong style="color:#D4AF37;">Provider:</strong> {sch_detail['provider']}</p>
                        <p><strong style="color:#D4AF37;">Benefit / Amount:</strong> {sch_detail['amount'] or 'Not specified'}</p>
                        <p><strong style="color:#D4AF37;">Academic Criteria:</strong> {sch_detail['eligibility_academic'] or 'Open to all'}</p>
                        <p><strong style="color:#D4AF37;">Income Limit:</strong> {sch_detail['eligibility_income'] or 'Not specified'}</p>
                        <p><strong style="color:#D4AF37;">Other Requirements:</strong> {sch_detail['eligibility_other'] or 'N/A'}</p>
                        <p><strong style="color:#D4AF37;">Application Deadline:</strong> {sch_detail['deadline'] or 'Open'}</p>
                        <p><strong style="color:#D4AF37;">Last Verified:</strong> {sch_detail['last_verified']}</p>
                        <p><strong style="color:#D4AF37;">Official URL:</strong> <a href="{sch_detail['official_source_url']}" target="_blank" style="color:#FCF6BA;">{sch_detail['official_source_url']}</a></p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with tab_evidence:
                    evidence_list = db_manager.get_evidence_for_scholarship(selected_id)
                    render_evidence_card(evidence_list)
                
                with tab_history:
                    history_list = db_manager.get_change_history(selected_id)
                    render_change_timeline(history_list)

# Sidebar Execution Button
st.sidebar.markdown("---")
if st.sidebar.button("👑 Trigger Crawler Pipeline"):
    st.sidebar.warning("Executing crawler pipeline...")
    from pipeline import ScholarshipPipeline
    pipeline = ScholarshipPipeline()
    results = pipeline.run_pipeline()
    st.sidebar.success(f"Crawler complete! Updated {len(results)} records.")
    st.rerun()
