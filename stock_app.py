import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import datetime
import pymysql
from io import BytesIO
import os
import yaml
import plotly.graph_objs as go


# MySQL 연결 정보
db_info = yaml.load(open('db.yaml').read(), Loader=yaml.FullLoader)

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

# 테이블 생성 함수
def create_table_if_not_exists(table_name):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                date DATE,
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume INT,
                PRIMARY KEY (date)
            )
            """
            cursor.execute(create_table_query)
        connection.commit()
    finally:
        connection.close()

# 데이터 삽입 함수
def insert_stock_data(table_name, df):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 기존 데이터 삭제
            delete_query = f"DELETE FROM {table_name}"
            cursor.execute(delete_query)

            # 새로운 데이터 삽입
            for index, row in df.iterrows():
                insert_query = f"""
                INSERT INTO {table_name} (date, open, high, low, close, volume)
                VALUES ('{index}', {row['Open']}, {row['High']}, {row['Low']}, {row['Close']}, {row['Volume']})
                """
                cursor.execute(insert_query)
        connection.commit()
    finally:
        connection.close()

# 입력 화면
def main():
    with st.sidebar:
        stock_name = st.text_input("회사이름", "삼성전자")
        today = datetime.datetime.now()
        this_year = today.year
        jan_1 = datetime.date(this_year, 1, 1)
        date_range = st.date_input("시작일-종료일", (jan_1, today), jan_1, today, format="MM.DD.YYYY")
        accept = st.button('주가 데이터 확인')
        if st.button('질문하러 가기'):
            st.session_state.page = 'gpt'
            st.session_state.stock_name = stock_name
            st.session_state.start_date = date_range[0]
            st.session_state.end_date = date_range[1]
            st.experimental_rerun()

    @st.cache_data
    def get_stock_info():
        base_url = "http://kind.krx.co.kr/corpgeneral/corpList.do"
        method = "download"
        url = f"{base_url}?method={method}"
        df = pd.read_html(url, header=0, encoding='cp949')[0]
        df['종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
        df = df[['회사명', '종목코드']]
        return df

    def get_ticker_symbol(company_name):
        df = get_stock_info()
        code = df[df['회사명'] == company_name]['종목코드'].values
        ticker_symbol = code[0]
        return ticker_symbol

    if accept:
        # 입력 화면
        st.markdown("<h2 style='text-align: center;'>📈 ott조 주식데이터 보조 앱 📉</h2>", unsafe_allow_html=True)
        # HTML을 사용하여 텍스트를 중앙 정렬
        st.markdown("<h2 style='text-align: center;'>💸 부자가 되어봅시다 💸</h2>", unsafe_allow_html=True)
        ticker_symbol = get_ticker_symbol(stock_name)
        start_p = date_range[0]
        end_p = date_range[1] + datetime.timedelta(days=1)
        df = fdr.DataReader(f'KRX:{ticker_symbol}', start_p, end_p)
        df.index = df.index.date
        st.subheader(f"[{stock_name}] 주가 데이터")
        st.dataframe(df.tail(7))
        
        # MySQL 데이터베이스에 저장
        table_name = f"table_{stock_name}"
        create_table_if_not_exists(table_name)
        insert_stock_data(table_name, df)

        excel_data = BytesIO()
        df.to_excel(excel_data)
        st.download_button("엑셀 파일 다운로드", excel_data, file_name='stock_data.xlsx')

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close'))
        fig.add_trace(go.Scatter(x=df.index, y=df['Open'], mode='lines', name='Open'))
        fig.add_trace(go.Scatter(x=df.index, y=df['High'], mode='lines', name='High'))
        fig.add_trace(go.Scatter(x=df.index, y=df['Low'], mode='lines', name='Low'))

        fig.update_layout(
            title=f'{stock_name} 주가 데이터',
            xaxis_title='Date',
            yaxis_title='Price',
            legend_title='Price Type'
        )
        
        st.plotly_chart(fig)

    # 페이지 전환
    if 'page' not in st.session_state:
        st.session_state.page = 'stock'

    if st.session_state.page == 'gpt':
        st.experimental_rerun()

if __name__ == "__main__":
    main()
