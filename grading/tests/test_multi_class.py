"""
Django tests for multi class functionality.
"""

import tempfile
from pathlib import Path

import pandas as pd
from django.test import TestCase

from grading.grade_registration import GradeRegistration


class MultiClassTest(TestCase):
    """Test cases for multi class functionality."""

    def setUp(self):
        """Set up test data."""
        self.grader = GradeRegistration()
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir) / "23java-mode-homework"
        self.repo_path.mkdir()

        # Create test files and directories
        (self.repo_path / "23计算机1班").mkdir()
        (self.repo_path / "23计算机1班" / "第一次作业").mkdir()
        (self.repo_path / "23计算机1班" / "第一次作业" / "黄嘉伟.docx").touch()

        # Create Excel file with proper content
        self.excel_file = self.repo_path / "平时成绩登记表-23计算机1-2班.xlsx"
        self._create_excel_file(self.excel_file)

    def tearDown(self):
        """Clean up test data."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_excel_file(self, excel_path):
        """创建有效的Excel文件"""
        data = {
            "序号": [1, 2, 3],
            "学号": ["2023001", "2023002", "2023003"],
            "姓名": ["黄嘉伟", "张三", "李四"],
            "第1次作业": ["", "", ""],
            "第2次作业": ["", "", ""],
        }
        df = pd.DataFrame(data)
        df.to_excel(excel_path, index=False)

    def test_multi_class_processing(self):
        """Test multi class repository processing."""
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

            # Verify grade format is correct
            for col in ["第1次作业", "第2次作业"]:
                if col in df.columns:
                    for grade in df[col].dropna():
                        self.assertIn(
                            grade,
                            ["A", "B", "C", "D", "E"],
                            f"成绩登记表 {excel_file} 中的成绩格式不正确: {grade}",
                        )

    def test_class_directories(self):
        """Test class directory structure."""
        # Verify class directories exist
        class_dirs = [
            d for d in self.repo_path.iterdir() if d.is_dir() and d.name.startswith("23计算机")
        ]
        self.assertTrue(len(class_dirs) > 0, "未找到班级目录")

        # Verify each class directory has homework directories
        for class_dir in class_dirs:
            homework_dirs = [
                d
                for d in class_dir.iterdir()
                if d.is_dir() and ("作业" in d.name or "第" in d.name)
            ]
            self.assertTrue(len(homework_dirs) > 0, f"班级目录 {class_dir} 下未找到作业目录")

    def test_excel_files(self):
        """Test Excel files."""
        # Verify Excel files exist
        excel_files = list(self.repo_path.glob("平时成绩登记表-*.xlsx"))
        self.assertTrue(len(excel_files) > 0, "未找到成绩登记表文件")

        # Verify each Excel file content
        for excel_file in excel_files:
            df = pd.read_excel(excel_file)

            # Verify required columns exist
            required_columns = ["序号", "学号", "姓名"]
            for col in required_columns:
                self.assertTrue(col in df.columns, f"成绩登记表 {excel_file} 缺少必要的列: {col}")

            # Verify student list is not empty
            self.assertTrue(len(df) > 0, f"成绩登记表 {excel_file} 中没有学生记录")
