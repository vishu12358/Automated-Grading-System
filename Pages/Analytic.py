import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
st.image("assets\images.jpg", width=80)
st.set_page_config(page_title="Analytics", layout="wide")

# Load Data
df = pd.read_csv("output/master_performance.csv")
df["Percentage"] = pd.to_numeric(df["Percentage"], errors="coerce").clip(0, 100)

st.title("📊 Analytics Dashboard")

# ============================
# KPI Cards
# ============================

c1, c2, c3, c4 = st.columns(4)

c1.metric("Students", len(df))
c2.metric("Average %", round(df["Percentage"].mean(),2))
c3.metric("Highest %", round(df["Percentage"].max(),2))
c4.metric("Lowest %", round(df["Percentage"].min(),2))

st.divider()

# ============================
# Quiz Average
# ============================

quiz_columns = [
    "Quiz1",
    "Quiz2",
    "Quiz3",
    "Quiz4",
    "Quiz5",
    "Quiz6",
    "Quiz7"
]

quiz_avg = df[quiz_columns].mean().reset_index()

quiz_avg.columns = ["Quiz","Average"]

fig = px.bar(
    quiz_avg,
    x="Quiz",
    y="Average",
    color="Average",
    text="Average",
    title="Average Marks in Each Quiz"
)

fig.update_traces(texttemplate="%{text:.2f}")

st.plotly_chart(fig, use_container_width=True)

# ============================
# Grade Distribution
# ============================

col1,col2 = st.columns(2)

fig2 = px.pie(
    df,
    names="Grade",
    title="Grade Distribution",
    hole=0.5
)

col1.plotly_chart(fig2, use_container_width=True)

fig3 = px.histogram(
    df,
    x="Percentage",
    nbins=20,
    title="Percentage Distribution",
    color="Grade"
)

col2.plotly_chart(fig3, use_container_width=True)

st.divider()

# ============================
# Top 15 Students
# ============================

top = df.sort_values(
    "Percentage",
    ascending=False
).head(15)

fig4 = px.bar(
    top,
    x="Name",
    y="Percentage",
    color="Grade",
    text="Percentage",
    title="Top 15 Students"
)

fig4.update_traces(texttemplate="%{text:.2f}%")

st.plotly_chart(fig4, use_container_width=True)

st.divider()


# ============================
# Rank vs Percentage
# ============================

fig6 = px.scatter(
    df,
    x="Rank",
    y="Percentage",
    color="Grade",
    hover_name="Name",
    size="Total_Marks",
    title="Rank vs Percentage"
)

st.plotly_chart(fig6, use_container_width=True)

st.divider()

# ============================
# Summary Statistics
# ============================

st.subheader("📋 Dataset Summary")

st.dataframe(
    df.describe(),
    use_container_width=True
)