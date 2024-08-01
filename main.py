import streamlit as st
import stock_app
import gpt_app

# 페이지 라우팅
if 'page' not in st.session_state:
    st.session_state.page = 'stock'

if st.session_state.page == 'stock':
    stock_app.main()
elif st.session_state.page == 'gpt':
    gpt_app.main()
