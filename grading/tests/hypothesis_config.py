"""
Hypothesis 测试配置

统一配置 Hypothesis 属性测试，防止在项目根目录创建随机测试目录。

最佳实践：
1. 将 Hypothesis 数据库存储在系统临时目录
2. 配置合理的测试示例数量
3. 禁用过于严格的健康检查（Django 测试可能较慢）
4. 设置合理的超时时间
"""

import os
import tempfile

import hypothesis

# 配置 Hypothesis 数据库位置
# 使用系统临时目录，避免在项目根目录创建文件
HYPOTHESIS_DB_DIR = os.path.join(tempfile.gettempdir(), '.hypothesis_db')
os.makedirs(HYPOTHESIS_DB_DIR, exist_ok=True)

# CI/CD 环境配置
hypothesis.settings.register_profile(
    "ci",
    max_examples=100,  # CI 环境使用较多示例以确保覆盖率
    database_file=os.path.join(HYPOTHESIS_DB_DIR, 'examples.db'),
    suppress_health_check=[
        hypothesis.HealthCheck.too_slow,
        hypothesis.HealthCheck.data_too_large,
    ],
    deadline=None,  # Django 测试可能较慢，禁用超时
    print_blob=False,  # 不打印大量调试信息
)

# 开发环境配置
hypothesis.settings.register_profile(
    "dev",
    max_examples=10,  # 开发时使用更少示例以加快速度
    database_file=os.path.join(HYPOTHESIS_DB_DIR, 'examples.db'),
    suppress_health_check=[
        hypothesis.HealthCheck.too_slow,
        hypothesis.HealthCheck.data_too_large,
    ],
    deadline=None,
    print_blob=False,
)

# 调试环境配置
hypothesis.settings.register_profile(
    "debug",
    max_examples=5,  # 调试时使用最少示例
    database_file=os.path.join(HYPOTHESIS_DB_DIR, 'examples.db'),
    suppress_health_check=[
        hypothesis.HealthCheck.too_slow,
        hypothesis.HealthCheck.data_too_large,
    ],
    deadline=None,
    print_blob=True,  # 调试时打印详细信息
    verbosity=hypothesis.Verbosity.verbose,
)

# 默认使用 CI profile
# 可以通过环境变量 HYPOTHESIS_PROFILE 覆盖
profile = os.environ.get('HYPOTHESIS_PROFILE', 'ci')
hypothesis.settings.load_profile(profile)
