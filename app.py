import streamlit as st
import pandas as pd
import re

st.title("地域ブランド ラダリング調査")

# =========================
# Excel読み込み（完全防御版）
# =========================

@st.cache_data
def load_questions():

    df = pd.read_excel("questions.xlsx", dtype=str)

    # 列名の空白除去
    df.columns = df.columns.str.strip()

    # 必須列チェック
    required_cols = ["QID", "text", "type"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Excelに必須列 '{col}' がありません")
            st.stop()

    # QIDが空の行を削除
    df = df[df["QID"].notna()]
    df = df[df["QID"].str.strip() != ""]

    questions = {}

    for _, row in df.iterrows():

        qid = row.get("QID", "").strip()

        if qid == "":
            continue

        questions[qid] = {
            "text": row.get("text", ""),
            "type": row.get("type", ""),
            "options": row.get("options", ""),
            "repeat_source": row.get("repeat_source", ""),
            "next": row.get("next", ""),
            "branch_yes": row.get("branch_はい", ""),
            "branch_no": row.get("branch_いいえ", ""),
        }

    return questions


questions = load_questions()

if len(questions) == 0:
    st.error("設問が0件です。Excelを確認してください。")
    st.stop()


# =========================
# セッション初期化
# =========================

first_qid = list(questions.keys())[0]

if "current_qid" not in st.session_state:
    st.session_state.current_qid = first_qid
    st.session_state.answers = {}
    st.session_state.repeat_stack = []
    st.session_state.repeat_index = 0


# =========================
# 安全な設問取得
# =========================

qid = st.session_state.current_qid

if qid not in questions:
    st.error(f"QID '{qid}' がExcelに存在しません")
    st.stop()

q = questions[qid]

text = q["text"]
qtype = q["type"]
options = q["options"]
repeat_source = q["repeat_source"]
next_q = q["next"]
branch_yes = q["branch_yes"]
branch_no = q["branch_no"]


# =========================
# repeat処理
# =========================

display_text = text

if repeat_source:

    words = st.session_state.answers.get(repeat_source, [])

    if isinstance(words, str):
        words = [words]

    if len(words) == 0:
        st.error(f"{repeat_source} の回答がありません")
        st.stop()

    if st.session_state.repeat_index >= len(words):

        st.session_state.repeat_index = 0
        st.session_state.repeat_stack = []

        if next_q == "END":
            st.success("調査完了です")
            st.write(st.session_state.answers)
            st.stop()

        st.session_state.current_qid = next_q
        st.rerun()

    word = words[st.session_state.repeat_index]
    display_text = text.replace("{word}", word)


# =========================
# 表示
# =========================

st.write(f"### {qid}")
st.write(display_text)


# =========================
# 回答UI
# =========================

answer = None

# text
if qtype == "text":
    answer = st.text_input("回答", key=qid)


# text5
elif qtype == "text5":

    answers = []

    for i in range(5):
        v = st.text_input(f"{i+1}個目", key=f"{qid}_{i}")
        if v:
            answers.append(v)

    answer = answers


# multiselect
elif qtype == "multiselect":

    opts = [o.strip() for o in options.split(",") if o.strip()]
    answer = st.multiselect("選択", opts, key=qid)


# multiselect5
elif qtype == "multiselect5":

    opts = [o.strip() for o in options.split(",") if o.strip()]
    answer = st.multiselect("最大5つ選択", opts, max_selections=5, key=qid)


# radio
elif qtype == "radio":

    opts = [o.strip() for o in options.split(",") if o.strip()]
    answer = st.radio("選択", opts, key=qid)


# number
elif qtype == "number":

    answer = st.number_input("数値", key=qid)


# =========================
# ボタン
# =========================

col1, col2 = st.columns(2)

next_clicked = col1.button("次へ")
quit_clicked = col2.button("回答をやめる")


# =========================
# 中断処理
# =========================

if quit_clicked:

    st.warning("回答を中断しました")

    st.write("回答結果")

    st.write(st.session_state.answers)

    st.stop()


# =========================
# 次へ処理
# =========================

if next_clicked:

    if answer is None or answer == "" or answer == []:
        st.warning("回答してください")
        st.stop()

    # 保存
    if repeat_source:
        key = f"{qid}_{st.session_state.repeat_index}"
        st.session_state.answers[key] = answer
        st.session_state.repeat_index += 1
        st.rerun()

    else:
        st.session_state.answers[qid] = answer

    # 分岐処理
    if branch_yes or branch_no:

        if answer == "はい":
            next_qid = branch_yes

        elif answer == "いいえ":
            next_qid = branch_no

        else:
            next_qid = next_q

    else:
        next_qid = next_q


    # END処理
    if next_qid == "END" or next_qid == "" or next_qid is None:

        st.success("調査完了です")

        st.write(st.session_state.answers)

        st.stop()


    # 次へ
    st.session_state.current_qid = next_qid
    st.rerun()
