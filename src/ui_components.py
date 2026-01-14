import streamlit as st

def inject_custom_css():
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #eee;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-value {font-size: 24px; font-weight: bold; color: #2563EB;}
    .metric-label {font-size: 14px; color: #666;}
    </style>
    """, unsafe_allow_html=True)

def card(label, value, col):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)
