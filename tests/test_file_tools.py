from __future__ import annotations

from tools.file_tools import read_course_file


def test_read_course_file_success(tmp_path):
    courses = tmp_path / "courses"
    courses.mkdir()
    (courses / "cv.md").write_text("# CV\n- 卷积", encoding="utf-8")

    result = read_course_file("cv.md", courses_dir=courses)
    assert result["success"] is True
    assert "卷积" in result["data"]["content"]


def test_read_course_file_rejects_traversal(tmp_path):
    courses = tmp_path / "courses"
    courses.mkdir()
    outside = tmp_path / "secret.md"
    outside.write_text("secret", encoding="utf-8")

    result = read_course_file("../secret.md", courses_dir=courses)
    assert result["success"] is False
    assert "之外" in result["error"]


def test_read_course_file_rejects_extension(tmp_path):
    courses = tmp_path / "courses"
    courses.mkdir()
    (courses / "run.py").write_text("print(1)", encoding="utf-8")

    result = read_course_file("run.py", courses_dir=courses)
    assert result["success"] is False
    assert "TXT" in result["error"]
