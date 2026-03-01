import streamlit as st
import pandas as pd
import os
from datetime import datetime

# =====================
# 基本設定
# =====================

st.title("地域ブランド ラダリング調査")

QUESTIONS_FILE = "questions.xlsx"
RESULTS_FILE = "results.xlsx"


# =====================
# 設問Excel読み込み
# =====================

@st.cache_data
def load_questions():
    df = pd.read_excel(QUESTIONS_FILE, sheet_name="設問一覧")
    df = df.fillna("")
    return df

df = load_questions()


# =====================
# results.xlsx 初期化
# =====================

def init_results_file():

    if not os.path.exists(RESULTS_FILE):

        columns = [
            "回答ID",
            "回答日時",
            "QID",
            "設問文",
            "回答",
            "繰り返し対象"
        ]

        empty_df = pd.DataFrame(columns=columns)
        empty_df.to_excel(RESULTS_FILE, index=False)

init_results_file()


# =====================
# 回答保存
# =====================

def save_answer(qid, question, answer, repeat_target=""):

    df_existing = pd.read_excel(RESULTS_FILE)

    if len(df_existing) == 0:
        new_id = 1
    else:
        new_id = df_existing["回答ID"].max() + 1

    new_row = pd.DataFrame([{
        "回答ID": new_id,
        "回答日時": datetime.now(),
        "QID": qid,
        "設問文": question,
        "回答": str(answer),
        "繰り返し対象": repeat_target
    }])

    df_new = pd.concat([df_existing, new_row], ignore_index=True)
    df_new.to_excel(RESULTS_FILE, index=False)


# =====================
# セッション状態初期化
# =====================

if "current_qid" not in st.session_state:

    st.session_state.current_qid = df.iloc[0]["QID"]

    st.session_state.answers = {}

    st.session_state.repeat_list = []
    st.session_state.repeat_index = 0
    st.session_state.repeat_qid = None

    st.session_state.start_time = datetime.now()


# =====================
# 回答中断ボタン
# =====================

if st.button("回答をやめる"):

    st.warning("回答を中断しました。ご協力ありがとうございました。")
    st.stop()


# =====================
# 現在設問取得（安全処理）
# =====================

matching_rows = df[df["QID"] == st.session_state.current_qid]

if len(matching_rows) == 0:

    st.error(f"QID '{st.session_state.current_qid}' がExcelに存在しません。")
    st.stop()

current_row = matching_rows.iloc[0]


qid = current_row["QID"]

question = current_row["設問文"]

answer_type = current_row["回答形式（単一選択 / 複数選択 / 自由記述 / 数値）"]

choices = current_row["選択肢（カンマ区切り）"]

next_q = current_row["次の設問（通常）"]


# =====================
# repeat対象取得
# =====================

repeat_target = ""

if st.session_state.repeat_list:

    repeat_target = st.session_state.repeat_list[
        st.session_state.repeat_index
    ]

    # {word}置換（パイピング機能）
    question = question.replace("{word}", repeat_target)

    st.info(f"対象：{repeat_target}")


# =====================
# 設問表示
# =====================

st.write(f"### {qid}")
st.write(question)


# =====================
# 回答入力UI
# =====================

answer = None


# 自由記述
if answer_type == "自由記述":

    answer = st.text_input("回答してください", key=qid)


# 数値
elif answer_type == "数値":

    answer = st.number_input("数値を入力してください", key=qid)


# 単一選択
elif answer_type == "単一選択":

    options = choices.split(",")

    answer = st.radio(
        "選択してください",
        options,
        key=qid
    )


# 複数選択
elif answer_type == "複数選択":

    options = choices.split(",")

    answer = st.multiselect(
        "選択してください",
        options,
        key=qid
    )


# text5
elif answer_type == "text5":

    answers = []

    for i in range(5):

        val = st.text_input(
            f"{i+1}つ目",
            key=f"{qid}_{i}"
        )

        if val != "":
            answers.append(val)

    answer = answers

    if answers:

        st.session_state.repeat_list = answers
        st.session_state.repeat_index = 0
        st.session_state.repeat_qid = next_q


# multiselect5
elif answer_type == "multiselect5":

    options = choices.split(",")

    answers = st.multiselect(
        "5つまで選択してください",
        options,
        max_selections=5,
        key=qid
    )

    answer = answers

    if answers:

        st.session_state.repeat_list = answers
        st.session_state.repeat_index = 0
        st.session_state.repeat_qid = next_q


# =====================
# 次へボタン
# =====================

if st.button("次へ"):

    if answer is None or answer == "" or answer == []:

        st.warning("回答してください")

    else:

        save_answer(qid, question, answer, repeat_target)

        st.session_state.answers[qid] = answer


        # repeat処理
        if st.session_state.repeat_list:

            st.session_state.repeat_index += 1

            if st.session_state.repeat_index < len(st.session_state.repeat_list):

                st.session_state.current_qid = st.session_state.repeat_qid

            else:

                st.session_state.repeat_list = []
                st.session_state.repeat_index = 0
                st.session_state.repeat_qid = None

                if next_q == "END":

                    st.success("調査完了です。ありがとうございました。")
                    st.stop()

                else:

                    st.session_state.current_qid = next_q


        else:

            if next_q == "END":

                st.success("調査完了です。ありがとうございました。")
                st.stop()

            else:

                st.session_state.current_qid = next_q


        st.rerun()
