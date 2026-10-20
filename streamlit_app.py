import streamlit as st
import pandas as pd
import plotly.express as px
import os
import gdown


# Page config & RTL CSS
st.set_page_config(page_title="Hadith & Explanation Browser", page_icon="📖", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&display=swap');
    .hadith-card {
        background-color: #f8f9fa; border-right: 5px solid #1b4332;
        padding: 20px; border-radius: 8px; margin-bottom: 20px;
        font-size: 1.25rem; line-height: 2.1; direction: rtl; text-align: right;
        font-family: 'Amiri', serif;
    }
    .explanation-card {
        background-color: #f0fdf4; border-right: 5px solid #2d6a4f;
        padding: 20px; border-radius: 8px; margin-top: 15px;
        font-size: 1.15rem; line-height: 2.0; direction: rtl; text-align: right;
        font-family: 'Amiri', serif;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data_from_drive():
    # REPLACE THESE WITH YOUR ACTUAL GOOGLE DRIVE FILE IDs
    hadith_file_id = "13H7vPAZ6ZL_tBcuXSbohCH9MwXW1SZbn"
    exp_file_id = "1qAjLqJ218JWAZdq44xxBRMmUhKhFHDxV"  # Or list your split parts IDs if split
    
    hadith_path = "hadiths.parquet"
    exp_path = "explanations.parquet"
    
    # Download Hadiths if not already cached in the app environment
    if not os.path.exists(hadith_path):
        url = f'https://drive.google.com/uc?id={hadith_file_id}'
        gdown.download(url, hadith_path, quiet=False)
        
    # Download Explanations if not already cached
    if not os.path.exists(exp_path):
        url = f'https://drive.google.com/uc?id={exp_file_id}'
        gdown.download(url, exp_path, quiet=False)
        
    df_h = pd.read_parquet(hadith_path)
    df_e = pd.read_parquet(exp_path)
    # ⚡ OPTIMIZATION: Set hadith_id as index for lightning-fast, zero-memory lookups
    if 'hadith_id' in df_h.columns:
        df_h = df_h.set_index('hadith_id')
    if 'hadith_id' in df_e.columns:
        # Note: multiple explanations can share the same hadith_id, so group them or keep index
        df_e = df_e.set_index('hadith_id')
    return df_h, df_e

df_hadiths, df_explanations = load_data_from_drive()

# Navigation
st.sidebar.title("📖 Navigation")
app_mode = st.sidebar.radio("Select View", ["Hadith Explorer", "Coverage Analytics"])

# -----------------------------------------------------------------------------
# View 1: Hadith Explorer
# -----------------------------------------------------------------------------
if app_mode == "Hadith Explorer":
    st.title("📚 Hadith & Explanation Browser")
    
    # Step 1: Collection
    collections = sorted(df_hadiths["collection"].dropna().unique().tolist())
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Step 1: Select Collection")
        selected_collection = st.selectbox("Collection:", collections)

    coll_hadiths = df_hadiths[df_hadiths["collection"] == selected_collection]
    coll_explanations = df_explanations[df_explanations["collection"] == selected_collection]

    total_in_coll = len(coll_hadiths)
    explained_in_coll = coll_hadiths["is_explained"].sum()
    cov_pct = (explained_in_coll / total_in_coll * 100) if total_in_coll > 0 else 0

    with col2:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Hadiths", f"{total_in_coll:,}")
        m2.metric("Explained Hadiths", f"{explained_in_coll:,}")
        m3.metric("Coverage %", f"{cov_pct:.1f}%")
        st.progress(min(cov_pct / 100, 1.0))

    st.markdown("---")

    # Step 2: Hadith ID
    st.subheader("Step 2: Select Hadith ID")
    available_hadith_ids = coll_hadiths["hadith_id"].tolist()
    
    if available_hadith_ids:
        selected_hadith_id = st.selectbox("Choose Hadith PK:", available_hadith_ids)
        selected_hadith = coll_hadiths[coll_hadiths["hadith_id"] == selected_hadith_id].iloc[0]
        
        st.markdown(f"**Hadith ID:** `{selected_hadith_id}` | **Collection:** {selected_collection}")
        st.markdown(f'<div class="hadith-card">{selected_hadith.get("hadith_text", "No text")}</div>', unsafe_allow_html=True)

        # Step 3: Explanation Source
        st.subheader("Step 3: Select Explanation Source")
        related_explanations = coll_explanations[coll_explanations["hadith_id"] == selected_hadith_id]

        if related_explanations.empty:
            st.warning("⚠️ No explanations available for this Hadith.")
        else:
            sources = related_explanations["source_name"].unique().tolist()
            selected_source = st.selectbox("Choose Explanation Source:", sources)

            exp_row = related_explanations[related_explanations["source_name"] == selected_source].iloc[0]
            st.markdown(f"**Source:** {selected_source}")
            st.markdown(f'<div class="explanation-card">{exp_row.get("explanation_text", "")}</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# View 2: Coverage Analytics
# -----------------------------------------------------------------------------
elif app_mode == "Coverage Analytics":
    st.title("📊 Global Coverage Analytics")
    
    summary = []
    for coll in df_hadiths["collection"].unique():
        sub_h = df_hadiths[df_hadiths["collection"] == coll]
        tot = len(sub_h)
        exp = sub_h["is_explained"].sum()
        pct = (exp / tot * 100) if tot > 0 else 0
        summary.append({"Collection": coll, "Total": tot, "Explained": exp, "Coverage %": round(pct, 2)})

    df_summary = pd.DataFrame(summary).sort_values(by="Coverage %", ascending=True)

    fig = px.bar(
        df_summary, x="Coverage %", y="Collection", orientation="h",
        text="Coverage %", color="Coverage %", color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_summary.sort_values(by="Coverage %", ascending=False), use_container_width=True)