import unittest
import os
import logging
from pathlib import Path
import pandas as pd
from huali_edu.grade_registration import GradeRegistration

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiClassTest(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        logger.info("="*50)
        logger.info("开始测试")
        
        # 使用真实的仓库路径
        self.repo_path = Path("/Users/linyuan/jobs/23java-mode-homework")
        
        # 验证仓库路径是否存在
        if not self.repo_path.exists():
            raise FileNotFoundError(f"仓库路径不存在: {self.repo_path}")
        
        logger.info(f"多班级仓库路径: {self.repo_path}")
        logger.info("="*50)
    
    def test_multi_class_processing(self):
        """测试多班级仓库的处理"""
        # 创建GradeRegistration实例
        grader = GradeRegistration()
        
        # 处理docx文件
        grader.process_docx_files(str(self.repo_path))
        
        # 验证成绩是否正确写入
        excel_files = list(self.repo_path.glob("平时成绩登记表-*.xlsx"))
        self.assertTrue(len(excel_files) > 0, "未找到成绩登记表文件")
        
        for excel_file in excel_files:
            logger.info(f"验证成绩登记表: {excel_file}")
            df = pd.read_excel(excel_file)
            
            # 验证成绩列是否存在
            self.assertTrue('第1次作业' in df.columns, f"成绩登记表 {excel_file} 缺少第1次作业列")
            self.assertTrue('第2次作业' in df.columns, f"成绩登记表 {excel_file} 缺少第2次作业列")
            
            # 验证成绩格式是否正确
            for col in ['第1次作业', '第2次作业']:
                if col in df.columns:
                    for grade in df[col].dropna():
                        self.assertIn(grade, ['A', 'B', 'C', 'D', 'E'], 
                                    f"成绩登记表 {excel_file} 中的成绩格式不正确: {grade}")
    
    def test_class_directories(self):
        """测试班级目录结构"""
        # 验证班级目录是否存在
        class_dirs = [d for d in self.repo_path.iterdir() if d.is_dir() and d.name.startswith('23计算机')]
        self.assertTrue(len(class_dirs) > 0, "未找到班级目录")
        
        # 验证每个班级目录下是否有作业目录
        for class_dir in class_dirs:
            homework_dirs = [d for d in class_dir.iterdir() if d.is_dir() and 
                           ('作业' in d.name or '第' in d.name)]
            self.assertTrue(len(homework_dirs) > 0, 
                          f"班级目录 {class_dir} 下未找到作业目录")
    
    def test_excel_files(self):
        """测试成绩登记表文件"""
        # 验证成绩登记表文件是否存在
        excel_files = list(self.repo_path.glob("平时成绩登记表-*.xlsx"))
        self.assertTrue(len(excel_files) > 0, "未找到成绩登记表文件")
        
        # 验证每个成绩登记表文件的内容
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

if __name__ == '__main__':
    unittest.main() 