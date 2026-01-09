# 自动学期创建功能设计文档

## 概述

本设计文档描述了自动学期创建功能的技术实现方案。该功能将在现有的Django学期管理系统基础上，添加智能的学期自动创建、命名和排序逻辑，确保学期数据的连续性和一致性。

## 架构

### 系统架构图

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   用户界面层     │    │    业务逻辑层     │    │    数据访问层    │
│                │    │                 │    │                │
│ - 学期管理页面   │◄──►│ - 学期管理服务   │◄──►│ - Semester模型  │
│ - 学期列表显示   │    │ - 自动创建服务   │    │ - Course模型    │
│ - 操作按钮      │    │ - 命名规则引擎   │    │ - 数据库操作    │
└─────────────────┘    │ - 时间计算引擎   │    └─────────────────┘
                      │ - 排序算法      │
                      └──────────────────┘
```

### 核心组件

1. **SemesterAutoCreator** - 自动学期创建服务
2. **SemesterNamingEngine** - 学期命名规则引擎
3. **SemesterTimeCalculator** - 学期时间计算引擎
4. **CurrentSemesterDetector** - 当前学期检测器
5. **SemesterSorter** - 学期排序器

## 组件和接口

### 1. SemesterAutoCreator (自动学期创建服务)

```python
class SemesterAutoCreator:
    """自动学期创建服务"""

    def check_and_create_current_semester(self) -> Optional[Semester]:
        """检查并创建当前学期"""

    def find_reference_semester(self, target_date: date) -> Optional[Semester]:
        """查找参考学期（上一年同期）"""

    def create_semester_from_reference(self, reference: Semester) -> Semester:
        """基于参考学期创建新学期"""

    def create_semester_from_template(self, target_date: date) -> Semester:
        """基于模板创建新学期"""
```

### 2. SemesterNamingEngine (学期命名规则引擎)

```python
class SemesterNamingEngine:
    """学期命名规则引擎"""

    def generate_name_from_reference(self, reference_name: str, target_year: int) -> str:
        """基于参考学期名称生成新名称"""

    def generate_default_name(self, target_date: date) -> str:
        """生成默认学期名称"""

    def detect_semester_season(self, start_date: date) -> str:
        """检测学期季节（春季/秋季）"""
```

### 3. SemesterTimeCalculator (学期时间计算引擎)

```python
class SemesterTimeCalculator:
    """学期时间计算引擎"""

    def calculate_dates_from_reference(self, reference: Semester, target_year: int) -> Tuple[date, date]:
        """基于参考学期计算新学期日期"""

    def calculate_dates_from_template(self, target_date: date) -> Tuple[date, date]:
        """基于模板计算学期日期"""

    def get_semester_templates(self) -> Dict[str, Dict]:
        """获取学期模板配置"""
```

### 4. CurrentSemesterDetector (当前学期检测器)

```python
class CurrentSemesterDetector:
    """当前学期检测器"""

    def detect_current_semester(self, current_date: date = None) -> Optional[Semester]:
        """检测当前学期"""

    def should_create_semester(self, current_date: date = None) -> bool:
        """判断是否需要创建学期"""

    def get_expected_semester_period(self, current_date: date) -> Tuple[date, date]:
        """获取预期的学期时间段"""
```

### 5. SemesterSorter (学期排序器)

```python
class SemesterSorter:
    """学期排序器"""

    def sort_semesters_for_display(self, semesters: QuerySet, current_date: date = None) -> List[Semester]:
        """为显示排序学期列表"""

    def identify_current_semester(self, semesters: List[Semester], current_date: date) -> Optional[Semester]:
        """识别当前学期"""
```

## 数据模型

### 现有模型扩展

```python
class Semester(models.Model):
    # 现有字段...

    # 新增字段
    auto_created = models.BooleanField(default=False, help_text="是否为自动创建")
    reference_semester = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, help_text="参考学期")
    season = models.CharField(max_length=10, choices=[('spring', '春季'), ('autumn', '秋季')], null=True, blank=True)

    class Meta:
        # 添加唯一约束，防止重复创建
        constraints = [
            models.UniqueConstraint(
                fields=['start_date', 'end_date'],
                name='unique_semester_period'
            )
        ]

    def get_season(self) -> str:
        """获取学期季节"""

    def is_current_semester(self, current_date: date = None) -> bool:
        """判断是否为当前学期"""

    def get_next_year_dates(self) -> Tuple[date, date]:
        """获取下一年对应的日期"""
