import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
st.image("assets\images.jpg", width=80)
st.set_page_config(page_title="Reports", layout="wide")

# ==============================
# Load Data
# ==============================
df = pd.read_csv("output/master_performance.csv")
df.columns = df.columns.str.strip()  # Strip whitespace from column names
df["Percentage"] = pd.to_numeric(df["Percentage"], errors="coerce").clip(0, 100)
report = df.copy()
st.title("📄 Reports Dashboard")
st.markdown("Generate and download training performance reports.")

# ==============================
# Report Type
# ==============================
report_type = st.selectbox(
    "Select Report",
    [
        "Overall Performance",
        "Top 10 Students",
        "Lower Performers",
        "Grade Wise Report",
        "Quiz Statistics"
    ]
)

# ==============================
# Overall Performance
# ==============================
if report_type == "Overall Performance":
    report = df.copy()
    st.subheader("Overall Dataset")

    st.dataframe(df, use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Students", len(report))
    c2.metric("Average %", round(report["Percentage"].mean(),2))
    c3.metric("Highest %", round(report["Percentage"].max(),2))
    c4.metric("Lowest %", round(report["Percentage"].min(),2))

# ==============================
# Top Students
# ==============================
elif report_type == "Top 10 Students":

    report = df.sort_values(
        "Percentage",
        ascending=False
    ).head(10)

    st.dataframe(report, use_container_width=True)

    fig = px.bar(
        report,
        x="Name",
        y="Percentage",
        color="Grade",
        text="Percentage",
        title="Top 10 Students"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# Lower Performers
# ==============================
elif report_type == "Lower Performers":

    threshold = st.slider(
        "Select Percentage",
        0,
        100,
        40
    )

    report = df[df["Percentage"] < threshold]

    st.dataframe(report, use_container_width=True)

    fig = px.bar(
        report,
        x="Name",
        y="Percentage",
        color="Grade",
        title="Lower Performers"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# Grade Wise
# ==============================
elif report_type == "Grade Wise Report":

    report = (
        df.groupby("Grade")
        .agg(
            Students=("Grade","count"),
            Average=("Percentage","mean"),
            Highest=("Percentage","max"),
            Lowest=("Percentage","min")
        )
        .reset_index()
    )

    st.dataframe(report, use_container_width=True)

    fig = px.bar(
        report,
        x="Grade",
        y="Students",
        color="Grade",
        title="Students by Grade"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# Quiz Statistics
# ==============================
elif report_type == "Quiz Statistics":

    quizzes = [
        "Quiz1","Quiz2","Quiz3",
        "Quiz4","Quiz5","Quiz6","Quiz7"
    ]

    report = pd.DataFrame({
        "Quiz": quizzes,
        "Average": df[quizzes].mean().values,
        "Highest": df[quizzes].max().values,
        "Lowest": df[quizzes].min().values
    })

    st.dataframe(report, use_container_width=True)

    fig = px.line(
        report,
        x="Quiz",
        y="Average",
        markers=True,
        title="Average Quiz Scores"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==============================
# Download CSV
# ==============================
st.divider()

csv = report.to_csv(index=False)

st.download_button(
    "⬇ Download CSV Report",
    csv,
    "report.csv",
    "text/csv"
)

# ==============================
# Download Excel
# ==============================
buffer = BytesIO()

with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    report.to_excel(writer, index=False)

st.download_button(
    "📥 Download Excel Report",
    buffer.getvalue(),
    "report.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ==============================
# Report Summary
# ==============================
st.divider()

st.subheader("📌 Report Summary")

st.success(f"""
✔ Total Students : {len(df)}

✔ Average Percentage : {round(df['Percentage'].mean(),2)}

✔ Highest Percentage : {round(df['Percentage'].max(),2)}

✔ Lowest Percentage : {round(df['Percentage'].min(),2)}

✔ Grade Categories : {df['Grade'].nunique()}
""")