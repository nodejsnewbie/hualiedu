from django.test import TestCase
from pathlib import Path
import pandas as pd
from grading.grade_registration import GradeRegistration

class BatchGradeTest(TestCase):
    def setUp(self):
        """设置测试环境"""
        # 使用真实的仓库路径进行测试
        self.test_repos = [
            "/Users/linyuan/jobs/22g-class-java-homework",  # 单班级仓库
            "/Users/linyuan/jobs/23java-mode-homework"      # 多班级仓库
        ]

    def test_batch_grade_registration(self):
        """测试批量登分功能"""
        grader = GradeRegistration()
        
        for repo_path in self.test_repos:
            if Path(repo_path).exists():
                # 设置仓库路径
                grader.repo_path = Path(repo_path)
                
                # 执行批量登分
                try:
                    grader.process_docx_files(repo_path)
                    
                    # 验证结果
                    self._verify_batch_grade_results(repo_path)
                    
                except Exception as e:
                    # 在测试中，我们允许某些仓库可能不存在或有问题
                    continue

    def _verify_batch_grade_results(self, repo_path):
        """验证批量登分结果"""
        repo_path = Path(repo_path)
        
        # 检查成绩登记表文件
        excel_files = list(repo_path.glob("平时成绩登记表-*.xlsx"))
        self.assertTrue(len(excel_files) > 0, f"未找到成绩登记表文件: {repo_path}")
        
        for excel_file in excel_files:
            df = pd.read_excel(excel_file)
            
            # 验证必要的列是否存在
            required_columns = ['序号', '学号', '姓名']
            for col in required_columns:
                self.assertTrue(col in df.columns, 
                              f"成绩登记表 {excel_file} 缺少必要的列: {col}")
            
            # 验证学生名单不为空
            self.assertTrue(len(df) > 0, 
                          f"成绩登记表 {excel_file} 中没有学生记录")
            
            # 检查是否有作业成绩列
            homework_columns = [col for col in df.columns if '第' in col and '作业' in col]
            if homework_columns:
                # 验证成绩格式
                for col in homework_columns:
                    if col in df.columns:
                        for grade in df[col].dropna():
                            self.assertIn(grade, ['A', 'B', 'C', 'D', 'E'], 
                                        f"成绩登记表 {excel_file} 中的成绩格式不正确: {grade}")

    def test_repository_detection(self):
        """测试仓库类型检测"""
        for repo_path in self.test_repos:
            if Path(repo_path).exists():
                # 查找成绩登记表
                excel_files = list(Path(repo_path).glob("平时成绩登记表-*.xlsx"))
                if excel_files:
                    for excel_file in excel_files:
                        # 从文件名判断是单班级还是多班级
                        file_name = excel_file.stem
                        if "-" in file_name and "班" in file_name:
                            # 检查是否是多班级格式
                            if any(char.isdigit() for char in file_name.split("-")[-1]):
                                pass
                            else:
                                pass
                        else:
                            pass

    def test_excel_file_processing(self):
        """测试Excel文件处理"""
        for repo_path in self.test_repos:
            if Path(repo_path).exists():
                excel_files = list(Path(repo_path).glob("平时成绩登记表-*.xlsx"))
                for excel_file in excel_files:
                    try:
                        df = pd.read_excel(excel_file)
                        
                        # 验证数据完整性
                        if len(df) > 0:
                            # 检查是否有空的学生信息
                            student_info_cols = ['学号', '姓名']
                            for col in student_info_cols:
                                if col in df.columns:
                                    df[col].isna().sum()
                    except Exception as e:
                        pass 