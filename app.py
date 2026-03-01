import streamlit as st
import pandas as pd
import re

st.title("地域ブランド ラダリング調査")

# =========================
# Excel読み込み（改訂・安定版）
# =========================

@st.cache_data
def load_questions():
    # dtype=str を外し、fillna("") で NaN を完全に潰す（重要）
    df = pd.read_excel("questions.xlsx")
    df = df.fillna("")

    # 列名の空白除去（重要）
    df.columns = df.columns.str.strip()

    # 必須列チェック
    required_cols = ["QID", "text", "type"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Excelに必須列 '{col}' がありません。現在の列名: {df.columns.tolist()}")
            st.stop()

    # QIDが空の行を削除（重要）
    df["QID"] = df["QID"].astype(str).str.strip()
    df = df[df["QID"] != ""]

    questions = {}

    for _, row in df.iterrows():
        # row は Series なので row.get が使える
        qid = str(row.get("QID", "")).strip()
        if qid == "":
            continue

        # 文字列として確実に取り出し、前後空白を除去
        text = str(row.get("text", "")).strip()
        qtype = str(row.get("type", "")).strip()

        options = str(row.get("options", "")).strip()
        repeat_source = str(row.get("repeat_source", "")).strip()
        next_q = str(row.get("next", "")).strip()

        # branch列（無い場合にも耐える）
        branch_yes = str(row.get("branch_はい", "")).strip()
        branch_no = str(row.get("branch_いいえ", "")).strip()

        # "nan" 文字列を無効化（超重要）
        if repeat_source.lower() == "nan":
            repeat_source = ""
        if next_q.lower() == "nan":
            next_q = ""
        if branch_yes.lower() == "nan":
            branch_yes = ""
        if branch_no.lower() == "nan":
            branch_no = ""

        questions[qid] = {
            "text": text,
            "type": qtype,
            "options": options,
            "repeat_source": repeat_source,
            "next": next_q,
            "branch_yes": branch_yes,
            "branch_no": branch_no,
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
# repeat処理（{word}置換）
# =========================

display_text = text

# repeat_source が有効な文字列のときだけ繰り返す
if isinstance(repeat_source, str) and repeat_source.strip() != "":
    repeat_source = repeat_source.strip()

    words = st.session_state.answers.get(repeat_source, [])

    # 繰り返し元が単一文字列の場合もリスト化
    if isinstance(words, str):
        words = [words]

    # そもそも繰り返し元の回答がないとき
    if not words or len(words) == 0:
        st.error(f"{repeat_source} の回答がありません（repeat_source列を確認してください）")
        st.stop()

    # すべて繰り返し終わったら next へ
    if st.session_state.repeat_index >= len(words):
        st.session_state.repeat_index = 0

        if next_q == "END" or next_q == "":
            st.success("調査完了です")
            st.write(st.session_state.answers)
            st.stop()

        st.session_state.current_qid = next_q
        st.rerun()

    word = str(words[st.session_state.repeat_index])
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

# text5（自由入力5つ）
elif qtype == "text5":
    answers = []
    for i in range(5):
        v = st.text_input(f"{i+1}個目", key=f"{qid}_{i}")
        if v:
            answers.append(v)
    answer = answers

# multiselect
elif qtype == "multiselect":
    opts = [o.strip() for o in str(options).split(",") if o.strip()]
    answer = st.multiselect("選択", opts, key=qid)

# multiselect5（最大5つ）
elif qtype == "multiselect5":
    opts = [o.strip() for o in str(options).split(",") if o.strip()]
    answer = st.multiselect("最大5つ選択", opts, max_selections=5, key=qid)

# radio
elif qtype == "radio":
    opts = [o.strip() for o in str(options).split(",") if o.strip()]
    answer = st.radio("選択", opts, key=qid)

# number
elif qtype == "number":
    answer = st.number_input("数値", key=qid)

else:
    st.error(f"type '{qtype}' が未対応です（text / text5 / radio / multiselect / multiselect5 / number）")
    st.stop()


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
    st.write("ここまでの回答")
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
    if isinstance(repeat_source, str) and repeat_source.strip() != "":
        # 繰り返し設問は index 付きで保存（「どのwordの回答か」追跡用）
        key = f"{qid}_{st.session_state.repeat_index}"
        st.session_state.answers[key] = answer
        st.session_state.repeat_index += 1
        st.rerun()
    else:
        st.session_state.answers[qid] = answer

    # 分岐処理（branch_はい / branch_いいえ）
    if (branch_yes or branch_no) and not isinstance(answer, list):
        if str(answer).strip() == "はい":
            next_qid = branch_yes
        elif str(answer).strip() == "いいえ":
            next_qid = branch_no
        else:
            next_qid = next_q
    else:
        next_qid = next_q

    next_qid = str(next_qid).strip()

    # END処理
    if next_qid == "END" or next_qid == "":
        st.success("調査完了です")
        st.write(st.session_state.answers)
        st.stop()

    # 次へ
    st.session_state.current_qid = next_qid
    st.rerun()