```

### 配置模型

```python
class SemesterTemplate(models.Model):
    """学期模板配置"""

    season = models.CharField(max_length=10, choices=[('spring', '春季'), ('autumn', '秋季')])
    start_month = models.IntegerField(help_text="开始月份")
    start_day = models.IntegerField(help_text="开始日期")
    end_month = models.IntegerField(help_text="结束月份")
    end_day = models.IntegerField(help_text="结束日期")
    duration_weeks = models.IntegerField(default=16, help_text="学期周数")
    name_pattern = models.CharField(max_length=50, help_text="命名模式，如'{year}年{season}'")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['season', 'is_active']
```

## 错误处理

### 异常类定义

```python
class SemesterCreationError(Exception):
    """学期创建异常基类"""
    pass

class DuplicateSemesterError(SemesterCreationError):
    """重复学期异常"""
    pass

class InvalidDateRangeError(SemesterCreationError):
    """无效日期范围异常"""
    pass

class TemplateNotFoundError(SemesterCreationError):
    """模板未找到异常"""
    pass
```

### 错误处理策略

1. **重复学期检测**: 在创建前检查是否存在相同时间段的学期
2. **日期验证**: 确保开始日期早于结束日期，学期长度合理
3. **回滚机制**: 创建失败时回滚所有相关操作
4. **日志记录**: 记录所有创建操作和错误信息
5. **优雅降级**: 自动创建失败时不影响现有功能

## 测试策略

### 单元测试

1. **SemesterAutoCreator测试**
   - 测试基于参考学期的创建逻辑
   - 测试基于模板的创建逻辑
   - 测试重复创建的防护机制

2. **SemesterNamingEngine测试**
   - 测试各种命名模式的解析
   - 测试年份更新逻辑
   - 测试默认命名生成

3. **SemesterTimeCalculator测试**
   - 测试日期计算的准确性
   - 测试跨年日期处理
   - 测试异常日期的处理

4. **CurrentSemesterDetector测试**
   - 测试当前学期检测逻辑
   - 测试边界日期处理
   - 测试学期间隙处理

### 集成测试

1. **完整创建流程测试**
   - 测试从检测到创建的完整流程
   - 测试多种场景下的自动创建
   - 测试与现有学期管理功能的集成

2. **并发安全测试**
   - 测试多用户同时访问时的创建逻辑
   - 测试数据库锁定和事务处理

### 性能测试

1. **响应时间测试**: 确保自动创建不影响页面加载速度
2. **数据库查询优化**: 优化学期检测和创建的数据库操作
3. **缓存策略**: 对频繁查询的数据进行缓存

## 实现计划

### 阶段1: 核心服务实现
- 实现SemesterAutoCreator基础功能
- 实现SemesterNamingEngine
- 实现SemesterTimeCalculator
- 添加基础的单元测试

### 阶段2: 检测和排序功能
- 实现CurrentSemesterDetector
- 实现SemesterSorter
- 集成到现有的学期管理视图

### 阶段3: 配置和模板系统
- 实现SemesterTemplate模型
- 添加配置管理界面
- 实现模板基础的创建逻辑

### 阶段4: 错误处理和优化
- 完善异常处理机制
- 添加日志记录
- 性能优化和缓存

### 阶段5: 测试和部署
- 完整的集成测试
- 用户验收测试
- 生产环境部署

## 配置参数

```python
# settings.py 中的配置
SEMESTER_AUTO_CREATION = {
    'ENABLED': True,
    'CHECK_ON_VIEW_ACCESS': True,
    'DEFAULT_TEMPLATES': {
        'spring': {
            'start_month': 3,
            'start_day': 1,
            'end_month': 7,
            'end_day': 31,
            'name_pattern': '{year}年春季'
        },
        'autumn': {
            'start_month': 9,
            'start_day': 1,
            'end_month': 1,  # 次年1月
            'end_day': 31,
            'name_pattern': '{year}年秋季'
        }
    },
    'LOGGING': {
        'ENABLED': True,
        'LEVEL': 'INFO'
    }
}
```

## 安全考虑

1. **权限控制**: 只有管理员可以触发手动创建
2. **数据验证**: 严格验证所有输入数据
3. **事务安全**: 使用数据库事务确保数据一致性
4. **审计日志**: 记录所有自动创建操作
5. **回滚能力**: 提供创建操作的撤销功能

## 监控和日志

1. **创建日志**: 记录每次自动创建的详细信息
2. **错误监控**: 监控创建失败的情况
3. **性能指标**: 监控创建操作的执行时间
4. **使用统计**: 统计自动创建功能的使用情况
