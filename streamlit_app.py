import streamlit as st
import duckdb
import gdown
import os

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

# 2. Ensure Parquet Files are Downloaded
@st.cache_resource
def init_data_files():
    hadith_file_id = "13H7vPAZ6ZL_tBcuXSbohCH9MwXW1SZbn"
    exp_file_id = "1qAjLqJ218JWAZdq44xxBRMmUhKhFHDxV"
    
    hadith_path = "hadiths.parquet"
    exp_path = "explanations.parquet"
    
    if not os.path.exists(hadith_path) or os.path.getsize(hadith_path) == 0:
        gdown.download(f'https://drive.google.com/uc?id={hadith_file_id}', output=hadith_path, quiet=False)
            
    if not os.path.exists(exp_path) or os.path.getsize(exp_path) == 0:
        gdown.download(f'https://drive.google.com/uc?id={exp_file_id}', output=exp_path, quiet=False)
        
    return hadith_path, exp_path

hadith_path, exp_path = init_data_files()

# 3. Application UI using DuckDB (Zero Memory Footprint)
st.title("📖 Hadith & Explanation Browser")

# Step 1: Get distinct collections using DuckDB
@st.cache_data
def get_collections():
    query = f"SELECT DISTINCT collection FROM '{hadith_path}' WHERE collection IS NOT NULL ORDER BY collection"
    return duckdb.sql(query).df()["collection"].tolist()

collections = get_collections()
selected_collection = st.selectbox("Choose Collection:", collections)

# Step 2: Get Hadith IDs for selected collection
@st.cache_data
def get_hadiths_by_collection(coll):
    query = f"SELECT hadith_id, hadith_text FROM '{hadith_path}' WHERE collection = ?"
    return duckdb.sql(query, params=[coll]).df()

coll_hadiths = get_hadiths_by_collection(selected_collection)
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

    # Step 3: Get Explanations for selected Hadith ID on the fly
    @st.cache_data
    def get_explanations(h_id):
        query = f"SELECT source_name, explanation_text FROM '{exp_path}' WHERE hadith_id = ?"
        return duckdb.sql(query, params=[h_id]).df()

    related_explanations = get_explanations(selected_hadith_id)

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