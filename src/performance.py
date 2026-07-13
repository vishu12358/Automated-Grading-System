import pandas as pd


def calculate_performance(df):
    # 1. Copy — never mutate the input
    df = df.copy()

    # 2. Derive max columns FROM score columns — keeps them in sync
    score_cols = [col for col in df.columns if col.startswith("Quiz") and not col.endswith("_Max")]
    max_cols = [f"{col}_Max" for col in score_cols]

    # 3. Only fill columns that actually exist in the DataFrame
    existing_scores = [c for c in score_cols if c in df.columns]
    existing_maxs = [c for c in max_cols if c in df.columns]

    df[existing_scores] = df[existing_scores].fillna(0)
    df[existing_maxs] = df[existing_maxs].fillna(0)

    # 4. Guard: warn if nothing matched
    if not existing_scores:
        print("⚠️  No Quiz columns found. Returning DataFrame with zero totals.")
        df["Total_Marks"] = 0
        df["Total_Max"] = 0
        df["Percentage"] = 0.0
        return df

    df["Total_Marks"] = df[existing_scores].sum(axis=1)
    df["Total_Max"] = df[existing_maxs].sum(axis=1)

    df["Percentage"] = (
        df["Total_Marks"]
        .div(df["Total_Max"].replace({0: 1}))
        .mul(100)
        .clip(upper=100)
        .round(2)                    # cleaner output
    )

    return df