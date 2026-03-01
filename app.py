import streamlit as st
import pandas as pd
from datetime import datetime

# ==============================
# 設定
# ==============================

QUESTIONS_FILE = "questions.xlsx"

# ==============================
# Excel読み込み
# ==============================

@st.cache_data
def load_questions():
    df = pd.read_excel(
        QUESTIONS_FILE,
        sheet_name="設問一覧"
    )

    # NaNを空文字に
    df = df.fillna("")

    return df


df = load_questions()


# ==============================
# セッション状態初期化
# ==============================

if "current_qid" not in st.session_state:
    st.session_state.current_qid = df.iloc[0]["QID"]

if "answers" not in st.session_state:
    st.session_state.answers = {}

# text5回答保存用
if "text5_words" not in st.session_state:
    st.session_state.text5_words = []

if "text5_index" not in st.session_state:
    st.session_state.text5_index = 0

# 回答開始時刻
if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.now()


# ==============================
# タイトル
# ==============================

st.title("地域ブランド ラダリング調査")


# ==============================
# QID存在チェック（エラー防止）
# ==============================

if st.session_state.current_qid == "END":

    st.success("調査は終了しました。ご協力ありがとうございました。")

    st.write("### 回答結果")

    for k, v in st.session_state.answers.items():
        st.write(f"{k}: {v}")

    end_time = datetime.now()
    duration = (end_time - st.session_state.start_time).seconds

    st.write(f"回答時間: {duration} 秒")

    st.stop()


filtered = df[df["QID"] == st.session_state.current_qid]

if len(filtered) == 0:

    st.error(f"QID '{st.session_state.current_qid}' がExcelに存在しません。")
    st.stop()

current_row = filtered.iloc[0]


# ==============================
# 設問情報取得
# ==============================

qid = current_row["QID"]
question = current_row["設問文"]
answer_type = current_row["回答形式（単一選択 / 複数選択 / 自由記述 / 数値）"]
options = str(current_row["選択肢（カンマ区切り）"])
next_q = current_row["次の設問（通常）"]
branch = current_row["次の設問（条件分岐）"]
repeat_source = current_row.get("繰り返し元QID", "")


# ==============================
# 設問表示
# ==============================

st.write(f"### {qid}")
st.write(question)


# ==============================
# 回答入力
# ==============================

answer = None


# ---------- 自由記述 ----------
if answer_type == "自由記述":

    answer = st.text_input("回答してください", key=qid)


# ---------- 数値 ----------
elif answer_type == "数値":

    answer = st.number_input("数値を入力してください", key=qid)


# ---------- 単一選択 ----------
elif answer_type == "単一選択":

    option_list = options.split(",")

    answer = st.radio(
        "選択してください",
        option_list,
        key=qid
    )


# ---------- 複数選択 ----------
elif answer_type == "複数選択":

    option_list = options.split(",")

    answer = st.multiselect(
        "選択してください",
        option_list,
        key=qid
    )


# ---------- text5 ----------
elif answer_type == "text5":

    st.write("最大5つまで入力できます")

    text_inputs = []

    for i in range(5):

        val = st.text_input(
            f"{i+1}つ目",
            key=f"{qid}_{i}"
        )

        if val != "":
            text_inputs.append(val)

    answer = text_inputs


# ==============================
# ボタン配置
# ==============================

col1, col2 = st.columns(2)

with col1:
    next_clicked = st.button("次へ")

with col2:
    quit_clicked = st.button("回答をやめる")


# ==============================
# 回答中断処理
# ==============================

if quit_clicked:

    st.warning("回答は途中で終了されました。ありがとうございました。")

    st.write("### ここまでの回答")

    for k, v in st.session_state.answers.items():
        st.write(f"{k}: {v}")

    duration = (datetime.now() - st.session_state.start_time).seconds

    st.write(f"回答時間: {duration} 秒")

    st.stop()


# ==============================
# 次へ処理
# ==============================

if next_clicked:

    if answer is None or answer == "" or answer == []:

        st.warning("回答を入力してください")

    else:

        # 保存
        st.session_state.answers[qid] = answer


        # ======================
        # 条件分岐処理
        # ======================

        next_question = next_q

        if branch != "":

            branches = branch.split("/")

            for b in branches:

                if "→" in b:

                    condition, destination = b.split("→")

                    condition = condition.strip()
                    destination = destination.strip()

                    if answer == condition:
                        next_question = destination


        # ======================
        # END判定
        # ======================

        if next_question == "END":

            st.session_state.current_qid = "END"

        else:

            st.session_state.current_qid = next_question

        st.rerun()
