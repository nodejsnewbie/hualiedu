# 学期状态显示功能

## 功能概述

系统现在能够根据当前时间智能识别并显示学期状态，包括：
- 当前学期是哪个
- 是否在寒暑假期间
- 下一个学期是什么
- 学期进度和时间线

## 核心功能

### 1. 智能学期识别
- **当前学期检测**：自动识别当前日期对应的学期
- **假期状态判断**：区分寒假、暑假、学期间隙
- **学期进度计算**：显示学期进度百分比和阶段（初期、中期、末期等）

### 2. 综合状态信息
- **状态摘要**：一句话描述当前状态
- **时间信息**：剩余天数、已过天数、倒计时等
- **下一学期预测**：自动识别即将到来的学期
- **历史学期追踪**：显示上一个学期信息

### 3. 可视化展示
- **状态概览卡片**：美观的状态展示界面
- **学期时间线**：直观的时间轴显示
- **进度指示器**：学期进度可视化
- **假期标识**：不同假期类型的图标和颜色

## 技术实现

### 核心服务类

#### SemesterStatusService
```python
# 主要方法
get_comprehensive_status()  # 获取综合状态
get_dashboard_info()       # 获取仪表板信息
get_simple_status()        # 获取简单状态文本
```

#### 状态分析功能
- 学期状态分析（在学期中/假期中）
- 假期类型识别（寒假/暑假/学期间隙）
- 时间计算（进度/剩余时间/倒计时）
- 学期关系分析（当前/过去/未来）

### 前端集成

#### 模板标签
```django
{% load semester_tags %}
{% semester_status_widget %}      # 状态小部件
{% semester_timeline_widget %}    # 时间线小部件
{% get_semester_status %}         # 获取状态数据
{% get_dashboard_info %}          # 获取仪表板数据
```

#### API接口
- `/grading/semester-status-api/` - 学期状态API
- 支持AJAX实时更新
- JSON格式数据返回

### 页面集成

#### 学期管理页面
- 顶部状态概览区域
- 实时状态更新
- 自动刷新功能

#### 首页仪表板
- 学期状态小部件
- 学期时间线展示
- 课程信息整合

## 使用示例

### 获取当前状态
```python
from grading.services.semester_status import semester_status_service

# 获取综合状态
status = semester_status_service.get_comprehensive_status()
print(status['summary']['text'])  # "当前在2024年春季学期中（前期）"

# 获取仪表板信息
dashboard = semester_status_service.get_dashboard_info()
print(dashboard['current_status'])  # 当前状态文本
```

### 模板中使用
```django
<!-- 显示状态小部件 -->
{% semester_status_widget %}

<!-- 获取状态信息 -->
{% get_semester_status as status %}
<p>{{ status.summary.text }}</p>

<!-- 显示时间线 -->
{% semester_timeline_widget %}
```

### 管理命令
```bash
# 查看学期状态
python manage.py semester_management stats

# 同步学期状态
python manage.py semester_management sync

# 验证学期数据
python manage.py semester_management validate
```

## 状态类型说明

### 学期状态
- **in_semester**: 在学期中
- **not_in_semester**: 不在学期中（假期）

### 假期类型
- **winter**: 寒假（1-2月）
- **summer**: 暑假（7-8月）
- **intersemester**: 学期间隙
- **none**: 非假期（在学期中）

### 学期阶段
- **beginning**: 学期初（0-20%）
- **early**: 前期（20-40%）
- **middle**: 中期（40-60%）
- **late**: 后期（60-80%）
- **ending**: 学期末（80-100%）

## 测试验证

### 功能测试
```bash
# 测试学期状态功能
make test-status

# 运行完整测试套件
make test-all
```

### 测试场景
- ✅ 当前学期识别
- ✅ 假期状态判断
- ✅ 学期进度计算
- ✅ 时间线生成
- ✅ 边界日期处理
- ✅ 无学期数据处理

## 配置选项

### Django设置
```python
# settings.py
SEMESTER_AUTO_CREATION = {
    'AUTO_DETECTION_ENABLED': True,
    'CACHE_TIMEOUT_SECONDS': 300,
    'NOTIFICATION_ENABLED': True,
}
```

### 缓存配置
- 状态信息缓存5分钟
- 自动刷新机制
- 支持手动刷新

## 性能优化

### 缓存策略
- 配置信息缓存
- 状态计算结果缓存
- 数据库查询优化

### 前端优化
- AJAX异步更新
- 自动刷新（5分钟间隔）
- 响应式设计

## 扩展功能

### 未来增强
- [ ] 学期事件提醒
- [ ] 自定义状态规则
- [ ] 多校区支持
- [ ] 国际化支持
- [ ] 移动端优化

### API扩展
- [ ] RESTful API
- [ ] WebSocket实时推送
- [ ] 第三方系统集成

## 故障排除

### 常见问题
1. **状态显示不正确**
   - 检查学期数据完整性
   - 运行 `make sync` 同步状态

2. **缓存问题**
   - 清除Django缓存
   - 重启应用服务

3. **时间计算错误**
   - 验证系统时间设置
   - 检查时区配置

### 调试命令
```bash
# 检查学期状态
python manage.py semester_management stats

# 验证数据
python manage.py semester_management validate --fix

# 查看日志
tail -f logs/semester.log
```

## 总结

学期状态显示功能为系统提供了智能的时间感知能力，用户可以：
- 一目了然地了解当前学期状态
- 清楚知道假期安排和下学期时间
- 通过可视化界面掌握学期进度
- 享受自动化的状态更新体验

这个功能大大提升了用户体验，让学期管理更加智能和人性化。
