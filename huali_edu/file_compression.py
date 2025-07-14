import os
from pathlib import Path
import zipfile
import shutil
from typing import List, Union


class FileCompression:
    """文件压缩工具类"""

    MAX_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self, output_dir: Union[str, Path] = None):
        """
        初始化压缩工具类

        Args:
            output_dir: 输出目录路径，如果不指定则使用当前目录下的 compressed_files 目录
        """
        if output_dir is None:
            output_dir = Path.cwd() / "compressed_files"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _clear_output_dir(self):
        """清除输出目录下的所有压缩文件"""
        for file in self.output_dir.glob("*.zip"):
            try:
                file.unlink()
                print(f"已删除旧文件: {file}")
            except Exception as e:
                print(f"删除文件失败 {file}: {e}")

    def compress_directory(
        self, source_dir: Union[str, Path], output_name: str = None
    ) -> Path:
        """
        压缩整个目录，如果超过大小限制会自动分割

        Args:
            source_dir: 源目录路径
            output_name: 输出文件名（不含扩展名），如果不指定则使用目录名

        Returns:
            输出文件路径
        """
        source_dir = Path(source_dir)
        if output_name is None:
            output_name = source_dir.name

        output_path = self.output_dir / f"{output_name}.zip"

        # 清除输出目录下的所有压缩文件
        self._clear_output_dir()

        # 获取目录总大小
        total_size = self._get_directory_size(source_dir)

        if total_size <= self.MAX_SIZE:
            # 如果总大小不超过限制，直接压缩
            self._compress_to_zip(source_dir, output_path)
        else:
            # 如果超过限制，分割压缩
            self._split_compress(source_dir, output_path)

        return output_path

    def compress_files(self, files: List[Union[str, Path]], output_name: str) -> Path:
        """
        压缩指定的文件列表

        Args:
            files: 要压缩的文件列表
            output_name: 输出文件名（不含扩展名）

        Returns:
            输出文件路径
        """
        output_path = self.output_dir / f"{output_name}.zip"

        # 清除输出目录下的所有压缩文件
        self._clear_output_dir()

        # 计算总大小
        total_size = sum(Path(f).stat().st_size for f in files)

        if total_size <= self.MAX_SIZE:
            # 如果总大小不超过限制，直接压缩
            self._compress_to_zip(files, output_path)
        else:
            # 如果超过限制，分割压缩
            self._split_compress_files(files, output_path)

        return output_path

    def _get_directory_size(self, directory: Path) -> int:
        """计算目录的总大小"""
        total_size = 0
        # 只计算子目录中的文件大小
        for path in directory.iterdir():
            if path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
        return total_size

    def _compress_to_zip(
        self, source: Union[Path, List[Path]], output_path: Path
    ) -> None:
        """压缩到单个zip文件"""
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            if isinstance(source, list):
                for file in source:
                    if file.is_file():
                        zipf.write(file, file.name)
                    elif file.is_dir():
                        for root, _, files in os.walk(file):
                            for f in files:
                                file_path = Path(root) / f
                                arcname = file_path.relative_to(file.parent)
                                zipf.write(file_path, arcname)
            else:
                # 只压缩子目录中的内容
                for item in source.iterdir():
                    if item.is_dir():
                        for root, _, files in os.walk(item):
                            for f in files:
                                file_path = Path(root) / f
                                arcname = file_path.relative_to(source)
                                zipf.write(file_path, arcname)

    def _split_compress(self, source_dir: Path, output_path: Path) -> None:
        """分割压缩目录"""
        output_dir = output_path.parent
        part_num = 1

        current_zip = None
        current_size = 0

        # 收集所有子目录中的文件
        all_files = []
        for item in source_dir.iterdir():
            if item.is_dir():
                for root, _, files in os.walk(item):
                    for f in files:
                        file_path = Path(root) / f
                        all_files.append((file_path, file_path.relative_to(source_dir)))

        # 按文件大小排序
        all_files.sort(key=lambda x: x[0].stat().st_size, reverse=True)

        for file_path, arcname in all_files:
            file_size = file_path.stat().st_size

            # 如果当前文件大小超过限制，需要分片处理
            if file_size > self.MAX_SIZE:
                # 计算需要多少个分片
                chunk_size = self.MAX_SIZE // 2  # 使用一半的最大大小作为分片大小
                num_chunks = (file_size + chunk_size - 1) // chunk_size

                # 分片处理大文件
                with open(file_path, "rb") as f:
                    for i in range(num_chunks):
                        # 创建新的压缩包
                        if current_zip is not None:
                            current_zip.close()
                        current_zip = zipfile.ZipFile(
                            output_dir / f"{output_path.stem}_part{part_num}.zip",
                            "w",
                            zipfile.ZIP_DEFLATED,
                        )
                        current_size = 0
                        part_num += 1

                        # 读取当前分片
                        chunk = f.read(chunk_size)

                        # 创建临时文件存储分片
                        temp_file = output_dir / f"temp_chunk_{i}.tmp"
                        try:
                            temp_file.write_bytes(chunk)

                            # 将分片添加到压缩包
                            chunk_arcname = f"{arcname}.part{i+1}"
                            current_zip.write(temp_file, chunk_arcname)
                        finally:
                            # 确保临时文件被删除
                            if temp_file.exists():
                                temp_file.unlink()

                        current_size += len(chunk)
                continue

            # 如果当前压缩包加上这个文件会超过限制，创建新的压缩包
            if current_zip is None or current_size + file_size > self.MAX_SIZE:
                if current_zip is not None:
                    current_zip.close()
                current_zip = zipfile.ZipFile(
                    output_dir / f"{output_path.stem}_part{part_num}.zip",
                    "w",
                    zipfile.ZIP_DEFLATED,
                )
                current_size = 0
                part_num += 1

            # 添加文件到当前压缩包
            current_zip.write(file_path, str(arcname))
            current_size += file_size

        if current_zip is not None:
            current_zip.close()

    def _split_compress_files(self, files: List[Path], output_path: Path) -> None:
        """分割压缩文件列表"""
        output_dir = output_path.parent
        part_num = 1

        current_zip = None
        current_size = 0

        # 按文件大小排序
        files = [Path(f) for f in files]
        files.sort(key=lambda x: x.stat().st_size, reverse=True)

        for file in files:
            file_size = file.stat().st_size

            # 如果当前文件大小超过限制，需要单独处理
            if file_size > self.MAX_SIZE:
                raise ValueError(f"文件 {file} 大小超过限制")

            # 如果当前压缩包加上这个文件会超过限制，创建新的压缩包
            if current_zip is None or current_size + file_size > self.MAX_SIZE:
                if current_zip is not None:
                    current_zip.close()
                current_zip = zipfile.ZipFile(
                    output_dir / f"{output_path.stem}_part{part_num}.zip",
                    "w",
                    zipfile.ZIP_DEFLATED,
                )
                current_size = 0
                part_num += 1

            # 添加文件到当前压缩包
            current_zip.write(file, file.name)
            current_size += file_size

        if current_zip is not None:
            current_zip.close()
