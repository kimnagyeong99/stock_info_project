import streamlit as st
import pandas as pd
import pymysql
import openai
import os
import yaml

# MySQL 연결 정보
db_info = yaml.load(open('db.yaml').read(), Loader=yaml.FullLoader)

# OpenAI API 키 설정
os.environ['OPENAI_API_KEY'] = db_info['OPENAI_API_KEY']
openai.api_key = os.getenv("OPENAI_API_KEY")

# MySQL 연결 정보
db_host = db_info['HOST']
db_user = db_info['USER']
db_password = db_info['PASSWD']
db_name = db_info['DB']

# MySQL 연결 함수
def get_db_connection():
    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        db=db_name,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# 데이터 조회 함수
def query_stock_data(table_name, start_date, end_date):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = f"""
            SELECT * FROM {table_name}
            WHERE date BETWEEN '{start_date}' AND '{end_date}'
            """
            cursor.execute(query)
            result = cursor.fetchall()
            return pd.DataFrame(result)
    finally:
        connection.close()

# OpenAI GPT 모델을 이용한 질문 응답

def ask_gpt(question, data):
    prompt = f"주식 데이터: {data.to_string(index=False)}\n\n질문: {question}\n답변:"
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=900
    )
    return response.choices[0].message.content.strip()

# 질문 입력 및 응답
def main():
    if 'stock_name' not in st.session_state or 'start_date' not in st.session_state or 'end_date' not in st.session_state:
        st.error("먼저 주식 데이터를 조회해야 합니다.")
        return

    st.subheader("질문을 입력하세요")
    question = st.text_input("질문")

    if question:
        table_name = f"table_{st.session_state.stock_name}"
        start_date = st.session_state.start_date
        end_date = st.session_state.end_date
        stock_data = query_stock_data(table_name, start_date, end_date)
        if not stock_data.empty:
            answer = ask_gpt(question, stock_data)
            st.write(f"질문: {question}")
            st.write(f"답변: {answer}")
        else:
            st.write("해당 기간에 대한 데이터가 없습니다.")

    if st.button('뒤로가기'):
        st.session_state.page = 'stock'
        st.experimental_rerun()

if __name__ == "__main__":
    main()
