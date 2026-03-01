import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

# =========================
# 初期設定
# =========================

QUESTION_FILE = "questions.xlsx"
ANSWER_FILE = "answers.xlsx"

st.set_page_config(page_title="アンケート", layout="centered")

# =========================
# 質問読み込み
# =========================

@st.cache_data
def load_questions():

    df = pd.read_excel(QUESTION_FILE)

    df = df.fillna("")

    questions = {}

    for _, row in df.iterrows():

        q = row.to_dict()

        qid = str(q["QID"]).strip()

        if qid == "":
            continue

        # options
        if "options" in q and q["options"] != "":
            q["options"] = [x.strip() for x in str(q["options"]).split(",")]
        else:
            q["options"] = []

        # branch
        branch = {}
        for col in df.columns:
            if col.startswith("branch_"):
                key = col.replace("branch_", "")
                val = str(q[col]).strip()
                if val != "":
                    branch[key] = val

        q["branch"] = branch

        # next
        q["next"] = str(q.get("next", "")).strip()

        questions[qid] = q

    return questions


questions = load_questions()

# =========================
# セッション初期化
# =========================

if "current_qid" not in st.session_state:
    st.session_state.current_qid = list(questions.keys())[0]
    st.session_state.answers = {}
    st.session_state.finished = False
    st.session_state.quit = False
    st.session_state.respondent_id = str(uuid.uuid4())

# =========================
# 保存処理
# =========================

def save_answers():

    data = []

    for qid, answer in st.session_state.answers.items():

        data.append({
            "respondent_id": st.session_state.respondent_id,
            "timestamp": datetime.now(),
            "QID": qid,
            "answer": answer
        })

    df = pd.DataFrame(data)

    try:
        old = pd.read_excel(ANSWER_FILE)
        df = pd.concat([old, df], ignore_index=True)
    except:
        pass

    df.to_excel(ANSWER_FILE, index=False)

# =========================
# 中断ボタン
# =========================

if not st.session_state.finished:

    if st.button("回答をやめる"):

        save_answers()

        st.session_state.quit = True
        st.session_state.finished = True

        st.rerun()

# =========================
# 終了画面
# =========================

if st.session_state.finished:

    if st.session_state.quit:
        st.write("回答を中断しました。ご協力ありがとうございました。")
    else:
        st.write("回答が完了しました。ありがとうございました。")

    st.stop()

# =========================
# 質問取得
# =========================

qid = st.session_state.current_qid

if qid not in questions:
    st.error(f"QID '{qid}' がExcelに存在しません")
    st.stop()

q = questions[qid]

# =========================
# 質問表示
# =========================

st.write(q["text"])

answer = None

type_ = q["type"]

# text
if type_ == "text":
    answer = st.text_input("")

# text5
elif type_ == "text5":

    answers = []

    for i in range(5):
        a = st.text_input(f"{i+1}つ目", key=f"{qid}_{i}")
        if a != "":
            answers.append(a)

    answer = answers

# radio
elif type_ == "radio":

    answer = st.radio("", q["options"])

# multiselect5
elif type_ == "multiselect5":

    answer = st.multiselect("", q["options"], max_selections=5)

# =========================
# 次へボタン
# =========================

if st.button("次へ"):

    st.session_state.answers[qid] = answer

    next_qid = ""

    # branch優先
    if isinstance(answer, list):
        next_qid = q["next"]
    else:
        if answer in q["branch"]:
            next_qid = q["branch"][answer]
        else:
            next_qid = q["next"]

    if next_qid == "" or next_qid == "END":

        save_answers()

        st.session_state.finished = True

    else:

        st.session_state.current_qid = next_qid

    st.rerun()
