"""
Django tests for single class functionality.
"""

import tempfile
from pathlib import Path

import pandas as pd
from django.test import TestCase

from grading.grade_registration import GradeRegistration


class SingleClassTest(TestCase):
    """Test cases for single class functionality."""

    def setUp(self):
        """Set up test data."""
        self.grader = GradeRegistration()
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir) / "22g-class-java-homework"
        self.repo_path.mkdir()

        # Create test files and directories
        (self.repo_path / "第一次作业").mkdir()
        (self.repo_path / "第一次作业" / "朱俏任.docx").touch()

        # Create Excel file with proper content
        self.excel_file = self.repo_path / "平时成绩登记表-22计算机G1班.xlsx"
        self._create_excel_file(self.excel_file)

    def tearDown(self):
        """Clean up test data."""
        import shutil

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

    def test_single_class_processing(self):
        """Test single class repository processing."""
        # Create GradeRegistration instance
        grader = GradeRegistration()

        # Process docx files
        grader.process_docx_files(str(self.repo_path))

        # Verify grades were written correctly
        excel_files = list(self.repo_path.glob("平时成绩登记表-*.xlsx"))
        self.assertTrue(len(excel_files) > 0, "未找到成绩登记表文件")

        for excel_file in excel_files:
            df = pd.read_excel(excel_file)

            # Verify grade columns exist
            self.assertTrue("第1次作业" in df.columns, f"成绩登记表 {excel_file} 缺少第1次作业列")
            self.assertTrue("第2次作业" in df.columns, f"成绩登记表 {excel_file} 缺少第2次作业列")
            self.assertTrue("第3次作业" in df.columns, f"成绩登记表 {excel_file} 缺少第3次作业列")

            # Verify grade format is correct
            for col in ["第1次作业", "第2次作业", "第3次作业"]:
                if col in df.columns:
                    for grade in df[col].dropna():
                        self.assertIn(
                            grade,
                            ["A", "B", "C", "D", "E"],
                            f"成绩登记表 {excel_file} 中的成绩格式不正确: {grade}",
                        )

    def test_homework_directories(self):
        """Test homework directory structure."""
        # Verify homework directories exist
        homework_dirs = [
            d
            for d in self.repo_path.iterdir()
            if d.is_dir() and ("作业" in d.name or "第" in d.name)
        ]
        self.assertTrue(len(homework_dirs) > 0, "未找到作业目录")

        # Verify each homework directory has docx files
        for homework_dir in homework_dirs:
            docx_files = list(homework_dir.glob("*.docx"))
            self.assertTrue(len(docx_files) > 0, f"作业目录 {homework_dir} 下未找到docx文件")

    def test_excel_file(self):
        """Test Excel file."""
        # Verify Excel file exists
        excel_files = list(self.repo_path.glob("平时成绩登记表-*.xlsx"))
        self.assertTrue(len(excel_files) > 0, "未找到成绩登记表文件")

        # Verify Excel file content
        for excel_file in excel_files:
            df = pd.read_excel(excel_file)

            # Verify required columns exist
            required_columns = ["序号", "学号", "姓名"]
            for col in required_columns:
                self.assertTrue(col in df.columns, f"成绩登记表 {excel_file} 缺少必要的列: {col}")

            # Verify student list is not empty
            self.assertTrue(len(df) > 0, f"成绩登记表 {excel_file} 中没有学生记录")
