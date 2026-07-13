import streamlit as st
import pandas as pd
import plotly.express as px
st.image("assets\images.jpg", width=80)
st.set_page_config(page_title="Leaderboard", layout="wide")

# ---------------------------
# Load Data
# ---------------------------
df = pd.read_csv("output/master_performance.csv")
df["Percentage"] = pd.to_numeric(df["Percentage"], errors="coerce").clip(0, 100)

# ---------------------------
# Title
# ---------------------------
st.title("🏆 Student Leaderboard")
st.markdown("View the highest-performing students based on their average score.")

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.header("Leaderboard Filters")

Grades = ["All"] + sorted(df["Grade"].dropna().unique().tolist())
selected_grade = st.sidebar.selectbox("Grade", Grades)

search_name = st.sidebar.text_input("🔍 Search Student")

top_n = st.sidebar.slider(
    "Show Top Students",
    min_value=5,
    max_value=min(100, len(df)),
    value=min(10, len(df))
)

# ---------------------------
# Apply Filters
# ---------------------------
filtered = df.copy()

if selected_grade != "All":
    filtered = filtered[filtered["Grade"] == selected_grade]

if search_name:
    filtered = filtered[
        filtered["Name"].str.contains(search_name, case=False, na=False)
    ]

# ---------------------------
# Ranking
# ---------------------------
filtered = filtered.dropna(subset=["Name"]).sort_values("Percentage", ascending=False).reset_index(drop=True)
filtered["Rank"] = filtered.index + 1

leaderboard = filtered.head(top_n).copy()
leaderboard["Name"] = leaderboard["Name"].astype(str)

# ---------------------------
# Top 3 Cards
# ---------------------------
st.subheader("🥇 Top Performers")

col1, col2, col3 = st.columns(3)

if len(leaderboard) >= 1:
    with col1:
        st.success("🥇 Rank 1")
        st.metric(
            leaderboard.iloc[0]["Name"],
            f"{leaderboard.iloc[0]['Percentage']:.2f}"
        )

if len(leaderboard) >= 2:
    with col2:
        st.info("🥈 Rank 2")
        st.metric(
            leaderboard.iloc[1]["Name"],
            f"{leaderboard.iloc[1]['Percentage']:.2f}"
        )

if len(leaderboard) >= 3:
    with col3:
        st.warning("🥉 Rank 3")
        st.metric(
            leaderboard.iloc[2]["Name"],
            f"{leaderboard.iloc[2]['Percentage']:.2f}"
        )

st.divider()

# ---------------------------
# Leaderboard Table
# ---------------------------
st.subheader("📋 Rankings")

display = leaderboard[
    ["Rank", "Name", "Grade", "Percentage"]
]

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True
)

# ---------------------------
# Score Chart
# ---------------------------
st.subheader("📊 Top Student Scores")

fig = px.bar(
    leaderboard,
    x="Name",
    y="Percentage",
    color="Grade",
    text="Percentage",
    title="Leaderboard Scores"
)

fig.update_traces(texttemplate="%{text:.1f}")

st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Progress Bars
# ---------------------------
st.subheader("📈 Performance Progress")

for _, row in leaderboard.iterrows():

    st.write(
        f"**#{row['Rank']}  {row['Name']}** "
        f"({row['Percentage']:.2f}%)"
    )

    st.progress(min(row["Percentage"] / 100, 1.0))

# ---------------------------
# Download
# ---------------------------
csv = leaderboard.to_csv(index=False)

st.download_button(
    "⬇ Download Leaderboard",
    csv,
    file_name="leaderboard.csv",
    mime="text/csv"
)