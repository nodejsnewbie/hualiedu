import os
from pathlib import Path
import pandas as pd
import re
from docx import Document
from datetime import datetime
import openpyxl

class GradeRegistration:
    def __init__(self):
        self.homework_pattern = re.compile(r'第(\d+)次作业')
        self.grade_pattern = re.compile(r'老师评分：\s*([A-E])')
        # 默认Excel文件路径
        self.default_excel_path = Path("/Users/linyuan/jobs/22g-class-java-homework/平时成绩登记表-22计算机G1班.xlsx")
        # 设置默认仓库路径
        self.repo_path = Path(".")
        # 添加缓存字典，用于存储每个班级的学生名单
        self._student_cache = {}
    
    def find_excel_file(self, class_name: str) -> Path:
        """查找Excel文件
        
        Args:
            class_name: 班级名称
            
        Returns:
            Excel文件路径
            
        Raises:
            FileNotFoundError: 如果找不到对应的Excel文件
        """
        # 构建Excel文件名
        excel_name = f"平时成绩登记表-{class_name}.xlsx"
        excel_path = self.repo_path / excel_name
        
        # 如果文件不存在，抛出异常
        if not excel_path.exists():
            raise FileNotFoundError(f"找不到班级 {class_name} 的成绩登记表")
        
        return excel_path
    
    def get_homework_number_from_path(self, path: Path) -> int | None:
        """从文件路径中提取作业次数
        
        Args:
            path: 文件路径
            
        Returns:
            int | None: 作业次数（1-16），如果找不到则返回None
        """
        # 中文数字到阿拉伯数字的映射
        chinese_nums = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
        
        path_str = str(path)
        
        # 处理中文数字的情况
        for parent in [path, path.parent]:
            parent_str = str(parent)
            # 处理"十"开头的数字 (10-16)
            match = re.search(r'第十([一二三四五六])?次作业', parent_str)
            if match:
                if not match.group(1):  # 只有"十"
                    return 10
                return 10 + chinese_nums[match.group(1)]
                
            # 处理单个中文数字 (1-9)
            match = re.search(r'第([一二三四五六七八九])次作业', parent_str)
            if match:
                return chinese_nums[match.group(1)]
        
        # 处理阿拉伯数字的情况
        match = self.homework_pattern.search(path_str)
        if match:
            homework_num = int(match.group(1))
            if 1 <= homework_num <= 16:
                return homework_num
        
        return None
    
    def _load_student_list(self, excel_path: Path) -> dict:
        """加载Excel文件中的学生名单
        
        Args:
            excel_path: Excel文件路径
            
        Returns:
            dict: 学生行号映射，key为学生姓名，value为行号
        """
        student_rows = {}
        with open(excel_path, 'rb') as f:
            wb = openpyxl.load_workbook(f)
            ws = wb.active
            
            # 查找学生行
            for row_idx in range(1, ws.max_row + 1):
                cell_value = str(ws.cell(row=row_idx, column=3).value).strip()  # 第3列是姓名列
                if cell_value and cell_value != "姓名":  # 排除表头和空值
                    student_rows[cell_value] = row_idx
                    
        return student_rows
    
    def write_grade_to_excel(self, excel_path: str, student_name: str, homework_number: int, grade: str) -> None:
        """
        将学生成绩写入Excel文件

        Args:
            excel_path: Excel文件路径
            student_name: 学生姓名
            homework_number: 作业次数
            grade: 成绩（A/B/C/D/E）

        Raises:
            FileNotFoundError: 如果找不到对应的Excel文件
            ValueError: 如果作业列索引超出当前列数
        """
        # 读取Excel文件
        with open(excel_path, 'rb') as f:
            wb = openpyxl.load_workbook(f)
            ws = wb.active

            # 缓存机制同前
            if excel_path not in self._student_cache:
                self._student_cache[excel_path] = self._load_student_list(excel_path)
            student_rows = self._student_cache[excel_path]
            if student_name not in student_rows:
                print(f"Warning: Student {student_name} not found in {excel_path}")
                return

            student_row = student_rows[student_name]
            # 第1列是序号，第2列是学号，第3列是姓名，第4列开始是作业成绩
            homework_col_idx = 3 + homework_number
            if homework_col_idx > ws.max_column:
                raise ValueError(f"作业列索引 {homework_col_idx} 超出当前列数 {ws.max_column}")

            ws.cell(row=student_row, column=homework_col_idx, value=grade)
            wb.save(excel_path)
    
    def _extract_class_name(self, path: Path, is_multi_class: bool) -> str:
        """从文件路径中提取班级名称
        
        Args:
            path: 文件路径
            is_multi_class: 是否为多班级仓库
            
        Returns:
            str: 班级名称
            
        Raises:
            ValueError: 如果无法从路径中提取班级名称
        """
        # 如果是多班级仓库，从目录名中提取班级信息
        if is_multi_class:
            # 获取文件所在目录
            current_dir = path.parent
            
            # 检查目录名是否符合班级命名规范（例如：23计算机1班）
            class_pattern = re.compile(r'^\d{2}计算机[12]班$')
            if class_pattern.match(current_dir.name):
                return current_dir.name
                
            # 如果目录名不符合规范，尝试从路径中提取
            class_match = re.search(r'(\d{2}计算机[12]班)', str(path))
            if class_match:
                return class_match.group(1)
                
            # 如果还是找不到，尝试从父目录中查找
            for parent in current_dir.parents:
                if class_pattern.match(parent.name):
                    return parent.name
                    
            raise ValueError(f"Could not determine class name from path: {path}")
            
        # 如果是单班级仓库，使用默认班级名称
        return "22计算机G1班"
    
    def _extract_student_name(self, path: Path) -> str:
        """
        Extract student name from docx filename.
        
        Args:
            path: Path to the docx file
            
        Returns:
            Student name as string
            
        Raises:
            ValueError: If no valid student name is found in the filename
        """
        # Get the filename without extension
        filename = path.stem
        
        # Check if the filename contains Chinese characters
        if not any('\u4e00' <= char <= '\u9fff' for char in filename):
            raise ValueError(f"No Chinese characters found in filename: {filename}")
        
        # Extract the student name (2-4 Chinese characters)
        # First try to find a sequence of 2-4 Chinese characters
        matches = re.findall(r'[\u4e00-\u9fff]{2,4}', filename)
        if matches:
            # If multiple matches, prefer the one that's not part of a class name
            for match in matches:
                if not any(class_name in match for class_name in ['计算机', '软件', '网络']):
                    return match
            # If all matches are part of class names, return the first one
            return matches[0]
        
        # If no match found, try to find any sequence of Chinese characters
        matches = re.findall(r'[\u4e00-\u9fff]+', filename)
        if matches:
            # Return the first sequence that's not a class name
            for match in matches:
                if not any(class_name in match for class_name in ['计算机', '软件', '网络']):
                    return match
            # If all matches are part of class names, return the first one
            return matches[0]
        
        raise ValueError(f"Could not extract valid student name from filename: {filename}")
    
    def _extract_grade_from_docx(self, path: Path) -> str:
        """
        Extract grade from docx file content.
        
        Args:
            path: Path to the docx file
            
        Returns:
            Grade as string (A, B, C, D, or E)
            
        Raises:
            ValueError: If an invalid grade is found
        """
        try:
            doc = Document(path)
            found_grade_pattern = False
            
            for paragraph in doc.paragraphs:
                if "老师评分：" in paragraph.text:
                    found_grade_pattern = True
                    grade_text = paragraph.text.split("老师评分：")[-1].strip()
                    if grade_text:
                        if grade_text in ['A', 'B', 'C', 'D', 'E']:
                            return grade_text
                        else:
                            raise ValueError(f"Invalid grade '{grade_text}' in file: {path}")
            
            # 如果没有找到成绩，返回默认成绩B
            return "B"
            
        except Exception as e:
            # 如果处理文件时出错，返回默认成绩B
            print(f"Error reading file {path}: {str(e)}")
            return "B"
    
    def process_docx_files(self, repository_path: str) -> None:
        """
        处理仓库中的所有docx文件，提取成绩并写入Excel

        Args:
            repository_path: 仓库路径
        """
        # 搜索成绩登记表文件
        excel_files = list(Path(repository_path).glob("平时成绩登记表-*.xlsx"))
        if not excel_files:
            raise FileNotFoundError(f"在 {repository_path} 中未找到成绩登记表文件")

        # 处理每个成绩登记表文件
        for excel_file in excel_files:
            # 从文件名中提取专业和年级信息
            class_name = excel_file.stem.split("-")[1]  # 例如：23计算机1-2班 或 22计算机G1班
            major = class_name.split("班")[0].split("计算机")[1]  # 例如：1-2 或 G1
            year = class_name.split("计算机")[0]  # 例如：23

            # 处理班级范围
            if "-" in major:  # 处理多班级情况
                class_range = major.split("-")
                start_class = int(class_range[0])
                end_class = int(class_range[1])
                class_numbers = list(range(start_class, end_class + 1))
            else:  # 处理单班级情况
                class_numbers = [major]  # 直接使用班级标识，如 "G1"

            # 处理每个班级
            for class_number in class_numbers:
                class_dir = Path(repository_path) / f"{year}计算机{class_number}班"
                if not class_dir.exists():
                    print(f"Warning: 班级目录 {class_dir} 不存在")
                    continue

                # 处理该班级的所有docx文件
                for docx_file in class_dir.glob("*.docx"):
                    try:
                        student_name = self._extract_student_name(docx_file.name)
                        homework_number = self._extract_homework_number(docx_file.name)
                        grade = self._extract_grade_from_docx(docx_file)

                        # 写入成绩
                        self.write_grade_to_excel(
                            excel_path=str(excel_file),
                            student_name=student_name,
                            homework_number=homework_number,
                            grade=grade
                        )
                    except Exception as e:
                        print(f"处理文件 {docx_file} 时出错: {e}")
                        continue

    def _is_multi_class_repo(self, repo_path: Path) -> bool:
        """判断仓库是否为多班级仓库
        
        Args:
            repo_path: 仓库根目录路径
            
        Returns:
            bool: 如果是多班级仓库返回True，否则返回False
        """
        # 检查仓库根目录下是否有包含"班"字的目录
        for item in repo_path.iterdir():
            if item.is_dir() and "班" in item.name:
                return True
        return False 