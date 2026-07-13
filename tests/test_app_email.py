from pathlib import Path

import os

import pandas as pd

import app
from app import resolve_gradecard_path


def test_resolve_gradecard_path_prefers_latest_matching_pdf(tmp_path):
    old_pdf = tmp_path / "vishujeetrathor_gmail_com.pdf"
    new_pdf = tmp_path / "Vishujeet_Rathore_vishujeetrathor_gmail_com.pdf"
    old_pdf.write_bytes(b"old")
    new_pdf.write_bytes(b"new")

    old_time = 1_700_000_000
    new_time = old_time + 60
    os.utime(old_pdf, (old_time, old_time))
    os.utime(new_pdf, (new_time, new_time))

    result = resolve_gradecard_path("vishujeetrathor@gmail.com", gradecards_dir=tmp_path)

    assert result == new_pdf


def test_build_master_report_replaces_old_gradecards(tmp_path, monkeypatch):
    gradecards_dir = tmp_path / "gradecards"
    gradecards_dir.mkdir()
    old_pdf = gradecards_dir / "student_old.pdf"
    old_pdf.write_bytes(b"old")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    monkeypatch.setattr(app, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(app, "GRADECARDS_DIR", gradecards_dir)
    monkeypatch.setattr(app, "MASTER_CSV", output_dir / "master_performance.csv")
    monkeypatch.setattr(app, "merge_files", lambda: pd.DataFrame([{"Email": "student@example.com", "Name": "Student"}]))
    monkeypatch.setattr(app, "calculate_performance", lambda df: df.assign(Percentage=80.0))
    monkeypatch.setattr(app, "assign_grade", lambda percent: "A")

    def fake_generate_gradecards(df, output_dir="gradecards"):
        new_pdf = Path(output_dir) / "student_new.pdf"
        new_pdf.write_bytes(b"new")
        return [str(new_pdf)]

    monkeypatch.setattr(app, "generate_gradecards", fake_generate_gradecards)

    app.build_master_report()

    assert not old_pdf.exists()
    assert (gradecards_dir / "student_new.pdf").exists()
