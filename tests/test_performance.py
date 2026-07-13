import pandas as pd

from src.performance import calculate_performance


def test_calculate_performance_caps_percentage_at_100():
    df = pd.DataFrame(
        [{
            "Quiz1": 15,
            "Quiz2": 15,
            "Quiz3": 25,
            "Quiz4": 15,
        }]
    )

    result = calculate_performance(df)

    assert result.loc[0, "Percentage"] == 100.0
