import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Dashboard",
    layout="wide",
    page_icon="🎓"
)

st.image("assets/images.jpg", width=80)

df = pd.read_csv("output/master_performance.csv")
df.columns = df.columns.str.strip()
df = df.drop(columns=["Name.1"], errors="ignore")
df["Percentage"] = pd.to_numeric(df["Percentage"], errors="coerce").clip(0, 100)
df = df.dropna(subset=["Name"])

st.title("🎓 Automated Training Performance Dashboard")
st.caption("Monitor student performance with interactive analytics and reports.")

st.sidebar.header("Filters")

grade = st.sidebar.multiselect(
    "Grade",
    sorted(df["Grade"].unique()),
    default=sorted(df["Grade"].unique())
)

filtered = df[df["Grade"].isin(grade)]

search = st.text_input(
    "🔍 Search Student",
    placeholder="Enter student name..."
)

if search:
    filtered = filtered[
        filtered["Name"].str.contains(search, case=False, na=False)
    ]

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("👨‍🎓 Students", len(filtered))
c2.metric("📈 Average %", round(filtered["Percentage"].mean(), 2))
c3.metric("🥇 Highest %", round(filtered["Percentage"].max(), 2))
c4.metric("📉 Lowest %", round(filtered["Percentage"].min(), 2))
c5.metric(
    "✅ Pass Rate",
    round((filtered["Percentage"] >= 40).mean() * 100, 2)
)

st.divider()

left, right = st.columns(2)
grade_count = (
    filtered["Grade"]
    .value_counts()
    .reset_index()
)

grade_count.columns = ["Grade", "Students"]

fig1 = px.pie(
    grade_count,
    names="Grade",
    values="Students",
    hole=0.55,
    title="Grade Distribution"
)

left.plotly_chart(fig1, use_container_width=True)

fig2 = px.box(
    filtered,
    x="Grade",
    y="Percentage",
    color="Grade",
    title="Percentage Spread by Grade"
)

right.plotly_chart(fig2, use_container_width=True)

left, right = st.columns(2)
top10 = filtered.nlargest(10, "Percentage")

fig3 = px.bar(
    top10,
    x="Percentage",
    y="Name",
    orientation="h",
    color="Grade",
    text="Percentage",
    title="🏆 Top 10 Students"
)

fig3.update_traces(texttemplate="%{text:.2f}%")

left.plotly_chart(fig3, use_container_width=True)

all_cols = df.columns.tolist()
quiz_cols = [col for col in all_cols if col.startswith("Quiz") and not col.endswith("_Max")]

if quiz_cols:
    quiz_avg = filtered[quiz_cols].mean().reset_index()
    quiz_avg.columns = ["Quiz", "Average"]

    fig4 = px.line(
        quiz_avg,
        x="Quiz",
        y="Average",
        markers=True,
        title="📈 Quiz-wise Average"
    )

    right.plotly_chart(fig4, use_container_width=True)

st.divider()

st.subheader("🤖 AI Insights")

st.info(f"""
**Performance Summary**

- 👨‍🎓 Total Students: **{len(filtered)}**
- 📈 Average Percentage: **{filtered['Percentage'].mean():.2f}%**
- 🥇 Highest Percentage: **{filtered['Percentage'].max():.2f}%**
- 📉 Lowest Percentage: **{filtered['Percentage'].min():.2f}%**
- ✅ Pass Rate: **{(filtered['Percentage'] >= 40).mean() * 100:.2f}%**
- 🏆 Most Common Grade: **{filtered['Grade'].mode()[0]}**
""")

st.subheader("📋 Student Performance")

st.dataframe(
    filtered.sort_values(
        "Percentage",
        ascending=False
    ),
    use_container_width=True
)

st.subheader("⬇ Download Data")

csv = filtered.to_csv(index=False)

st.download_button(
    "Download CSV",
    csv,
    "Performance.csv",
    "text/csv"
)