import streamlit as st
import pandas as pd

# タイトル
st.title("地域ブランド ラダリング調査")

# Excel読み込み
@st.cache_data
def load_questions():
    df = pd.read_excel(
        "questions.xlsx",
        sheet_name="設問一覧"
    )
    return df

df = load_questions()

# セッション状態初期化
if "current_qid" not in st.session_state:
    st.session_state.current_qid = df.iloc[0]["QID"]
    st.session_state.answers = {}

# 現在の設問取得
current_row = df[df["QID"] == st.session_state.current_qid].iloc[0]

qid = current_row["QID"]
question = current_row["設問文"]
answer_type = current_row["回答形式（単一選択 / 複数選択 / 自由記述 / 数値）"]
next_q = current_row["次の設問（通常）"]

# 設問表示
st.write(f"### {qid}")
st.write(question)

# 回答入力
answer = None

if answer_type == "自由記述":
    answer = st.text_input("回答を入力してください", key=qid)

elif answer_type == "数値":
    answer = st.number_input("数値を入力してください", key=qid)

elif answer_type == "単一選択":
    options = current_row["選択肢（カンマ区切り）"].split(",")
    answer = st.radio("選択してください", options, key=qid)

elif answer_type == "複数選択":
    options = current_row["選択肢（カンマ区切り）"].split(",")
    answer = st.multiselect("選択してください", options, key=qid)

# 次へボタン
if st.button("次へ"):

    if answer == "" or answer is None:
        st.warning("回答を入力してください")
    else:

        # 回答保存
        st.session_state.answers[qid] = answer

        # ENDなら終了
        if next_q == "END":
            st.success("調査完了です。ありがとうございました。")

            st.write("### 回答結果")
            for k, v in st.session_state.answers.items():
                st.write(f"{k}: {v}")

        else:
            st.session_state.current_qid = next_q
            st.rerun()
