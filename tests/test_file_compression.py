import unittest
from pathlib import Path
import shutil
import tempfile
import os
import zipfile
from huali_edu.file_compression import FileCompression

class FileCompressionTest(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        self.compression = FileCompression()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # 创建测试目录结构
        self.test_dir = self.temp_dir / "test_data"
        self.test_dir.mkdir()
        
        # 创建输出目录
        self.output_dir = self.temp_dir / "output"
        self.output_dir.mkdir()
        
        # 创建根目录下的文件（这些文件应该被忽略）
        (self.test_dir / "root_file1.txt").write_text("This is a root file 1")
        (self.test_dir / "root_file2.txt").write_text("This is a root file 2")
        
        # 创建子目录1及其文件
        subdir1 = self.test_dir / "subdir1"
        subdir1.mkdir()
        (subdir1 / "file1.txt").write_text("This is a test file 1")
        (subdir1 / "file2.txt").write_text("This is a test file 2")
        
        # 创建子目录2及其文件
        subdir2 = self.test_dir / "subdir2"
        subdir2.mkdir()
        (subdir2 / "file3.txt").write_text("This is a test file 3")
        
        # 创建嵌套子目录及其文件
        nested_dir = subdir2 / "nested"
        nested_dir.mkdir()
        (nested_dir / "file4.txt").write_text("This is a test file 4")
        
    def tearDown(self):
        """清理测试环境"""
        # 打印临时目录内容
        print("\n临时目录内容：")
        for root, dirs, files in os.walk(self.temp_dir):
            level = root.replace(str(self.temp_dir), '').count(os.sep)
            indent = ' ' * 4 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print(f"{subindent}{f}")
        
        # 保留测试目录以便检查
        # shutil.rmtree(self.temp_dir)
        
    def test_compress_directory(self):
        """测试目录压缩功能"""
        # 压缩整个目录
        output_path = self.output_dir / "compressed.zip"
        self.compression.compress_directory(self.test_dir, output_path)
        
        # 验证压缩文件存在
        self.assertTrue(output_path.exists())
        
        # 验证压缩文件大小不超过100MB
        self.assertLessEqual(output_path.stat().st_size, 100 * 1024 * 1024)
        
        # 解压缩并验证内容
        extract_dir = self.output_dir / "extracted"
        extract_dir.mkdir()
        with zipfile.ZipFile(output_path, 'r') as zipf:
            zipf.extractall(extract_dir)
            
        # 验证根目录文件没有被压缩
        self.assertFalse((extract_dir / "root_file1.txt").exists())
        self.assertFalse((extract_dir / "root_file2.txt").exists())
        
        # 验证子目录文件被正确压缩
        self.assertTrue((extract_dir / "subdir1" / "file1.txt").exists())
        self.assertTrue((extract_dir / "subdir1" / "file2.txt").exists())
        self.assertTrue((extract_dir / "subdir2" / "file3.txt").exists())
        self.assertTrue((extract_dir / "subdir2" / "nested" / "file4.txt").exists())
        
    def test_compress_specific_files(self):
        """测试压缩特定文件"""
        # 选择一些特定文件进行压缩
        files_to_compress = [
            self.test_dir / "subdir1" / "file1.txt",
            self.test_dir / "subdir2" / "nested" / "file4.txt"
        ]
        
        output_path = self.output_dir / "specific_files.zip"
        self.compression.compress_files(files_to_compress, output_path)
        
        # 验证压缩文件存在
        self.assertTrue(output_path.exists())
        
        # 验证压缩文件大小不超过100MB
        self.assertLessEqual(output_path.stat().st_size, 100 * 1024 * 1024)
        
        # 解压缩并验证内容
        extract_dir = self.output_dir / "extracted_specific"
        extract_dir.mkdir()
        with zipfile.ZipFile(output_path, 'r') as zipf:
            zipf.extractall(extract_dir)
            
        # 验证文件被正确压缩
        self.assertTrue((extract_dir / "file1.txt").exists())
        self.assertTrue((extract_dir / "file4.txt").exists())
        
    def test_split_large_directory(self):
        """测试大目录分割压缩"""
        # 创建子目录中的大文件
        large_dir = self.test_dir / "large_subdir"
        large_dir.mkdir()
        large_file = large_dir / "large_file.txt"
        with open(large_file, 'wb') as f:
            f.write(os.urandom(150 * 1024 * 1024))  # 150MB
            
        # 在根目录也创建一个大文件（应该被忽略）
        root_large_file = self.test_dir / "root_large_file.txt"
        with open(root_large_file, 'wb') as f:
            f.write(os.urandom(150 * 1024 * 1024))  # 150MB
        
        # 压缩整个目录，如果超过100MB会自动分割
        output_path = self.output_dir / "compressed.zip"
        self.compression.compress_directory(self.test_dir, output_path)
        
        # 验证至少有一个压缩文件存在
        zip_files = list(self.output_dir.glob("*.zip"))
        self.assertGreater(len(zip_files), 0)
        
        # 验证每个压缩文件大小不超过100MB
        for zip_file in zip_files:
            self.assertLessEqual(zip_file.stat().st_size, 100 * 1024 * 1024)
            
        # 打印压缩文件信息
        print("\n压缩文件列表：")
        for zip_file in zip_files:
            print(f"- {zip_file.name}: {zip_file.stat().st_size / 1024 / 1024:.2f}MB") 