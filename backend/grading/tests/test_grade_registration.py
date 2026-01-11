"""
Django tests for grade registration functionality.
"""

import os  # noqa: F401
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
from django.test import TestCase

from grading.grade_registration import GradeRegistration


class GradeRegistrationTest(TestCase):
    """Test cases for GradeRegistration class."""

    def setUp(self):
        """Set up test data."""
        self.grade_reg = GradeRegistration()

        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.single_class_repo = Path(self.temp_dir) / "22g-class-java-homework"
        self.multi_class_repo = Path(self.temp_dir) / "23java-mode-homework"

        # Create directory structure
        self.single_class_repo.mkdir()
        self.multi_class_repo.mkdir()

        # Create test files and directories
        (self.single_class_repo / "第一次作业").mkdir()
        (self.single_class_repo / "第一次作业" / "朱俏任.docx").touch()
        (self.multi_class_repo / "23计算机1班").mkdir()
        (self.multi_class_repo / "23计算机1班" / "第一次作业").mkdir()
        (self.multi_class_repo / "23计算机1班" / "第一次作业" / "黄嘉伟.docx").touch()

        # Create Excel files
        self.single_class_excel = self.single_class_repo / "平时成绩登记表-22计算机G1班.xlsx"
        self.multi_class_excel = self.multi_class_repo / "平时成绩登记表-23计算机1-2班.xlsx"

        # Create empty Excel files
        pd.DataFrame().to_excel(self.single_class_excel, index=False)
        pd.DataFrame().to_excel(self.multi_class_excel, index=False)

        # Set repository path
        self.grade_reg.repo_path = self.single_class_repo

    def tearDown(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_repository_type_detection(self):
        """Test repository type detection (single class vs multi class)."""
        # Test single class repository
        self.assertFalse(self.grade_reg._is_multi_class_repo(self.single_class_repo))

        # Test multi class repository
        self.assertTrue(self.grade_reg._is_multi_class_repo(self.multi_class_repo))

    def test_extract_student_name(self):
        """Test extracting student name from filename."""
        # Test single class repository docx file
        docx_path = next(self.single_class_repo.rglob("*.docx"))
        student_name = self.grade_reg._extract_student_name(docx_path)
        self.assertTrue(2 <= len(student_name) <= 4)
        self.assertTrue(all("\u4e00" <= char <= "\u9fff" for char in student_name))

        # Test multi class repository docx file
        docx_path = next(self.multi_class_repo.rglob("*.docx"))
        student_name = self.grade_reg._extract_student_name(docx_path)
        self.assertTrue(2 <= len(student_name) <= 4)
        self.assertTrue(all("\u4e00" <= char <= "\u9fff" for char in student_name))

    @patch("grading.grade_registration.Document")
    def test_extract_grade_from_docx(self, mock_document):
        """Test extracting grade from docx file."""
        # Mock the Document class
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        # Mock paragraphs with grade information
        mock_paragraph = MagicMock()
        mock_paragraph.text = "老师评分：A"
        mock_doc.paragraphs = [mock_paragraph]

        # Test single class repository docx file
        docx_path = next(self.single_class_repo.rglob("*.docx"))
        grade = self.grade_reg._extract_grade_from_docx(docx_path)
        self.assertIn(grade, ["A", "B", "C", "D", "E"])

        # Test multi class repository docx file
        docx_path = next(self.multi_class_repo.rglob("*.docx"))
        grade = self.grade_reg._extract_grade_from_docx(docx_path)
        self.assertIn(grade, ["A", "B", "C", "D", "E"])

    def test_write_grade_to_excel(self):
        """Test writing grade to Excel file."""
        # Test single class Excel writing
        excel_path = str(self.single_class_excel)
        self.grade_reg.write_grade_to_excel(
            excel_path=excel_path, student_name="朱俏任", homework_dir_name="第一次作业", grade="A"
        )

        # Verify Excel file format
        df = pd.read_excel(self.single_class_excel, header=None)
        self.assertTrue(df.shape[1] >= 4, "Excel file should have at least 4 columns")

        # Test multi class Excel writing
        excel_path = str(self.multi_class_excel)
        self.grade_reg.write_grade_to_excel(
            excel_path=excel_path, student_name="黄嘉伟", homework_dir_name="第一次作业", grade="A"
        )

    @patch("grading.grade_registration.Document")
    def test_process_docx_files(self, mock_document):
        """Test processing entire repository docx files."""
        # Mock the Document class
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        # Mock paragraphs with grade information
        mock_paragraph = MagicMock()
        mock_paragraph.text = "老师评分：A"
        mock_doc.paragraphs = [mock_paragraph]

        # Test processing single class repository
        self.grade_reg.process_docx_files(str(self.single_class_repo))

        # Verify single class Excel file update
        df = pd.read_excel(self.single_class_excel, header=None)
        self.assertTrue(df.shape[1] >= 4, "Excel file should have at least 4 columns")

        # Verify grade was written
        student_rows = df[df[2] == "朱俏任"]
        if not student_rows.empty:
            student_row = student_rows.index[0]
            grade = df.iloc[student_row, 3]
            self.assertIsNotNone(grade, "Grade should not be None")
            self.assertIn(grade, ["A", "B", "C", "D", "E"], "Grade should be one of A, B, C, D, E")

        # Test processing multi class repository
        self.grade_reg.process_docx_files(str(self.multi_class_repo))

        # Verify multi class Excel file update
        df = pd.read_excel(self.multi_class_excel, header=None)
        self.assertTrue(df.shape[1] >= 4, "Excel file should have at least 4 columns")

        # Verify grade was written
        student_rows = df[df[2] == "黄嘉伟"]
        if not student_rows.empty:
            student_row = student_rows.index[0]
            grade = df.iloc[student_row, 3]
            self.assertIsNotNone(grade, "Grade should not be None")
            self.assertIn(grade, ["A", "B", "C", "D", "E"], "Grade should be one of A, B, C, D, E")

    def test_write_grade_to_excel_with_existing_data(self):
        """Test writing grade to Excel file with existing data."""
        # Create Excel file with existing data
        existing_data = pd.DataFrame(
            {
                "序号": [1, 2],
                "学号": ["2022001", "2022002"],
                "姓名": ["张三", "李四"],
                "第1次作业": ["A", "B"],
            }
        )
        existing_data.to_excel(self.single_class_excel, index=False)

        # Write new grade
        self.grade_reg.write_grade_to_excel(
            excel_path=str(self.single_class_excel),
            student_name="王五",
            homework_dir_name="第一次作业",
            grade="C",
        )

        # Verify data was preserved and new data was added
        df = pd.read_excel(self.single_class_excel)
        self.assertEqual(len(df), 3)  # Should have 3 students now
        self.assertTrue("王五" in df["姓名"].values)

    def test_write_grade_to_excel_duplicate_student(self):
        """Test writing grade for existing student."""
        # Create Excel file with existing student
        existing_data = pd.DataFrame(
            {"序号": [1], "学号": ["2022001"], "姓名": ["朱俏任"], "第1次作业": ["A"]}
        )
        existing_data.to_excel(self.single_class_excel, index=False)

        # Write grade for existing student
        self.grade_reg.write_grade_to_excel(
            excel_path=str(self.single_class_excel),
            student_name="朱俏任",
            homework_dir_name="第一次作业",
            grade="B",
        )

        # Verify grade was updated
        df = pd.read_excel(self.single_class_excel)
        student_row = df[df["姓名"] == "朱俏任"].iloc[0]
        self.assertEqual(student_row["第1次作业"], "B")

    def test_extract_student_name_edge_cases(self):
        """Test extracting student name with edge cases."""
        # Test with filename containing numbers
        test_path = Path("test/作业/张三123.docx")
        student_name = self.grade_reg._extract_student_name(test_path)
        self.assertEqual(student_name, "张三")

        # Test with filename containing special characters
        test_path = Path("test/作业/李四_作业.docx")
        student_name = self.grade_reg._extract_student_name(test_path)
        self.assertEqual(student_name, "李四")

        # Test with very short name
        test_path = Path("test/作业/王.docx")
        student_name = self.grade_reg._extract_student_name(test_path)
        self.assertEqual(student_name, "王")

    def test_repository_path_validation(self):
        """Test repository path validation."""
        # Test with valid path
        valid_path = Path(self.temp_dir)
        self.assertTrue(valid_path.exists())

        # Test with invalid path
        invalid_path = Path("/nonexistent/path")
        self.assertFalse(invalid_path.exists())

    def test_excel_file_creation(self):
        """Test Excel file creation when it doesn't exist."""
        # Remove existing Excel file
        if self.single_class_excel.exists():
            self.single_class_excel.unlink()

        # Write grade (should create Excel file)
        self.grade_reg.write_grade_to_excel(
            excel_path=str(self.single_class_excel),
            student_name="新学生",
            homework_dir_name="第一次作业",
            grade="A",
        )

        # Verify Excel file was created
        self.assertTrue(self.single_class_excel.exists())

        # Verify content
        df = pd.read_excel(self.single_class_excel)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["姓名"], "新学生")
        self.assertEqual(df.iloc[0]["第1次作业"], "A")

    def _create_excel_file(self, excel_path):
        """创建有效的Excel文件"""
        data = {
            "序号": [1, 2, 3],
            "学号": ["2022001", "2022002", "2022003"],
            "姓名": ["朱俏任", "李四", "王五"],
            "第1次作业": ["", "", ""],
            "第2次作业": ["", "", ""],
        }
        df = pd.DataFrame(data)
        df.to_excel(excel_path, index=False)
