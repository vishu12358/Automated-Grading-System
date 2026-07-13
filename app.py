from pathlib import Path

import os
import pandas as pd
import streamlit as st

from src.email_sender import send_file_to_self, send_gradecard, send_all_gradecards
from src.secure_store import save_credentials as save_encrypted_credentials, load_credentials as load_encrypted_credentials
from src.gradecard import generate_gradecards
from src.grading import assign_grade
from src.merge_data import merge_files
from src.performance import calculate_performance

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output"
GRADECARDS_DIR = ROOT_DIR / "gradecards"
MASTER_CSV = OUTPUT_DIR / "master_performance.csv"


def resolve_gradecard_path(student_email, gradecards_dir=GRADECARDS_DIR):
    normalized_email = student_email.replace("@", "_").replace(".", "_").lower()
    candidates = [
        path
        for path in gradecards_dir.glob("*.pdf")
        if normalized_email in path.name.lower()
    ]
    if not candidates:
        return None

    exact_matches = [
        path for path in candidates if path.name.lower().endswith(f"{normalized_email}.pdf")
    ]
    preferred_candidates = exact_matches or candidates
    return max(preferred_candidates, key=lambda path: path.stat().st_mtime)


def build_master_report():
    df = merge_files()
    df = calculate_performance(df)

    df["Percentile"] = df["Percentage"].rank(pct=True) * 100
    df["Rank"] = df["Percentage"].rank(ascending=False, method="min")
    df["Grade"] = df["Percentage"].apply(assign_grade)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GRADECARDS_DIR.mkdir(parents=True, exist_ok=True)

    for old_pdf in GRADECARDS_DIR.glob("*.pdf"):
        old_pdf.unlink(missing_ok=True)

    df.to_csv(MASTER_CSV, index=False)
    generate_gradecards(df, output_dir=str(GRADECARDS_DIR))
    return df


def load_master_report():
    if not MASTER_CSV.exists():
        return None

    df = pd.read_csv(MASTER_CSV)
    if "Name.1" in df.columns and "Name" in df.columns:
        df["Name"] = df["Name.1"].combine_first(df["Name"])
        df = df.drop(columns=["Name.1"])

    if "Percentage" in df.columns and df["Percentage"].max() > 100:
        return build_master_report()

    return df


def main():
    st.set_page_config(
        page_title="Automated Training Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📊 Automated Training Performance Dashboard")
    st.markdown(
        """
        ### Welcome!

        Generate a fresh report and grade cards, then review the latest performance data below.
        """
    )

    if st.button("🔄 Generate / Refresh Reports", use_container_width=True):
        with st.spinner("Preparing the latest report and grade cards..."):
            df = build_master_report()
        st.success(f"Generated report for {len(df)} students.")

    df = load_master_report()
    if df is None:
        st.info("No report has been generated yet. Click the button above to create one.")
        return

    display_df = df.drop(columns=["Email", "Total_Max", "Name.1"], errors="ignore")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Students", len(df))
    col2.metric("Average %", round(df["Percentage"].mean(), 2))
    col3.metric("Highest %", round(df["Percentage"].max(), 2))
    col4.metric("Lowest %", round(df["Percentage"].min(), 2))

    # ---------------------------
    # Send Gradecard PDF
    # ---------------------------
    st.subheader("Send Gradecard PDF")
    students = df[["Email", "Name"]].drop_duplicates().fillna("")
    student_options = students.apply(lambda r: f"{r['Name']} <{r['Email']}>", axis=1).tolist()
    selected = st.selectbox("Select student", student_options)
    if selected:
        import re
        m = re.search(r"<(.+?)>$", selected)
        selected_email = m.group(1) if m else selected
        selected_name = ""
        matched = students[students["Email"] == selected_email]
        if not matched.empty:
            selected_name = matched.iloc[0]["Name"]

        col_send_1, col_send_2 = st.columns(2)

        with col_send_1:
            confirm_bulk = st.checkbox("I confirm: send grade cards to ALL students", key="confirm_bulk")
            if st.button("Send gradecards to all", key="send_gc_all"):
                if not confirm_bulk:
                    st.warning("Please confirm bulk sending by checking the box first.")
                else:
                    with st.spinner("Sending gradecards to all students..."):
                        try:
                            sent, failed = send_all_gradecards(df, self_send=False)
                            if failed:
                                st.warning(f"Sent {sent} emails; {len(failed)} failures.")
                                for email, err in failed:
                                    st.text(f"Failed: {email} -> {err}")
                            else:
                                st.success(f"Bulk emails sent successfully ({sent} emails).")
                        except Exception as e:
                            st.error(f"Bulk send failed: {e}")

        with col_send_2:
            if st.button("Send gradecard to student", key="send_gc_student"):
                pdf_path = resolve_gradecard_path(selected_email)
                if not pdf_path:
                    st.error("Gradecard not found. Generate reports first.")
                else:
                    try:
                        send_gradecard(selected_email, selected_name or selected_email, str(pdf_path), self_send=False)
                        st.success(f"Gradecard sent to {selected_email}.")
                    except Exception as e:
                        st.error(f"Failed to send gradecard: {e}")

    st.markdown("---")
    st.subheader("SMTP Sender Details")
    sender_input = st.text_input("Sender email", value=os.getenv("SENDER_EMAIL", ""), key="report_sender")
    pwd_input = st.text_input("App password", value=os.getenv("APP_PASSWORD", ""), type="password", key="report_password")
    st.caption("Use a valid Gmail App Password if your account requires 2FA.")
    # Determine currently selected student (if any)
    selected_email = None
    selected_name = None
    try:
        import re
        if selected:
            m = re.search(r"<(.+?)>$", selected)
            selected_email = m.group(1) if m else selected
            matched = students[students["Email"] == selected_email]
            if not matched.empty:
                selected_name = matched.iloc[0]["Name"]
    except Exception:
        selected_email = None

    if st.button("📧 Send report to self", use_container_width=True):
        if not sender_input or not pwd_input:
            st.error("Please enter both sender email and app password before sending.")
        else:
            os.environ["SENDER_EMAIL"] = sender_input
            os.environ["APP_PASSWORD"] = pwd_input.replace(" ", "")
            # Prefer sending the selected student's gradecard PDF to self.
            try:
                if selected_email:
                    pdf_path = resolve_gradecard_path(selected_email)
                else:
                    pdf_path = None

                if pdf_path:
                    send_file_to_self(
                        str(pdf_path),
                        f"Gradecard: {selected_name or selected_email}",
                        f"Attached gradecard for {selected_name or selected_email}."
                    )
                    st.success(f"Gradecard sent to {sender_input}.")
                else:
                    # Fallback: send the master CSV if no gradecard found
                    send_file_to_self(
                        str(MASTER_CSV),
                        "Automated Training Performance Report",
                        "Please find the latest master performance report attached."
                    )
                    st.success("No gradecard found for the selected student; master report sent instead.")
            except Exception as e:
                st.error(f"Failed to send report: {e}")

if __name__ == "__main__":
    main()