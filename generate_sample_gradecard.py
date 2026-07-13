from pathlib import Path
import pandas as pd
from src.gradecard import generate_gradecards

output_dir = Path('gradecards')
output_dir.mkdir(parents=True, exist_ok=True)

sample_df = pd.DataFrame([
    {
        'Email': 'aman@gmail.com',
        'Name': 'Aman Sharma',
        'Enrollment No.': '2201234567',
        'Batch': 'ML Summer Training 2026',
        'Quiz1': 8,
        'Quiz2': 9,
        'Quiz3': 10,
        'Quiz4': 7,
        'Percentage': 85.0,
        'Percentile': 92.45,
        'Rank': 12,
        'Grade': 'A',
    }
])
created = generate_gradecards(sample_df, output_dir=str(output_dir))
print(created[0])
