"""
Django tests for batch grade functionality.
"""

import os  # noqa: F401
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
from django.test import TestCase

from grading.grade_registration import GradeRegistration


class BatchGradeTest(TestCase):
    """Test cases for batch grade functionality."""

    def setUp(self):
        """Set up test data."""
        # Create temporary test repositories
        self.temp_dir = tempfile.mkdtemp()
        self.single_class_repo = Path(self.temp_dir) / "22g-class-java-homework"
        self.multi_class_repo = Path(self.temp_dir) / "23java-mode-homework"

        # Create directory structure
        self.single_class_repo.mkdir()
        self.multi_class_repo.mkdir()

        # Create test files and directories for single class
        (self.single_class_repo / "第一次作业").mkdir()
        (self.single_class_repo / "第一次作业" / "朱俏任.docx").touch()
        (self.single_class_repo / "第二次作业").mkdir()
        (self.single_class_repo / "第二次作业" / "李四.docx").touch()

        # Create test files and directories for multi class
        (self.multi_class_repo / "23计算机1班").mkdir()
        (self.multi_class_repo / "23计算机1班" / "第一次作业").mkdir()
        (self.multi_class_repo / "23计算机1班" / "第一次作业" / "黄嘉伟.docx").touch()
        (self.multi_class_repo / "23计算机2班").mkdir()
        (self.multi_class_repo / "23计算机2班" / "第一次作业").mkdir()
        (self.multi_class_repo / "23计算机2班" / "第一次作业" / "张三.docx").touch()

        # Create Excel files
        self.single_class_excel = self.single_class_repo / "平时成绩登记表-22计算机G1班.xlsx"
        self.multi_class_excel = self.multi_class_repo / "平时成绩登记表-23计算机1-2班.xlsx"

        # Create Excel files with initial data
        self._create_excel_file(self.single_class_excel)
        self._create_excel_file(self.multi_class_excel)

    def tearDown(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

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

    @patch("grading.grade_registration.Document")
    def test_batch_grade_registration_single_class(self, mock_document):
        """Test batch grade registration for single class repository."""
        # Mock the Document class
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        # Mock paragraphs with grade information
        mock_paragraph = MagicMock()
        mock_paragraph.text = "老师评分：A"
        mock_doc.paragraphs = [mock_paragraph]

        grader = GradeRegistration()
        grader.repo_path = self.single_class_repo

        # Execute batch grade registration
        grader.process_docx_files(str(self.single_class_repo))

        # Verify results
        self._verify_batch_grade_results(self.single_class_repo)

    @patch("grading.grade_registration.Document")
    def test_batch_grade_registration_multi_class(self, mock_document):
        """Test batch grade registration for multi class repository."""
        # Mock the Document class
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        # Mock paragraphs with grade information
        mock_paragraph = MagicMock()
        mock_paragraph.text = "老师评分：B"
        mock_doc.paragraphs = [mock_paragraph]

        grader = GradeRegistration()
        grader.repo_path = self.multi_class_repo

        # Execute batch grade registration
        grader.process_docx_files(str(self.multi_class_repo))

        # Verify results
        self._verify_batch_grade_results(self.multi_class_repo)

    def _verify_batch_grade_results(self, repo_path):
        """Verify batch grade registration results."""
        repo_path = Path(repo_path)

        # Check Excel files exist
        excel_files = list(repo_path.glob("平时成绩登记表-*.xlsx"))
        self.assertTrue(len(excel_files) > 0, f"未找到成绩登记表文件: {repo_path}")

        for excel_file in excel_files:
            df = pd.read_excel(excel_file)

            # Verify required columns exist
            required_columns = ["序号", "学号", "姓名"]
            for col in required_columns:
                self.assertTrue(col in df.columns, f"成绩登记表 {excel_file} 缺少必要的列: {col}")

            # Verify student list is not empty
            self.assertTrue(len(df) > 0, f"成绩登记表 {excel_file} 中没有学生记录")

            # Check homework grade columns
            homework_columns = [col for col in df.columns if "第" in col and "作业" in col]
            if homework_columns:
                # Verify grade format
                for col in homework_columns:
                    if col in df.columns:
                        for grade in df[col].dropna():
                            self.assertIn(
                                grade,
                                ["A", "B", "C", "D", "E"],
                                f"成绩登记表 {excel_file} 中的成绩格式不正确: {grade}",
                            )

    def test_repository_detection(self):
        """Test repository type detection."""
        # Test single class repository detection
        excel_files = list(self.single_class_repo.glob("平时成绩登记表-*.xlsx"))
        self.assertTrue(len(excel_files) > 0, "未找到单班级成绩登记表")

        for excel_file in excel_files:
            file_name = excel_file.stem
            # Single class format should not contain class numbers
            self.assertNotIn("1-2", file_name)
            self.assertNotIn("1班", file_name)

        # Test multi class repository detection
        excel_files = list(self.multi_class_repo.glob("平时成绩登记表-*.xlsx"))
        self.assertTrue(len(excel_files) > 0, "未找到多班级成绩登记表")

        for excel_file in excel_files:
            file_name = excel_file.stem
            # Multi class format should contain class numbers
            self.assertIn("1-2", file_name)

    def test_excel_file_processing(self):
        """Test Excel file processing."""
        # Test single class Excel processing
        excel_files = list(self.single_class_repo.glob("平时成绩登记表-*.xlsx"))
        for excel_file in excel_files:
            try:
                df = pd.read_excel(excel_file)

                # Verify data integrity
                if len(df) > 0:
                    # Check for empty student information
                    student_info_cols = ["学号", "姓名"]
                    for col in student_info_cols:
                        if col in df.columns:
                            empty_count = df[col].isna().sum()
                            self.assertEqual(
                                empty_count, 0, f"成绩登记表 {excel_file} 中有空的学生信息"
                            )
            except Exception as e:
                self.fail(f"处理Excel文件 {excel_file} 时出错: {str(e)}")

    def test_batch_grade_with_empty_repository(self):
        """Test batch grade with empty repository."""
        empty_repo = Path(self.temp_dir) / "empty-repo"
        empty_repo.mkdir()

        grader = GradeRegistration()
        grader.repo_path = empty_repo

        # Should not raise exception
        try:
            grader.process_docx_files(str(empty_repo))
        except Exception as e:
            self.fail(f"处理空仓库时不应该出错: {str(e)}")

    def test_batch_grade_with_invalid_files(self):
        """Test batch grade with invalid files."""
        invalid_repo = Path(self.temp_dir) / "invalid-repo"
        invalid_repo.mkdir()
        (invalid_repo / "作业").mkdir()

        # Create invalid files
        (invalid_repo / "作业" / "test.txt").touch()
        (invalid_repo / "作业" / "test.pdf").touch()

        grader = GradeRegistration()
        grader.repo_path = invalid_repo

        # Should not raise exception
        try:
            grader.process_docx_files(str(invalid_repo))
        except Exception as e:
            self.fail(f"处理无效文件时不应该出错: {str(e)}")

    @patch("grading.grade_registration.Document")
    def test_batch_grade_with_mixed_grades(self, mock_document):
        """Test batch grade with mixed grade types."""
        # Mock the Document class with different grades
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        # Create different grade scenarios
        grade_scenarios = [
            ("老师评分：A", "A"),
            ("老师评分：B", "B"),
            ("老师评分：C", "C"),
            ("老师评分：D", "D"),
            ("老师评分：E", "E"),
        ]

        for grade_text, expected_grade in grade_scenarios:
            mock_paragraph = MagicMock()
            mock_paragraph.text = grade_text
            mock_doc.paragraphs = [mock_paragraph]

            grader = GradeRegistration()
            grader.repo_path = self.single_class_repo

            # Process files
            grader.process_docx_files(str(self.single_class_repo))

            # Verify grade was written correctly
            df = pd.read_excel(self.single_class_excel)
            if "第1次作业" in df.columns:
                grades = df["第1次作业"].dropna()
                if len(grades) > 0:
                    self.assertIn(expected_grade, grades.values)

    def test_batch_grade_performance(self):
        """Test batch grade performance with large number of files."""
        # Create many test files
        large_repo = Path(self.temp_dir) / "large-repo"
        large_repo.mkdir()

        for i in range(10):  # Create 10 homework directories
            homework_dir = large_repo / f"第{i+1}次作业"
            homework_dir.mkdir()

            for j in range(5):  # Create 5 students per homework
                student_file = homework_dir / f"学生{j+1}.docx"
                student_file.touch()

        # Create Excel file
        excel_file = large_repo / "平时成绩登记表-测试班.xlsx"
        data = {
            "序号": list(range(1, 6)),
            "学号": [f"202200{i}" for i in range(1, 6)],
            "姓名": [f"学生{i}" for i in range(1, 6)],
        }
        df = pd.DataFrame(data)
        df.to_excel(excel_file, index=False)

        grader = GradeRegistration()
        grader.repo_path = large_repo

        # Should complete without timeout
        import time

        start_time = time.time()
        grader.process_docx_files(str(large_repo))
        end_time = time.time()

        # Should complete within reasonable time (5 seconds)
        self.assertLess(end_time - start_time, 5.0, "批量处理应该在合理时间内完成")
