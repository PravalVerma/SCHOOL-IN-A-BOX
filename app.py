import streamlit as st

st.set_page_config(page_title="School in a Box", layout="wide")

def main():
    st.title("School in a Box")
    tab_learn, tab_quiz, tab_coach = st.tabs(["Learn", "Quiz", "Coach"])
    with tab_learn:
        st.write("TODO: Learn tab UI")
    with tab_quiz:
        st.write("TODO: Quiz tab UI")
    with tab_coach:
        st.write("TODO: Coach tab UI")

if __name__ == "__main__":
    main()
