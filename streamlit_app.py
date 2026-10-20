import streamlit as st
import pandas as pd
import gdown
import os

# 1. Page Configuration
st.set_page_config(page_title="Hadith & Explanation Browser", page_icon="📖", layout="wide")

# Custom CSS for UI Cards
st.markdown("""
<style:
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

# 2. Data Loading Function with Safe Downloads
@st.cache_data(show_spinner=False)
def load_data():
    # REPLACE WITH YOUR ACTUAL GOOGLE DRIVE FILE IDs
    hadith_file_id = "13H7vPAZ6ZL_tBcuXSbohCH9MwXW1SZbn"
    exp_file_id = "1qAjLqJ218JWAZdq44xxBRMmUhKhFHDxV"
    
    hadith_path = "hadiths.parquet"
    exp_path = "explanations.parquet"
    
    # Download Hadiths
    if not os.path.exists(hadith_path) or os.path.getsize(hadith_path) == 0:
        with st.spinner("Downloading Hadiths dataset from Google Drive..."):
            url = f'https://drive.google.com/uc?id={hadith_file_id}'
            gdown.download(url, output=hadith_path, quiet=False, fuzzy=True)
            
    # Download Explanations
    if not os.path.exists(exp_path) or os.path.getsize(exp_path) == 0:
        with st.spinner("Downloading Explanations dataset from Google Drive..."):
            url = f'https://drive.google.com/uc?id={exp_file_id}'
            gdown.download(url, output=exp_path, quiet=False, fuzzy=True)
            
    # Load DataFrames
    df_h = pd.read_parquet(hadith_path)
    df_e = pd.read_parquet(exp_path)
    
    # Ensure index is reset so 'hadith_id' is ALWAYS a normal column in both DataFrames
    if 'hadith_id' not in df_h.columns and df_h.index.name == 'hadith_id':
        df_h = df_h.reset_index()
    if 'hadith_id' not in df_e.columns and df_e.index.name == 'hadith_id':
        df_e = df_e.reset_index()
        
    return df_h, df_e

# Run Data Loader
try:
    df_hadiths, df_explanations = load_data()
except Exception as e:
    st.error(f"❌ Error initializing app data: {e}")
    st.stop()

# 3. Application UI
st.title("📖 Hadith & Explanation Browser")

# Step 1: Select Collection
st.subheader("Step 1: Select Collection")
if "collection" in df_hadiths.columns:
    collections = df_hadiths["collection"].unique().tolist()
    selected_collection = st.selectbox("Choose Collection:", collections)
    coll_hadiths = df_hadiths[df_hadiths["collection"] == selected_collection]
else:
    coll_hadiths = df_hadiths
    selected_collection = "All"

# Step 2: Select Hadith ID
st.subheader("Step 2: Select Hadith ID")
available_hadith_ids = coll_hadiths["hadith_id"].tolist()

if available_hadith_ids:
    selected_hadith_id = st.selectbox(
        "Choose Hadith PK:", 
        available_hadith_ids,
        key=f"hadith_pk_{selected_collection}"
    )
    
    # Filter selected Hadith
    selected_hadith_df = coll_hadiths[coll_hadiths["hadith_id"] == selected_hadith_id]
    
    if not selected_hadith_df.empty:
        selected_hadith = selected_hadith_df.iloc[0]
        st.markdown(f"**Hadith ID:** `{selected_hadith_id}` | **Collection:** {selected_collection}")
        st.markdown(f'<div class="hadith-card">{selected_hadith.get("hadith_text", "No text found")}</div>', unsafe_allow_html=True)

    # Step 3: Select Explanation Source
    st.subheader("Step 3: Select Explanation Source")
    
    # Direct column filter across full explanation dataset
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

        exp_df = related_explanations[related_explanations["source_name"] == selected_source]
        if not exp_df.empty:
            exp_row = exp_df.iloc[0]
            st.markdown(f"**Source:** {selected_source}")
            st.markdown(f'<div class="explanation-card">{exp_row.get("explanation_text", "No explanation text")}</div>', unsafe_allow_html=True)