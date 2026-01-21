import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Set page config
st.set_page_config(page_title="Sigma Streamlit Plugin", layout="wide")

# --- Sigma Integration Javascript ---
# This script handles communication with Sigma Computing
sigma_script = """
<script src="https://files.sigmacomputing.com/release/sigma-plugin-api-1.0.min.js"></script>
<script>
  // Initialize Sigma API
  sigma.utils.init();

  // Listen for data updates from Sigma
  sigma.plugin.on('change', (event) => {
    const data = event.data;
    console.log("Data received from Sigma:", data);
    
    // Send data to Streamlit via query parameters or a custom event
    // For this demo, we'll try to update query params which Streamlit can read
    const params = new URLSearchParams(window.location.search);
    params.set('sigma_data', JSON.stringify(data));
    window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`);
    
    // Force a Streamlit rerun by clicking a hidden button if needed
    // or just let Streamlit detect query param changes
  });
</script>
"""

# Inject the script
st.components.v1.html(sigma_script, height=0)

# --- App Content (Based on Snowflake Demo) ---

st.title(f"Example Streamlit App :balloon: {st.__version__}")
st.write(
    """This app is integrated with **Sigma Computing**! 
    Map your Sigma columns to the plugin to see live data here.
    """
)

# Get data from Sigma (via query params for this simple implementation)
# In a production app, you might use a more robust custom component.
sigma_raw_data = st.query_params.get("sigma_data", None)

if sigma_raw_data:
    try:
        import json
        data = json.loads(sigma_raw_data)
        # Assuming data comes in as { "columns": { "col1": [...], "col2": [...] } }
        df = pd.DataFrame(data.get("columns", {}))
        st.success("Connected to Sigma Data!")
    except Exception as e:
        df = None
        st.error(f"Error parsing Sigma data: {e}")
else:
    # Fallback to Dummy Data (Snowflake Demo Style)
    hifives_val = st.slider(
        "Number of high-fives in Q3",
        min_value=0,
        max_value=90,
        value=60,
        help="Use this to enter the number of high-fives you gave in Q3"
    )
    
    data = {
        "HIGH_FIVES": [50, 20, hifives_val],
        "FIST_BUMPS": [25, 35, 30],
        "QUARTER": ["Q1", "Q2", "Q3"]
    }
    df = pd.DataFrame(data)
    st.info("Showing demo data. Connect this plugin in Sigma to see live data.")

# --- Visualization ---

st.subheader("Number of high-fives")

# Replicating the bar chart from the image
chart = alt.Chart(df).mark_bar(color="#1f77b4").encode(
    x=alt.X('QUARTER:N', title='Quarter'),
    y=alt.Y('HIGH_FIVES:Q', title='High-Fives'),
    tooltip=['QUARTER', 'HIGH_FIVES', 'FIST_BUMPS']
).properties(
    height=400
)

st.altair_chart(chart, use_container_width=True)

# Also show Fist Bumps if available
if "FIST_BUMPS" in df.columns:
    st.subheader("Comparison: High-Fives vs Fist Bumps")
    df_melted = df.melt('QUARTER', value_vars=['HIGH_FIVES', 'FIST_BUMPS'], var_name='Type', value_name='Count')
    comparison_chart = alt.Chart(df_melted).mark_bar().encode(
        x='QUARTER:N',
        y='Count:Q',
        color='Type:N',
        column='Type:N'
    ).properties(width=300)
    st.altair_chart(comparison_chart)

st.write("---")
st.caption("Sigma Plugin Integration Template")
