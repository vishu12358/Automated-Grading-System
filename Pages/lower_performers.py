import streamlit as st
import pandas as pd
import plotly.express as px
st.image("assets\images.jpg", width=80)

st.set_page_config(page_title="Module Analysis", layout="wide")

# -----------------------------
# Load Data
# -----------------------------
df = pd.read_csv("output/master_performance.csv")

st.title("📚 Module Analysis Dashboard")
st.markdown("Analyze the performance of each quiz/module.")

# -----------------------------
# Quiz Selection
# -----------------------------
quiz_columns = [
    "Quiz1",
    "Quiz2",
    "Quiz3",
    "Quiz4",
    "Quiz5",
    "Quiz6",
    "Quiz7"
]

selected_quiz = st.selectbox(
    "📌 Select Quiz",
    quiz_columns
)

# -----------------------------
# KPI Cards
# -----------------------------
avg = df[selected_quiz].mean()
highest = df[selected_quiz].max()
lowest = df[selected_quiz].min()

topper = df.loc[df[selected_quiz].idxmax(), "Name"]
lowest_student = df.loc[df[selected_quiz].idxmin(), "Name"]

c1, c2, c3 = st.columns(3)

c1.metric("📈 Average Marks", round(avg, 2))
c2.metric("🏆 Highest Marks", highest)
c3.metric("📉 Lowest Marks", lowest)

st.success(f"🥇 Topper: **{topper}** ({highest} marks)")
st.error(f"⚠ Lowest Performer: **{lowest_student}** ({lowest} marks)")

st.divider()

# -----------------------------
# Marks Distribution
# -----------------------------
fig = px.histogram(
    df,
    x=selected_quiz,
    nbins=15,
    title=f"{selected_quiz} Marks Distribution",
    color_discrete_sequence=["#4CAF50"]
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Top 10 Students
# -----------------------------
st.subheader(f"🏆 Top 10 Students - {selected_quiz}")

top10 = df.sort_values(
    selected_quiz,
    ascending=False
).head(10)

fig2 = px.bar(
    top10,
    x="Name",
    y=selected_quiz,
    text=selected_quiz,
    color=selected_quiz,
    title=f"Top 10 Students in {selected_quiz}"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Bottom 10 Students
# -----------------------------
st.subheader(f"⚠ Bottom 10 Students - {selected_quiz}")

# FIX: Drop rows where the quiz score or Name is NaN
valid_df = df.dropna(subset=[selected_quiz, "Name"])

if valid_df.empty:
    st.warning(f"No valid scores found for {selected_quiz}.")
else:
    bottom10 = valid_df.sort_values(by=selected_quiz).head(10)

    fig3 = px.bar(
        bottom10,
        x="Name",
        y=selected_quiz,
        text=selected_quiz,
        color=selected_quiz,
        title=f"Bottom 10 Students in {selected_quiz}"
    )
    
    # Optional: Makes the numbers on top of the bars look clean (removes .0 decimals)
    fig3.update_traces(texttemplate="%{text:.0f}", textposition="outside")

    st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# Difficulty Analysis
# -----------------------------
st.subheader("📊 Quiz Difficulty Analysis")

quiz_avg = df[quiz_columns].mean().reset_index()
quiz_avg.columns = ["Quiz", "Average"]

fig4 = px.bar(
    quiz_avg,
    x="Quiz",
    y="Average",
    text="Average",
    color="Average",
    title="Average Score of Every Quiz"
)

st.plotly_chart(fig4, use_container_width=True)

easiest = quiz_avg.loc[quiz_avg["Average"].idxmax()]
hardest = quiz_avg.loc[quiz_avg["Average"].idxmin()]

st.success(
    f"✅ Easiest Quiz: **{easiest['Quiz']}** "
    f"(Average = {round(easiest['Average'],2)})"
)

st.warning(
    f"⚠ Hardest Quiz: **{hardest['Quiz']}** "
    f"(Average = {round(hardest['Average'],2)})"
)

st.divider()

# -----------------------------
# Student Table
# -----------------------------
st.subheader("📋 Student Marks")

student_marks = df[
    ["Name", selected_quiz, "Percentage", "Grade"]
].sort_values(selected_quiz, ascending=False)

st.dataframe(
    student_marks,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# Download
# -----------------------------
csv = student_marks.to_csv(index=False)

st.download_button(
    "⬇ Download Module Report",
    csv,
    file_name=f"{selected_quiz}_Report.csv",
    mime="text/csv"
)