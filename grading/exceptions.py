"""
学期管理相关异常类

定义学期自动创建和管理过程中可能出现的各种异常。
"""

import logging

logger = logging.getLogger(__name__)


class SemesterError(Exception):
    """学期相关异常基类"""

    def __init__(self, message, error_code=None, details=None):
        """初始化异常

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 详细信息字典
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

        # 记录异常日志
        logger.error(
            f"SemesterError: {message}", extra={"error_code": error_code, "details": details}
        )

    def to_dict(self):
        """转换为字典格式"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class SemesterCreationError(SemesterError):
    """学期创建异常"""

    def __init__(self, message, semester_name=None, **kwargs):
        """初始化学期创建异常

        Args:
            message: 错误消息
            semester_name: 相关学期名称
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if semester_name:
            details["semester_name"] = semester_name

        super().__init__(message, **kwargs)


class DuplicateSemesterError(SemesterCreationError):
    """重复学期异常"""

    def __init__(self, message=None, semester_name=None, start_date=None, end_date=None, **kwargs):
        """初始化重复学期异常

        Args:
            message: 错误消息
            semester_name: 学期名称
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数
        """
        if not message:
            if semester_name:
                message = f"学期 '{semester_name}' 已存在"
            elif start_date and end_date:
                message = f"时间段 {start_date} - {end_date} 的学期已存在"
            else:
                message = "学期已存在"

        details = kwargs.get("details", {})
        if start_date:
            details["start_date"] = str(start_date)
        if end_date:
            details["end_date"] = str(end_date)

        kwargs["details"] = details
        kwargs["error_code"] = "DUPLICATE_SEMESTER"

        super().__init__(message, semester_name=semester_name, **kwargs)


class InvalidDateRangeError(SemesterCreationError):
    """无效日期范围异常"""

    def __init__(self, message=None, start_date=None, end_date=None, **kwargs):
        """初始化无效日期范围异常

        Args:
            message: 错误消息
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数
        """
        if not message:
            if start_date and end_date:
                message = f"无效的日期范围: {start_date} - {end_date}"
            else:
                message = "无效的日期范围"

        details = kwargs.get("details", {})
        if start_date:
            details["start_date"] = str(start_date)
        if end_date:
            details["end_date"] = str(end_date)

        kwargs["details"] = details
        kwargs["error_code"] = "INVALID_DATE_RANGE"

        super().__init__(message, **kwargs)


class TemplateNotFoundError(SemesterCreationError):
    """模板未找到异常"""

    def __init__(self, message=None, season=None, template_type=None, **kwargs):
        """初始化模板未找到异常

        Args:
            message: 错误消息
            season: 季节
            template_type: 模板类型
            **kwargs: 其他参数
        """
        if not message:
            if season:
                message = f"未找到 '{season}' 季节的学期模板"
            else:
                message = "未找到学期模板"

        details = kwargs.get("details", {})
        if season:
            details["season"] = season
        if template_type:
            details["template_type"] = template_type

        kwargs["details"] = details
        kwargs["error_code"] = "TEMPLATE_NOT_FOUND"

        super().__init__(message, **kwargs)


class SemesterDetectionError(SemesterError):
    """学期检测异常"""

    def __init__(self, message, current_date=None, **kwargs):
        """初始化学期检测异常

        Args:
            message: 错误消息
            current_date: 当前日期
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if current_date:
            details["current_date"] = str(current_date)

        kwargs["details"] = details
        kwargs["error_code"] = "SEMESTER_DETECTION_ERROR"

        super().__init__(message, **kwargs)


class SemesterConfigurationError(SemesterError):
    """学期配置异常"""

    def __init__(self, message, config_key=None, config_value=None, **kwargs):
        """初始化学期配置异常

        Args:
            message: 错误消息
            config_key: 配置键
            config_value: 配置值
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)

        kwargs["details"] = details
        kwargs["error_code"] = "SEMESTER_CONFIGURATION_ERROR"

        super().__init__(message, **kwargs)


class SemesterValidationError(SemesterError):
    """学期验证异常"""

    def __init__(self, message, field_name=None, field_value=None, **kwargs):
        """初始化学期验证异常

        Args:
            message: 错误消息
            field_name: 字段名
            field_value: 字段值
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = str(field_value)

        kwargs["details"] = details
        kwargs["error_code"] = "SEMESTER_VALIDATION_ERROR"

        super().__init__(message, **kwargs)


