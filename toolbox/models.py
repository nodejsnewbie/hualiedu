from django.contrib.auth.models import User
from django.db import models


class FileConversionTask(models.Model):
    """文件转换任务模型"""

    TASK_STATUS_CHOICES = [
        ("pending", "等待中"),
        ("processing", "处理中"),
        ("completed", "已完成"),
        ("failed", "失败"),
    ]

    CONVERSION_TYPE_CHOICES = [
        ("ppt_to_pdf", "PPT转PDF"),
        ("doc_to_pdf", "DOC转PDF"),
        ("xls_to_pdf", "XLS转PDF"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    task_type = models.CharField(
        max_length=20, choices=CONVERSION_TYPE_CHOICES, verbose_name="转换类型"
    )
    source_directory = models.CharField(max_length=500, verbose_name="源目录")
    output_directory = models.CharField(max_length=500, verbose_name="输出目录")
    status = models.CharField(
        max_length=20, choices=TASK_STATUS_CHOICES, default="pending", verbose_name="任务状态"
    )
    total_files = models.IntegerField(default=0, verbose_name="总文件数")
    processed_files = models.IntegerField(default=0, verbose_name="已处理文件数")
    success_files = models.IntegerField(default=0, verbose_name="成功文件数")
    failed_files = models.IntegerField(default=0, verbose_name="失败文件数")
    error_message = models.TextField(blank=True, null=True, verbose_name="错误信息")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "文件转换任务"
        verbose_name_plural = "文件转换任务"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.get_task_type_display()} - {self.status}"

    @property
    def progress_percentage(self):
        """计算进度百分比"""
        if self.total_files == 0:
            return 0
        return int((self.processed_files / self.total_files) * 100)


class ConversionLog(models.Model):
    """转换日志模型"""

    task = models.ForeignKey(FileConversionTask, on_delete=models.CASCADE, verbose_name="任务")
    file_name = models.CharField(max_length=255, verbose_name="文件名")
    status = models.CharField(
        max_length=20, choices=FileConversionTask.TASK_STATUS_CHOICES, verbose_name="状态"
    )
    error_message = models.TextField(blank=True, null=True, verbose_name="错误信息")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "转换日志"
        verbose_name_plural = "转换日志"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task} - {self.file_name} - {self.status}"
