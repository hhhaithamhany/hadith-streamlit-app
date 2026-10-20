import streamlit as st
import pandas as pd
import gdown
import os
import gc

# 1. Page Configuration & Styling
st.set_page_config(page_title="Hadith & Explanation Browser", page_icon="📖", layout="wide")

st.markdown("""
<style>
    .hadith-card {
        background-color: #f8f9fa;
        border-right: 5px solid #1f77b4;
        padding: 15px;
        border-radius: 5px;
        font-size: 1.1em;
        margin-bottom: 20px;
        direction: rtl;
        text-align: right;
    }
    .explanation-card {
        background-color: #f0f4f8;
        border-right: 5px solid #2ca02c;
        padding: 15px;
        border-radius: 5px;
        font-size: 1.05em;
        margin-top: 10px;
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# 2. Memory-Optimized Data Loading Function
@st.cache_data(show_spinner=False)
def load_data():
    hadith_file_id = "13H7vPAZ6ZL_tBcuXSbohCH9MwXW1SZbn"
    exp_file_id = "1qAjLqJ218JWAZdq44xxBRMmUhKhFHDxV"
    
    hadith_path = "hadiths.parquet"
    exp_path = "explanations.parquet"
    
    if not os.path.exists(hadith_path) or os.path.getsize(hadith_path) == 0:
        gdown.download(f'https://drive.google.com/uc?id={hadith_file_id}', output=hadith_path, quiet=False)
            
    if not os.path.exists(exp_path) or os.path.getsize(exp_path) == 0:
        gdown.download(f'https://drive.google.com/uc?id={exp_file_id}', output=exp_path, quiet=False)
            
    # Load DataFrames
    df_h = pd.read_parquet(hadith_path)
    df_e = pd.read_parquet(exp_path)
    
    # ⚡ CRITICAL RAM OPTIMIZATION: Convert repetitive string columns to 'category' 
    # This reduces memory footprint by up to 70% to prevent OOM crashes on Streamlit Cloud
    for col in ['collection', 'source_name']:
        if col in df_h.columns:
            df_h[col] = df_h[col].astype('category')
        if col in df_e.columns:
            df_e[col] = df_e[col].astype('category')
            
    gc.collect()
    return df_h, df_e

try:
    df_hadiths, df_explanations = load_data()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# 3. Application UI
st.title("📖 Hadith & Explanation Browser")

# Step 1: Select Collection
st.subheader("Step 1: Select Collection")
collections = df_hadiths["collection"].unique().tolist()
selected_collection = st.selectbox("Choose Collection:", collections)

coll_hadiths = df_hadiths[df_hadiths["collection"] == selected_collection]

# Step 2: Select Hadith ID
st.subheader("Step 2: Select Hadith ID")
available_hadith_ids = coll_hadiths["hadith_id"].tolist()

if available_hadith_ids:
    selected_hadith_id = st.selectbox(
        "Choose Hadith ID:", 
        available_hadith_ids,
        key=f"hadith_pk_{selected_collection}"
    )
    
    hadith_row = coll_hadiths[coll_hadiths["hadith_id"] == selected_hadith_id].iloc[0]
    
    st.markdown(f"**Hadith ID:** `{selected_hadith_id}` | **Collection:** {selected_collection}")
    st.markdown(f'<div class="hadith-card">{hadith_row["hadith_text"]}</div>', unsafe_allow_html=True)

    # Step 3: Select Explanation Source
    st.subheader("Step 3: Select Explanation Source")
    
    related_explanations = df_explanations[df_explanations["hadith_id"] == selected_hadith_id]

    if related_explanations.empty:
        st.warning("⚠️ No explanations available for this Hadith.")
    else:
        sources = related_explanations["source_name"].unique().tolist()
        
        selected_source = st.selectbox(
            "Choose Explanation Source:", 
            sources, 
            key=f"exp_source_{selected_hadith_id}"
        )

        exp_row = related_explanations[related_explanations["source_name"] == selected_source].iloc[0]
        st.markdown(f"**Source:** {selected_source}")
        st.markdown(f'<div class="explanation-card">{exp_row["explanation_text"]}</div>', unsafe_allow_html=True)
else:
    st.info("No hadiths found for this collection.")