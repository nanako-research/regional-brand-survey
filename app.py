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

# 自由記述
if answer_type == "自由記述":
    answer = st.text_input("回答を入力してください", key=qid)

# 数値
elif answer_type == "数値":
    answer = st.number_input("数値を入力してください", key=qid)

# 単一選択
elif answer_type == "単一選択":
    options = current_row["選択肢（カンマ区切り）"].split(",")
    answer = st.radio("選択してください", options, key=qid)

# 複数選択
elif answer_type == "複数選択":
    options = current_row["選択肢（カンマ区切り）"].split(",")
    answer = st.multiselect("選択してください", options, key=qid)

# text3, text5, text10 などに対応
elif isinstance(answer_type, str) and answer_type.startswith("text"):

    max_n = int(answer_type.replace("text", ""))

    st.write(f"思いつくものを最大 {max_n} 個まで入力してください")

    answers_list = []

    for i in range(max_n):
        a = st.text_input(f"{i+1}つ目", key=f"{qid}_{i}")
        if a.strip() != "":
            answers_list.append(a.strip())

    answer = answers_list

# 次へボタン
if st.button("次へ"):

    # 未回答チェック
    if (
        answer is None
        or answer == ""
        or answer == []
    ):
        st.warning("回答を入力してください")

    else:

        # 回答保存
        st.session_state.answers[qid] = answer

        # 終了処理
        if next_q == "END":

            st.success("調査完了です。ありがとうございました。")

            st.write("### 回答結果")

            for k, v in st.session_state.answers.items():

                # リストの場合（text5など）
                if isinstance(v, list):
                    st.write(f"{k}: {', '.join(v)}")

                else:
                    st.write(f"{k}: {v}")

        else:
            st.session_state.current_qid = next_q
            st.rerun()
