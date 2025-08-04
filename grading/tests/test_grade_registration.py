from django.test import TestCase
from pathlib import Path
import pandas as pd
import shutil
import tempfile
from grading.grade_registration import GradeRegistration

class GradeRegistrationTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.grade_reg = GradeRegistration()
        
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.single_class_repo = Path(self.temp_dir) / "22g-class-java-homework"
        self.multi_class_repo = Path(self.temp_dir) / "23java-mode-homework"
        self.single_class_repo.mkdir()
        self.multi_class_repo.mkdir()

        # 创建测试文件和目录
        (self.single_class_repo / "第一次作业").mkdir()
        (self.single_class_repo / "第一次作业" / "朱俏任.docx").touch()
        (self.multi_class_repo / "23计算机1班").mkdir()
        (self.multi_class_repo / "23计算机1班" / "第一次作业").mkdir()
        (self.multi_class_repo / "23计算机1班" / "第一次作业" / "黄嘉伟.docx").touch()
        
        # 原始Excel文件
        self.single_class_excel = self.single_class_repo / "平时成绩登记表-22计算机G1班.xlsx"
        self.multi_class_excel = self.multi_class_repo / "平时成绩登记表-23计算机1-2班.xlsx"
        
        # 创建空的Excel文件
        pd.DataFrame().to_excel(self.single_class_excel, index=False)
        pd.DataFrame().to_excel(self.multi_class_excel, index=False)

        # 创建备份
        self.single_class_excel_backup = Path(self.temp_dir) / "single_class_backup.xlsx"
        self.multi_class_excel_backup = Path(self.temp_dir) / "multi_class_backup.xlsx"
        
        if self.single_class_excel.exists():
            shutil.copy2(self.single_class_excel, self.single_class_excel_backup)
        
        if self.multi_class_excel.exists():
            shutil.copy2(self.multi_class_excel, self.multi_class_excel_backup)
            
        # 设置仓库路径
        self.grade_reg.repo_path = self.single_class_repo

    def tearDown(self):
        """Clean up test data"""
        shutil.rmtree(self.temp_dir)

    def test_repository_type_detection(self):
        """测试仓库类型判断（单班级/多班级）"""
        # 测试单班级仓库
        self.assertFalse(self.grade_reg._is_multi_class_repo(self.single_class_repo))
        
        # 测试多班级仓库
        self.assertTrue(self.grade_reg._is_multi_class_repo(self.multi_class_repo))
    
    def test_extract_student_name(self):
        """测试从文件名中提取学生姓名"""
        # 测试单班级仓库的docx文件
        docx_path = next(self.single_class_repo.rglob("*.docx"))
        student_name = self.grade_reg._extract_student_name(docx_path)
        self.assertTrue(2 <= len(student_name) <= 4)
        self.assertTrue(all('\u4e00' <= char <= '\u9fff' for char in student_name))
        
        # 测试多班级仓库的docx文件
        docx_path = next(self.multi_class_repo.rglob("*.docx"))
        student_name = self.grade_reg._extract_student_name(docx_path)
        self.assertTrue(2 <= len(student_name) <= 4)
        self.assertTrue(all('\u4e00' <= char <= '\u9fff' for char in student_name))
    
    def test_extract_grade_from_docx(self):
        """测试从docx文件中提取成绩"""
        # 测试单班级仓库的docx文件
        docx_path = next(self.single_class_repo.rglob("*.docx"))
        grade = self.grade_reg._extract_grade_from_docx(docx_path)
        self.assertIn(grade, ["A", "B", "C", "D", "E"])
        
        # 测试多班级仓库的docx文件
        docx_path = next(self.multi_class_repo.rglob("*.docx"))
        grade = self.grade_reg._extract_grade_from_docx(docx_path)
        self.assertIn(grade, ["A", "B", "C", "D", "E"])
    
    def test_write_grade_to_excel(self):
        """测试成绩写入Excel文件"""
        # 测试单班级Excel写入
        excel_path = str(self.single_class_repo / "平时成绩登记表-22计算机G1班.xlsx")
        self.grade_reg.write_grade_to_excel(
            excel_path=excel_path,
            student_name="朱俏任",
            homework_dir_name="第一次作业",
            grade="A"
        )
    
        # 验证Excel文件格式
        df = pd.read_excel(self.single_class_excel, header=None)
        self.assertTrue(df.shape[1] >= 4, "Excel file should have at least 4 columns")
        
        # 测试多班级Excel写入
        excel_path = str(self.multi_class_repo / "平时成绩登记表-23计算机1-2班.xlsx")
        self.grade_reg.write_grade_to_excel(
            excel_path=excel_path,
            student_name="黄嘉伟",
            homework_dir_name="第一次作业",
            grade="A"
        )
    
    def test_process_docx_files(self):
        """测试处理整个仓库的docx文件"""
        # 测试处理单班级仓库
        self.grade_reg.process_docx_files(str(self.single_class_repo))
        
        # 验证单班级Excel文件更新
        df = pd.read_excel(self.single_class_excel, header=None)
        # 检查Excel文件是否存在且格式正确
        self.assertTrue(df.shape[1] >= 4, "Excel file should have at least 4 columns")
        
        # 验证成绩是否被写入
        # 找到"朱俏任"的行
        student_rows = df[df[2] == "朱俏任"]
        if not student_rows.empty:
            student_row = student_rows.index[0]
            # 检查第1次作业的成绩（第4列）
            grade = df.iloc[student_row, 3]
            self.assertIsNotNone(grade, "Grade should not be None")
            self.assertIn(grade, ["A", "B", "C", "D", "E"], "Grade should be one of A, B, C, D, E")
        # 测试处理多班级仓库
        self.grade_reg.process_docx_files(str(self.multi_class_repo))
        
        # 验证多班级Excel文件更新
        df = pd.read_excel(self.multi_class_excel, header=None)
        # 检查Excel文件是否存在且格式正确
        self.assertTrue(df.shape[1] >= 4, "Excel file should have at least 4 columns")
        
        # 验证成绩是否被写入
        # 找到"黄嘉伟"的行
        student_rows = df[df[2] == "黄嘉伟"]
        if not student_rows.empty:
            student_row = student_rows.index[0]
            # 检查第1次作业的成绩（第4列）
            grade = df.iloc[student_row, 3]
            self.assertIsNotNone(grade, "Grade should not be None")
            self.assertIn(grade, ["A", "B", "C", "D", "E"], "Grade should be one of A, B, C, D, E") 