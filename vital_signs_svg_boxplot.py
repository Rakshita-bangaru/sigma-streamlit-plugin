import streamlit as st
import pandas as pd
import html
import numpy as np

# Page Config
st.set_page_config(layout="wide", page_title="Box Plot - Vital Signs")

# Custom CSS for box plot visualization
st.markdown("""
<style>
    .main-header {
        font-size: 32px;
        font-weight: bold;
        color: white;
        background: linear-gradient(90deg, #1f3b8e 0%, #2b4bf2 100%);
        padding: 25px;
        text-align: center;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .kpi-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2b4bf2;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: bold;
        color: #1f3b8e;
        margin: 10px 0;
    }
    .kpi-label {
        font-size: 14px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .boxplot-container {
        background: white;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 20px 0;
        overflow-x: auto;
    }
    .box {
        display: inline-block;
        position: relative;
        margin: 0 8px;
        text-align: center;
    }
    .box-svg {
        height: 300px;
        display: flex;
        align-items: flex-end;
        justify-content: center;
    }
    .box-body {
        background: #2b4bf2;
        border: 2px solid #1f3b8e;
        border-radius: 3px;
        position: relative;
    }
    .whisker {
        position: absolute;
        background: #1f3b8e;
        width: 2px;
    }
    .median-line {
        position: absolute;
        background: #ff0000;
        width: 100%;
        height: 2px;
        top: 50%;
    }
    .outlier {
        position: absolute;
        width: 8px;
        height: 8px;
        background: #ff6b6b;
        border-radius: 50%;
        border: 2px solid #ff0000;
    }
    .label {
        font-size: 11px;
        margin-top: 10px;
        word-wrap: break-word;
        max-width: 60px;
        color: #333;
        font-weight: 500;
    }
    .stat-label {
        font-size: 12px;
        color: #666;
        margin-top: 5px;
    }
    .subheader-custom {
        font-size: 20px;
        font-weight: bold;
        color: #1f3b8e;
        margin-top: 30px;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 3px solid #2b4bf2;
    }
    .stat-table {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">💓 Systolic Blood Pressure Box Plot Dashboard</div>', unsafe_allow_html=True)

# Load data from Snowflake
@st.cache_data
def load_data():
    """Load data from Snowflake"""
    try:
        conn = st.connection("snowflake")
        query = """
            SELECT 
                EVENT_GROUP,
                EVENT,
                SYSTOLIC_BLOOD_PRESSURE_TRANS,
                SUBJECT
            FROM DEMO_STREAMLIT.DEMO.BOXPLOT
            WHERE SYSTOLIC_BLOOD_PRESSURE_TRANS IS NOT NULL
            ORDER BY EVENT_GROUP, EVENT
        """
        df = conn.query(query, ttl=600)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load the data
df = load_data()

if df is not None and len(df) > 0:
    # Convert to uppercase for consistency
    df.columns = df.columns.str.upper()
    
    # Prepare data
    df_subset = df[['EVENT_GROUP', 'EVENT', 'SYSTOLIC_BLOOD_PRESSURE_TRANS', 'SUBJECT']].copy()
    df_subset = df_subset.dropna(subset=['SYSTOLIC_BLOOD_PRESSURE_TRANS'])
    
    # Fill NaN values
    df_subset['EVENT_GROUP'] = df_subset['EVENT_GROUP'].fillna('Unknown')
    df_subset['EVENT'] = df_subset['EVENT'].fillna('Unknown')
    
    # Get unique combinations
    unique_groups = df_subset[['EVENT_GROUP', 'EVENT']].drop_duplicates().sort_values(by=['EVENT_GROUP', 'EVENT']).reset_index(drop=True)
    
    # Calculate statistics for all groups
    stats_list = []
    
    for _, row in unique_groups.iterrows():
        eg = row['EVENT_GROUP']
        ev = row['EVENT']
        
        group_data = df_subset[(df_subset['EVENT_GROUP'] == eg) & (df_subset['EVENT'] == ev)]
        values = group_data['SYSTOLIC_BLOOD_PRESSURE_TRANS'].values
        
        if len(values) == 0:
            continue
        
        # Calculate basic statistics
        min_val = float(min(values))
        max_val = float(max(values))
        mean_val = float(sum(values) / len(values))
        
        # Calculate median
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        if n % 2 == 0:
            median_val = float((sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2)
        else:
            median_val = float(sorted_vals[n//2])
        
        # Calculate Q1, Q3
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        q1 = float(sorted_vals[q1_idx])
        q3 = float(sorted_vals[q3_idx])
        iqr = q3 - q1
        
        # Count outliers
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = [v for v in values if v < lower_bound or v > upper_bound]
        
        # Calculate std dev
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = float(variance ** 0.5)
        
        stats_list.append({
            'Event Group': eg,
            'Event': ev,
            'Count': len(values),
            'Min': min_val,
            'Q1': q1,
            'Median': median_val,
            'Q3': q3,
            'Max': max_val,
            'Mean': mean_val,
            'Std Dev': std_dev,
            'Outliers': len(outliers),
            'Outlier Values': outliers,
            'Lower Bound': lower_bound,
            'Upper Bound': upper_bound
        })
    
    # ===== KPI SECTION =====
    st.markdown('<div class="subheader-custom">📊 Key Metrics</div>', unsafe_allow_html=True)
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    all_values = df_subset['SYSTOLIC_BLOOD_PRESSURE_TRANS'].values
    overall_mean = float(sum(all_values) / len(all_values))
    overall_sorted = sorted(all_values)
    overall_n = len(overall_sorted)
    if overall_n % 2 == 0:
        overall_median = float((overall_sorted[overall_n//2 - 1] + overall_sorted[overall_n//2]) / 2)
    else:
        overall_median = float(overall_sorted[overall_n//2])
    
    with kpi1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Total Records</div>
            <div class="kpi-value">{len(df_subset):,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Unique Subjects</div>
            <div class="kpi-value">{df_subset['SUBJECT'].nunique():,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Overall Mean</div>
            <div class="kpi-value">{overall_mean:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi4:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Overall Median</div>
            <div class="kpi-value">{overall_median:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ===== BOX PLOT VISUALIZATION =====
    st.markdown('<div class="subheader-custom">📈 Box Plot Visualization</div>', unsafe_allow_html=True)
    
    if stats_list:
        # Find overall min and max for scaling
        all_mins = [s['Min'] for s in stats_list]
        all_maxs = [s['Max'] for s in stats_list]
        overall_min = min(all_mins)
        overall_max = max(all_maxs)
        y_range = overall_max - overall_min
        
        # Create SVG box plots
        boxplot_html = '<div class="boxplot-container"><svg width="100%" height="400" style="background: white;">'
        
        box_width = 40
        x_start = 80
        x_spacing = 80
        y_start = 320
        y_scale = 250 / y_range if y_range > 0 else 1
        
        for idx, stat in enumerate(stats_list):
            x_pos = x_start + (idx * x_spacing)
            
            # Calculate y positions (inverted because SVG y goes down)
            y_min = y_start - (stat['Min'] - overall_min) * y_scale
            y_q1 = y_start - (stat['Q1'] - overall_min) * y_scale
            y_median = y_start - (stat['Median'] - overall_min) * y_scale
            y_q3 = y_start - (stat['Q3'] - overall_min) * y_scale
            y_max = y_start - (stat['Max'] - overall_min) * y_scale
            
            # Draw whiskers (lines from min to max)
            boxplot_html += f'<line x1="{x_pos + box_width/2}" y1="{y_max}" x2="{x_pos + box_width/2}" y2="{y_min}" stroke="#1f3b8e" stroke-width="1" opacity="0.7"/>'
            
            # Draw top whisker cap
            boxplot_html += f'<line x1="{x_pos + box_width/4}" y1="{y_max}" x2="{x_pos + 3*box_width/4}" y2="{y_max}" stroke="#1f3b8e" stroke-width="2"/>'
            
            # Draw bottom whisker cap
            boxplot_html += f'<line x1="{x_pos + box_width/4}" y1="{y_min}" x2="{x_pos + 3*box_width/4}" y2="{y_min}" stroke="#1f3b8e" stroke-width="2"/>'
            
            # Draw box (Q1 to Q3)
            box_height = y_q1 - y_q3
            boxplot_html += f'<rect x="{x_pos}" y="{y_q3}" width="{box_width}" height="{box_height}" fill="#2b4bf2" stroke="#1f3b8e" stroke-width="2" opacity="0.8"/>'
            
            # Draw median line (red)
            boxplot_html += f'<line x1="{x_pos}" y1="{y_median}" x2="{x_pos + box_width}" y2="{y_median}" stroke="#ff0000" stroke-width="2"/>'
            
            # Draw outliers as red dots
            for outlier_val in stat['Outlier Values']:
                y_outlier = y_start - (outlier_val - overall_min) * y_scale
                boxplot_html += f'<circle cx="{x_pos + box_width/2}" cy="{y_outlier}" r="4" fill="#ff6b6b" stroke="#ff0000" stroke-width="1.5"/>'
            
            # Draw labels below
            label_text = f"{stat['Event']}"
            boxplot_html += f'<text x="{x_pos + box_width/2}" y="360" text-anchor="middle" font-size="11" fill="#333">{label_text}</text>'
            
            # Draw values above boxes
            boxplot_html += f'<text x="{x_pos + box_width/2}" y="{y_q3 - 10}" text-anchor="middle" font-size="10" fill="#1f3b8e" font-weight="bold">{stat["Median"]:.0f}</text>'
        
        # Draw y-axis
        boxplot_html += f'<line x1="50" y1="50" x2="50" y2="{y_start}" stroke="#333" stroke-width="2"/>'
        boxplot_html += f'<line x1="40" y1="{y_start}" x2="50" y2="{y_start}" stroke="#333" stroke-width="2"/>'
        
        # Draw y-axis labels
        for i in range(0, int(overall_max) + 20, 20):
            y_pos = y_start - (i - overall_min) * y_scale
            boxplot_html += f'<line x1="45" y1="{y_pos}" x2="50" y2="{y_pos}" stroke="#333" stroke-width="1"/>'
            boxplot_html += f'<text x="40" y="{y_pos + 5}" text-anchor="end" font-size="10" fill="#333">{i}</text>'
        
        boxplot_html += '</svg></div>'
        
        st.markdown(boxplot_html, unsafe_allow_html=True)
        
        # ===== STATISTICS TABLE =====
        st.markdown('<div class="subheader-custom">📋 Detailed Statistics</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-table">', unsafe_allow_html=True)
        
        header = "| Event | Count | Min | Q1 | Median | Q3 | Max | Mean | Std Dev | Outliers |"
        separator = "|---|---|---|---|---|---|---|---|---|---|"
        
        st.write(header)
        st.write(separator)
        
        for stat in stats_list:
            row = f"| {stat['Event']} | {stat['Count']} | {stat['Min']:.1f} | {stat['Q1']:.1f} | **{stat['Median']:.1f}** | {stat['Q3']:.1f} | {stat['Max']:.1f} | {stat['Mean']:.1f} | {stat['Std Dev']:.1f} | {stat['Outliers']} |"
            st.write(row)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.info("No data available to display.")
else:
    st.error("Unable to load data from Snowflake. Please check your connection and permissions.")
