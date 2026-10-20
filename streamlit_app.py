import streamlit as st
import pandas as pd
import gdown
import os
import traceback

st.set_page_config(page_title="Hadith Browser Debug", layout="wide")

try:
    st.write("🔄 Initializing app...")
    
    hadith_file_id = "13H7vPAZ6ZL_tBcuXSbohCH9MwXW1SZbn"
    exp_file_id = "1qAjLqJ218JWAZdq44xxBRMmUhKhFHDxV"
    
    hadith_path = "hadiths.parquet"
    exp_path = "explanations.parquet"
    
    if not os.path.exists(hadith_path) or os.path.getsize(hadith_path) == 0:
        st.write("📥 Downloading hadiths...")
        gdown.download(f'https://drive.google.com/uc?id={hadith_file_id}', output=hadith_path, quiet=False)
            
    if not os.path.exists(exp_path) or os.path.getsize(exp_path) == 0:
        st.write("📥 Downloading explanations...")
        gdown.download(f'https://drive.google.com/uc?id={exp_file_id}', output=exp_path, quiet=False)
            
    st.write("📊 Loading dataframes into memory...")
    df_h = pd.read_parquet(hadith_path)
    df_e = pd.read_parquet(exp_path)
    
    st.success("✅ Data loaded successfully!")
    
    # Display column names so we can verify them instantly
    st.write("Hadiths Columns:", df_h.columns.tolist())
    st.write("Explanations Columns:", df_e.columns.tolist())
    
    st.dataframe(df_h.head(2))

except Exception as e:
    st.error("❌ App crashed with the following error:")
    st.exception(e)