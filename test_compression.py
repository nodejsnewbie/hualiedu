from pathlib import Path
from huali_edu.file_compression import FileCompression

def compress_directory(source_dir: Path, output_dir: Path, name: str):
    """压缩指定目录"""
    print(f"\n开始压缩目录: {source_dir}")
    compression = FileCompression(output_dir)
    output_path = compression.compress_directory(source_dir, name)
    print(f"压缩完成，输出文件：{output_path}")
    
    # 检查输出目录中的文件
    print("\n输出目录中的文件：")
    for file in output_dir.glob(f"{name}*.zip"):
        print(f"- {file.name}: {file.stat().st_size / 1024 / 1024:.2f}MB")

def main():
    # 设置源目录和输出目录
    directories = [
        ("/Users/linyuan/jobs/22g-class-java-homework", "22g-class-java-homework"),
        ("/Users/linyuan/jobs/23java-mode-homework", "23java-mode-homework")
    ]
    
    for source_path, name in directories:
        source_dir = Path(source_path)
        output_dir = source_dir / "compressed_files"
        compress_directory(source_dir, output_dir, name)

if __name__ == "__main__":
    main() 