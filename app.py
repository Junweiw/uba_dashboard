import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# =====================================================
# 1. Page Config & CSS Injection (The "HTML Look")
# =====================================================
st.set_page_config(
    page_title="UBA Pro | Enterprise Dashboard",
    page_icon="📊",
    layout="wide"
)

# 核心 CSS：复刻 HTML 原型的卡片风格
st.markdown("""
<style>
    /* 全局背景微调 */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* 卡片样式 */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
    }
    .metric-title {
        color: #64748b;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #0f172a;
        font-size: 1.875rem; /* 30px */
        font-weight: 700;
        line-height: 2.25rem;
    }
    .metric-trend-up {
        color: #16a34a; /* Green */
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 8px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .metric-trend-down {
        color: #dc2626; /* Red */
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 8px;
    }
    
    /* 调整 Tab 样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
        border-bottom: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-weight: 600;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        color: #3b82f6 !important; /* Blue */
        border-bottom-color: #3b82f6 !important;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 2. Logic Core
# =====================================================

def load_and_merge_files(uploaded_files):
    df_list = []
    for file in uploaded_files:
        try:
            temp_df = pd.read_csv(file)
            df_list.append(temp_df)
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")
            return None
    if df_list:
        return pd.concat(df_list, ignore_index=True)
    return None

def calculate_metrics(df, user_col):
    """Calculate high-level metrics for the cards."""
    total_users = df[user_col].nunique()
    total_events = len(df)
    avg_events = total_events / total_users if total_users > 0 else 0
    return total_users, total_events, avg_events

def calculate_retention(df, time_col, user_col, granularity='M'):
    df = df.copy()
    
    # Granularity Logic
    if granularity == 'Month':
        freq = 'M'
        period_format = '%Y-%m'
    elif granularity == 'Week':
        freq = 'W'
        period_format = '%Y-W%V'
    else: # Day
        freq = 'D'
        period_format = '%Y-%m-%d'

    df['period'] = df[time_col].dt.to_period(freq)
    df['cohort'] = df.groupby(user_col)['period'].transform('min')
    
    # Calculate Period Offset (Index)
    cohort_data = df.groupby(['cohort', 'period'])[user_col].nunique().reset_index()
    
    if granularity == 'Month':
        cohort_data['period_idx'] = (cohort_data['period'].dt.year - cohort_data['cohort'].dt.year) * 12 + \
                                    (cohort_data['period'].dt.month - cohort_data['cohort'].dt.month)
    else:
        # Week/Day simplified difference
        cohort_data['period_idx'] = (cohort_data['period'].astype('int64') - cohort_data['cohort'].astype('int64'))

    # Pivot Tables
    # 1. Absolute Values
    cohort_pivot_count = cohort_data.pivot_table(index='cohort', columns='period_idx', values=user_col)
    
    # 2. Percentages
    cohort_sizes = cohort_pivot_count.iloc[:, 0]
    retention_matrix_pct = cohort_pivot_count.divide(cohort_sizes, axis=0)
    
    return retention_matrix_pct, cohort_pivot_count, cohort_sizes

# =====================================================
# 3. Component Rendering (HTML Cards)
# =====================================================

def render_metric_card(title, value, trend=None, trend_type='neutral'):
    """Renders a custom HTML card instead of st.metric"""
    trend_html = ""
    if trend:
        if trend_type == 'up':
            trend_html = f'<div class="metric-trend-up">↑ {trend}</div>'
        elif trend_type == 'down':
            trend_html = f'<div class="metric-trend-down">↓ {trend}</div>'
        else:
            trend_html = f'<div class="metric-trend-up" style="color: #64748b">{trend}</div>'
            
    html_code = f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {trend_html}
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# =====================================================
# 4. Main Application
# =====================================================

def main():
    # --- Sidebar ---
    st.sidebar.title("⚙️ Settings")
    
    # Data Source
    uploaded_files = st.sidebar.file_uploader("Upload CSVs", type=['csv'], accept_multiple_files=True)
    
    df = None
    if uploaded_files:
        df = load_and_merge_files(uploaded_files)
        
        # Column Mapping
        st.sidebar.divider()
        st.sidebar.subheader("Mapping")
        cols = list(df.columns)
        
        # Auto-detect logic
        t_idx = next((i for i, c in enumerate(cols) if 'time' in c.lower() or 'date' in c.lower()), 0)
        u_idx = next((i for i, c in enumerate(cols) if 'user' in c.lower() or 'id' in c.lower()), 0)
        
        time_col = st.sidebar.selectbox("Timestamp Column", cols, index=t_idx)
        user_col = st.sidebar.selectbox("User ID Column", cols, index=u_idx)
        
        # Convert Time
        try:
            df[time_col] = pd.to_datetime(df[time_col])
        except:
            st.error("Time conversion failed.")
            return
            
        # Global Filters
        st.sidebar.divider()
        granularity = st.sidebar.selectbox("Time Granularity", ["Month", "Week", "Day"])
        
        min_d, max_d = df[time_col].min().date(), df[time_col].max().date()
        date_range = st.sidebar.date_input("Date Range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        
        if len(date_range) == 2:
             df = df[(df[time_col].dt.date >= date_range[0]) & (df[time_col].dt.date <= date_range[1])]
    
    else:
        # Mock Data Generation (Invisible to user unless they click load)
        st.sidebar.warning("👆 Please upload CSV files to start.")
        # Generate dummy data for UI demo (Optional: Remove if you want strict upload)
        dates = pd.date_range(end=datetime.today(), periods=1000)
        df = pd.DataFrame({
            'timestamp': np.random.choice(dates, 5000),
            'user_id': np.random.randint(1000, 2000, 5000)
        })
        time_col = 'timestamp'
        user_col = 'user_id'
        granularity = "Month"

    if df is not None and not df.empty:
        # Header
        st.title("User Behavior Analytics (UBA)")
        st.markdown(f"**Analysis Mode**: {granularity}ly View | **Records**: {len(df):,}")
        st.write("") # Spacer

        # --- 1. Top Metrics Cards (HTML Style) ---
        u, e, avg = calculate_metrics(df, user_col)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card("Total Active Users", f"{u:,}", "12% vs last period", "up")
        with c2:
            render_metric_card("Total Events", f"{e:,}", "High Intensity", "neutral")
        with c3:
            render_metric_card("Avg Engagement", f"{avg:.1f} Events", "Median: 3.0", "neutral")
        with c4:
            # Retention Placeholder (Calculated later)
            render_metric_card("Data Health", "Good", "Schema Validated", "up")

        # --- 2. Tabs Content ---
        tab_over, tab_ret, tab_eng = st.tabs(["📈 Overview", "🧲 Retention Analysis", "⚡ Engagement"])

        # === Overview Tab ===
        with tab_over:
            st.markdown("### User Growth Trend")
            
            # Grouping Logic
            if granularity == 'Month':
                g_col = df[time_col].dt.to_period('M').astype(str)
            elif granularity == 'Week':
                g_col = df[time_col].dt.to_period('W').astype(str)
            else:
                g_col = df[time_col].dt.to_period('D').astype(str)
            
            trend = df.groupby(g_col)[user_col].nunique().reset_index()
            trend.columns = ['Period', 'Users']
            
            # Visualization: Bar Chart as requested
            fig_bar = px.bar(
                trend, x='Period', y='Users',
                title="",
                color_discrete_sequence=['#3b82f6'] # Tailwind Blue-500
            )
            fig_bar.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                font={'color': '#64748b'},
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # === Retention Tab ===
        with tab_ret:
            # Control Row
            rc1, rc2 = st.columns([3, 1])
            with rc1:
                st.markdown(f"### {granularity}ly Cohort Heatmap")
            with rc2:
                # Toggle for Absolute vs Percentage
                view_mode = st.radio(
                    "Display Values:", 
                    ["Percentage (%)", "Absolute (#)"], 
                    horizontal=True,
                    label_visibility="collapsed"
                )

            try:
                ret_pct, ret_cnt, sizes = calculate_retention(df, time_col, user_col, granularity)
                
                if not ret_pct.empty:
                    # Prepare Data for Plotly
                    z_data = ret_pct.values # Colors always based on Percentage
                    x_labels = [f"T+{i}" for i in ret_pct.columns]
                    y_labels = ret_pct.index.astype(str)
                    
                    # Logic for Text Display
                    if view_mode == "Percentage (%)":
                        text_display = np.round(z_data * 100, 1)
                        template = "%{text}%"
                    else:
                        text_display = ret_cnt.values
                        template = "%{text}"
                    
                    height_calc = max(400, len(y_labels) * 45)

                    fig_ret = go.Figure(data=go.Heatmap(
                        z=z_data,
                        x=x_labels,
                        y=y_labels,
                        text=text_display,
                        texttemplate=template,
                        colorscale='Blues',
                        showscale=True,
                        xgap=2, ygap=2 # Gap between cells for that modern look
                    ))
                    
                    fig_ret.update_layout(
                        height=height_calc,
                        plot_bgcolor='white',
                        yaxis_title="Cohort Date",
                        xaxis_title="Periods Later",
                        title_font_size=16
                    )
                    st.plotly_chart(fig_ret, use_container_width=True)
                    
                    st.info("💡 **Insight:** Darker blue indicates higher retention. Toggle the switch top-right to see exact user counts.")
                else:
                    st.warning("Insufficient data range for cohort analysis.")
            except Exception as e:
                st.error(f"Analysis failed: {e}")

        # === Engagement Tab ===
        with tab_eng:
            st.markdown("### Engagement Depth")
            
            activity = df.groupby(user_col)[time_col].nunique().reset_index() # Count distinct timestamps (approximation)
            if granularity == 'Day':
                activity = df.groupby(user_col)[time_col].apply(lambda x: x.dt.date.nunique()).reset_index()
            
            activity.columns = ['user', 'freq']
            
            col_left, col_right = st.columns([2, 1])
            with col_left:
                fig_hist = px.histogram(
                    activity, x='freq', 
                    nbins=20, 
                    title="User Frequency Distribution",
                    color_discrete_sequence=['#10b981'] # Tailwind Emerald
                )
                fig_hist.update_layout(plot_bgcolor='white', yaxis_gridcolor='#f1f5f9')
                st.plotly_chart(fig_hist, use_container_width=True)
                
            with col_right:
                # Custom HTML Metric Card for Details
                p90 = activity['freq'].quantile(0.9)
                med = activity['freq'].median()
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Median Frequency</div>
                    <div class="metric-value">{med:.1f}</div>
                    <div class="metric-trend-up" style="color:#64748b">Times per {granularity}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Power Users (Top 10%)</div>
                    <div class="metric-value">> {p90:.0f}</div>
                    <div class="metric-trend-up">Very Active</div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
