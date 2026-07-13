from pathlib import Path
import pandas as pd
import numpy as np


def extract_score(score_text):
    """Safely extract the numerator from a '85/100' string."""
    if pd.isna(score_text):
        return np.nan
    text = str(score_text).strip()
    if not text:
        return np.nan
    try:
        return float(text.split('/')[0].strip())
    except ValueError:
        return np.nan


def extract_max(score_text):
    """Safely extract the denominator from a '85/100' string."""
    if pd.isna(score_text):
        return np.nan
    parts = str(score_text).split('/')
    if len(parts) > 1:
        try:
            return float(parts[1].strip())
        except ValueError:
            return np.nan
    return np.nan


def _safe_get_column(df, possible_names):
    """Find a column in a DataFrame ignoring case and extra spaces."""
    # Normalize actual column names: lowercase, strip spaces, replace spaces with underscores
    col_map = {c.strip().lower().replace(" ", "_"): c for c in df.columns}
    
    for name in possible_names:
        normalized = name.strip().lower().replace(" ", "_")
        if normalized in col_map:
            return col_map[normalized]
    return None


def merge_files():
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = next((path for path in [root_dir / "Data", root_dir / "data"] if path.exists()), None)

    if data_dir is None:
        raise FileNotFoundError("No data directory found. Expected a 'Data' or 'data' folder.")

    files = sorted(data_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    master = None
    quiz_indices = []

    for i, file in enumerate(files, start=1):
        try:
            df = pd.read_csv(file)
        except Exception as e:
            print(f"⚠️ Warning: Could not read {file.name}. Skipping. Error: {e}")
            continue

        # Flexible column matching (handles "Total Score", "total_score", "Email ", etc.)
        email_col = _safe_get_column(df, ["Email", "E-mail", "email"])
        name_col = _safe_get_column(df, ["Name", "Student Name", "name"])
        score_col = _safe_get_column(df, ["Total score", "Total Score", "total_score", "Score", "score"])

        if not all([email_col, name_col, score_col]):
            print(f"⚠️ Warning: {file.name} is missing required columns (Email, Name, Total Score). Skipping.")
            continue

        # Standardize names for this iteration
        df = df.rename(columns={
            email_col: "Email", 
            name_col: f"Name_{i}", 
            score_col: "TotalScoreCol"
        })

        df[f"Quiz{i}"] = df["TotalScoreCol"].apply(extract_score)
        df[f"Quiz{i}_Max"] = df["TotalScoreCol"].apply(extract_max)

        temp_df = df[["Email", f"Name_{i}", f"Quiz{i}", f"Quiz{i}_Max"]]

        if master is None:
            master = temp_df
        else:
            master = pd.merge(master, temp_df, on="Email", how="outer")
        
        quiz_indices.append(i)

    if master is None or master.empty:
        raise ValueError("No valid CSV data could be merged. Check your files.")

    # Combine name columns safely (handles missing names in ANY quiz)
    name_cols = [col for col in master.columns if col.startswith("Name_")]
    if name_cols:
        # ffill forward, bfill backward, then take the first column which is now fully populated
        master["Name"] = master[name_cols].ffill(axis=1).bfill(axis=1).iloc[:, 0]
        master.drop(columns=name_cols, inplace=True)

    # Strict, predictable column ordering (prevents jumbling)
    ordered_cols = ["Email", "Name"]
    for i in quiz_indices:
        ordered_cols.append(f"Quiz{i}")
        ordered_cols.append(f"Quiz{i}_Max")
        
    master = master[ordered_cols]

    return master