import streamlit as st

pg = st.navigation([
    st.Page("pages/1_Maps.py",     title="Maps"),
    st.Page("pages/2_Analysis.py", title="Analysis"),
])
pg.run()