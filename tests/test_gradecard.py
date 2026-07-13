from pathlib import Path

import pandas as pd

from src.gradecard import generate_gradecards


def test_generate_gradecards_creates_pdf(tmp_path):
    df = pd.DataFrame(
        [
            {
                "Email": "aman@gmail.com",
                "Name": "Aman Sharma",
                "Enrollment No.": "2201234567",
                "Batch": "ML Summer Training 2026",
                "Quiz1": 8,
                "Quiz2": 9,
                "Quiz3": 10,
                "Quiz4": 7,
                "Percentage": 85.0,
                "Percentile": 92.45,
                "Rank": 12,
                "Grade": "A",
            }
        ]
    )

    output_dir = tmp_path / "gradecards"
    generated_files = generate_gradecards(df, output_dir=str(output_dir))

    assert len(generated_files) == 1
    pdf_path = Path(generated_files[0])
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000
