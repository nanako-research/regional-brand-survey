import streamlit as st
import pandas as pd
import re

st.title("地域ブランド ラダリング調査")

# Excel読み込み
@st.cache_data
def load_questions():
    return pd.read_excel("questions.xlsx", sheet_name="設問一覧")

df = load_questions()

# 初期化
if "current_qid" not in st.session_state:
    st.session_state.current_qid = df.iloc[0]["QID"]
    st.session_state.answers = {}

# QID存在確認（安全化）
matched = df[df["QID"] == st.session_state.current_qid]

if matched.empty:
    st.error(f"QID '{st.session_state.current_qid}' がExcelに存在しません")
    st.stop()

current_row = matched.iloc[0]

qid = current_row["QID"]
question = current_row["設問文"]
answer_type = current_row["回答形式（単一選択 / 複数選択 / 自由記述 / 数値）"]

normal_next = current_row["次の設問（通常）"]
branch_next = current_row["次の設問（条件分岐）"]

# 設問表示
st.write(f"### {qid}")
st.write(question)

# 回答入力
answer = None

if answer_type == "自由記述":
    answer = st.text_input("回答", key=qid)

elif answer_type == "数値":
    answer = st.number_input("回答", key=qid)

elif answer_type == "単一選択":
    options = current_row["選択肢（カンマ区切り）"].split(",")
    answer = st.radio("選択", options, key=qid)

elif answer_type == "複数選択":
    options = current_row["選択肢（カンマ区切り）"].split(",")
    answer = st.multiselect("選択", options, key=qid)

elif answer_type == "text5":
    answers = []
    for i in range(5):
        val = st.text_input(f"回答 {i+1}", key=f"{qid}_{i}")
        if val:
            answers.append(val)
    answer = answers if answers else None

# 条件分岐解析関数
def get_next_q(answer, normal_next, branch_next):

    # 条件分岐優先
    if pd.notna(branch_next):

        parts = branch_next.split("/")

        for part in parts:

            match = re.match(r"(.*)→(.*)", part.strip())

            if match:

                condition = match.group(1).strip()
                target = match.group(2).strip()

                if answer == condition:
                    return target

    # 通常遷移
    if pd.notna(normal_next):
        return normal_next

    return None


# 次へボタン
if st.button("次へ"):

    if answer is None or answer == "":
        st.warning("回答してください")

    else:

        st.session_state.answers[qid] = answer

        next_q = get_next_q(answer, normal_next, branch_next)

        if next_q == "END" or next_q is None:

            st.success("調査完了です")

            st.write("### 回答結果")

            for k, v in st.session_state.answers.items():
                st.write(k, ":", v)

        else:

            st.session_state.current_qid = next_q
            st.rerun()
