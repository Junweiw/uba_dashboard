import streamlit as st
import plotly.express as px
from src import data_loader, analytics, ui_components

st.set_page_config(page_title="UBA Pro", layout="wide", page_icon="🚀")
ui_components.inject_custom_css()

# Sidebar
with st.sidebar:
    st.title("🛠 Settings")
    uploaded_file = st.file_uploader("Upload Data", type=['csv', 'xlsx'])

# Data Logic
if uploaded_file:
    df = data_loader.load_data(uploaded_file)
else:
    df = data_loader.generate_mock_data()

# Main UI
st.title("🚀 User Behavior Analytics Pro")
st.markdown("---")

# KPIs
total, users = analytics.calculate_kpis(df)
c1, c2 = st.columns(2)
ui_components.card("Total Events", f"{total:,}", c1)
ui_components.card("Total Users", f"{users:,}", c2)

# Charts
st.markdown("### 📊 Analytics Overview")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Traffic Trend")
    trend = analytics.get_trend(df)
    fig = px.line(trend, x='event_time', y='count', template="plotly_white")
    fig.update_traces(line_color='#2563EB', line_width=3)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Event Mix")
    dist = analytics.get_distribution(df)
    fig2 = px.pie(dist, values='count', names='event_type', hole=0.5)
    st.plotly_chart(fig2, use_container_width=True)