class SemesterOperationError(SemesterError):
    """学期操作异常"""

    def __init__(self, message, operation=None, semester_id=None, **kwargs):
        """初始化学期操作异常

        Args:
            message: 错误消息
            operation: 操作类型
            semester_id: 学期ID
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if operation:
            details["operation"] = operation
        if semester_id:
            details["semester_id"] = str(semester_id)

        kwargs["details"] = details
        kwargs["error_code"] = "SEMESTER_OPERATION_ERROR"

        super().__init__(message, **kwargs)


# 异常处理装饰器
def handle_semester_exceptions(default_return=None, log_level=logging.ERROR):
    """学期异常处理装饰器

    Args:
        default_return: 异常时的默认返回值
        log_level: 日志级别
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SemesterError as e:
                logger.log(
                    log_level, f"学期操作异常 in {func.__name__}: {e.message}", extra=e.details
                )
                if default_return is not None:
                    return default_return
                raise
            except Exception as e:
                logger.error(f"未预期异常 in {func.__name__}: {str(e)}")
                # 将未知异常包装为SemesterError
                raise SemesterError(
                    f"操作失败: {str(e)}",
                    error_code="UNKNOWN_ERROR",
                    details={"function": func.__name__, "original_error": str(e)},
                ) from e

        return wrapper

    return decorator


# 异常处理上下文管理器
class SemesterErrorContext:
    """学期异常处理上下文管理器"""

    def __init__(self, operation_name, suppress_errors=False):
        """初始化上下文管理器

        Args:
            operation_name: 操作名称
            suppress_errors: 是否抑制错误
        """
        self.operation_name = operation_name
        self.suppress_errors = suppress_errors
        self.errors = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if issubclass(exc_type, SemesterError):
                self.errors.append(exc_val)
                logger.error(f"学期操作 '{self.operation_name}' 失败: {exc_val.message}")
            else:
                error = SemesterError(
                    f"操作 '{self.operation_name}' 发生未预期错误: {str(exc_val)}",
                    error_code="UNKNOWN_ERROR",
                    details={"operation": self.operation_name},
                )
                self.errors.append(error)
                logger.error(f"操作 '{self.operation_name}' 发生未预期错误: {str(exc_val)}")

            return self.suppress_errors
        return False

    def has_errors(self):
        """检查是否有错误"""
        return len(self.errors) > 0

    def get_errors(self):
        """获取错误列表"""
        return self.errors.copy()

    def get_error_summary(self):
        """获取错误摘要"""
        if not self.errors:
            return "无错误"

        return f"操作 '{self.operation_name}' 发生 {len(self.errors)} 个错误: " + "; ".join(
            [error.message for error in self.errors]
        )


# 批量操作异常处理
class BatchOperationResult:
    """批量操作结果"""

    def __init__(self, operation_name):
        """初始化批量操作结果

        Args:
            operation_name: 操作名称
        """
        self.operation_name = operation_name
        self.successes = []
        self.errors = []
        self.total_count = 0

    def add_success(self, item, result=None):
        """添加成功项"""
        self.successes.append({"item": item, "result": result})

    def add_error(self, item, error):
        """添加错误项"""
        self.errors.append({"item": item, "error": error})

    def set_total_count(self, count):
        """设置总数"""
        self.total_count = count

    def get_success_count(self):
        """获取成功数量"""
        return len(self.successes)

    def get_error_count(self):
        """获取错误数量"""
        return len(self.errors)

    def get_success_rate(self):
        """获取成功率"""
        if self.total_count == 0:
            return 0.0
        return self.get_success_count() / self.total_count

    def is_success(self):
        """检查是否全部成功"""
        return self.get_error_count() == 0

    def is_partial_success(self):
        """检查是否部分成功"""
        return self.get_success_count() > 0 and self.get_error_count() > 0

    def get_summary(self):
        """获取操作摘要"""
        return {
            "operation": self.operation_name,
            "total_count": self.total_count,
            "success_count": self.get_success_count(),
            "error_count": self.get_error_count(),
            "success_rate": self.get_success_rate(),
            "is_success": self.is_success(),
            "is_partial_success": self.is_partial_success(),
        }
