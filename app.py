import streamlit as st
import pandas as pd

# ======================
# タイトル
# ======================
st.title("地域ブランド ラダリング調査")

# ======================
# Excel読み込み
# ======================
@st.cache_data
def load_questions():
    df = pd.read_excel(
        "questions.xlsx",
        sheet_name="設問一覧"
    )
    return df

df = load_questions()


# ======================
# セッション初期化
# ======================
if "current_qid" not in st.session_state:
    st.session_state.current_qid = df.iloc[0]["QID"]

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "ladder_index" not in st.session_state:
    st.session_state.ladder_index = 0


# ======================
# 設問取得（安全処理付き）
# ======================
filtered = df[df["QID"] == st.session_state.current_qid]

if len(filtered) == 0:
    st.error(f"QID '{st.session_state.current_qid}' がExcelに存在しません")
    st.stop()

current_row = filtered.iloc[0]


qid = current_row["QID"]
question = current_row["設問文"]

answer_type = current_row["回答形式（単一選択 / 複数選択 / 自由記述 / 数値）"]

options_raw = current_row.get("選択肢（カンマ区切り）", "")

next_q_normal = current_row.get("次の設問（通常）", "")

branch_raw = current_row.get("次の設問（条件分岐）", "")

repeat_source = current_row.get("繰り返し元QID", "")


# ======================
# 繰り返し処理（ラダリング）
# ======================
if pd.notna(repeat_source) and repeat_source != "":

    words = st.session_state.answers.get(repeat_source, [])

    if not isinstance(words, list):
        words = [words]

    if len(words) == 0:
        st.error("繰り返し元の回答が存在しません")
        st.stop()

    if st.session_state.ladder_index >= len(words):

        # 繰り返し終了 → 次の設問へ
        if next_q_normal == "END" or pd.isna(next_q_normal):
            st.success("調査完了です。ありがとうございました。")

            st.write("### 回答結果")
            for k, v in st.session_state.answers.items():
                st.write(f"{k}: {v}")

            st.stop()

        else:
            st.session_state.current_qid = next_q_normal
            st.session_state.ladder_index = 0
            st.rerun()

    current_word = words[st.session_state.ladder_index]

    question = question.replace("{word}", str(current_word))


# ======================
# 設問表示
# ======================
st.write(f"### {qid}")
st.write(question)

answer = None


# ======================
# 回答UI生成
# ======================

# 自由記述
if answer_type == "自由記述":

    answer = st.text_input("回答を入力してください", key=f"{qid}_{st.session_state.ladder_index}")


# 数値
elif answer_type == "数値":

    answer = st.number_input("数値を入力してください", key=f"{qid}_{st.session_state.ladder_index}")


# 単一選択
elif answer_type == "単一選択":

    options = [x.strip() for x in str(options_raw).split(",")]

    answer = st.radio("選択してください", options, key=f"{qid}_{st.session_state.ladder_index}")


# 複数選択
elif answer_type == "複数選択":

    options = [x.strip() for x in str(options_raw).split(",")]

    answer = st.multiselect("選択してください", options, key=f"{qid}_{st.session_state.ladder_index}")


# text5（最大5個入力）
elif answer_type == "text5":

    answers = []

    st.write("最大5つまで入力してください")

    for i in range(5):

        val = st.text_input(
            f"{i+1}つ目",
            key=f"{qid}_{i}"
        )

        if val != "":
            answers.append(val)

    answer = answers


# ======================
# 条件分岐関数
# ======================
def get_next_qid(answer, branch_raw, default_next):

    if pd.isna(branch_raw) or branch_raw == "":
        return default_next

    branches = str(branch_raw).split("/")

    for branch in branches:

        if "→" in branch:

            condition, target = branch.split("→")

            condition = condition.strip()
            target = target.strip()

            if isinstance(answer, list):

                if condition in answer:
                    return target

            else:

                if str(answer) == condition:
                    return target

    return default_next


# ======================
# 次へボタン
# ======================
if st.button("次へ"):

    if answer is None or answer == "" or answer == []:

        st.warning("回答を入力してください")

    else:

        # 保存（繰り返し設問対応）
        if pd.notna(repeat_source) and repeat_source != "":

            if qid not in st.session_state.answers:
                st.session_state.answers[qid] = []

            st.session_state.answers[qid].append(answer)

        else:

            st.session_state.answers[qid] = answer


        # 次の設問決定（条件分岐対応）
        next_q = get_next_qid(answer, branch_raw, next_q_normal)


        # 繰り返し処理中
        if pd.notna(repeat_source) and repeat_source != "":

            st.session_state.ladder_index += 1
            st.rerun()


        # END処理
        elif next_q == "END" or pd.isna(next_q):

            st.success("調査完了です。ありがとうございました。")

            st.write("### 回答結果")

            for k, v in st.session_state.answers.items():
                st.write(f"{k}: {v}")


        else:

            st.session_state.current_qid = next_q
            st.session_state.ladder_index = 0
            st.rerun()
