# 文件架构说明

## 说明

本文件记录当前仓库中手工维护的源码、模板、测试、部署与文档文件职责。  
以下内容不逐项展开：

- `.packages/`、`.tmp/`、`.venv/`
- `__pycache__/`
- `dev-bootstrap.sqlite3`
- `staticfiles/`

这些内容均为本地依赖、临时文件、编译缓存、SQLite 自检库或 `collectstatic` 产物，不属于业务源码。

## 根目录

- `/.gitignore`
  - 忽略虚拟环境、本地依赖目录、缓存目录、静态产物与媒体目录
- `/.env.example`
  - 生产/开发环境变量示例
- `/manage.py`
  - Django 管理入口
- `/requirements.txt`
  - Python 依赖清单
- `/sitecustomize.py`
  - 本地 Python 启动时尝试附加 `.packages` 目录
- `/pytest.ini`
  - pytest 与 pytest-django 配置
- `/Dockerfile`
  - Web 容器镜像构建文件
- `/docker-compose.yml`
  - Django + PostgreSQL + Nginx 编排文件
- `/entrypoint.sh`
  - 容器启动脚本，负责迁移、静态资源收集和 Gunicorn 启动
- `/README.md`
  - 本地启动、测试、部署、导出、提醒命令与默认账号说明

## config 目录

- `/config/__init__.py`
  - 配置包初始化文件
- `/config/bootstrap.py`
  - 将 `.packages` 加入 `sys.path` 的本地依赖引导
- `/config/env.py`
  - 环境变量读取与 PostgreSQL 配置构建工具
- `/config/urls.py`
  - 项目总路由，挂载登录、登出、工作台、排课、完成、备注、收款、提醒路由
- `/config/asgi.py`
  - ASGI 入口
- `/config/wsgi.py`
  - WSGI 入口

### settings 分层

- `/config/settings/__init__.py`
  - settings 包初始化文件
- `/config/settings/base.py`
  - 通用设置：应用注册、中间件、模板、静态资源、登录跳转、日志、Sentry 接入
- `/config/settings/dev.py`
  - 开发设置；默认走 PostgreSQL，允许显式启用 SQLite 自检模式
- `/config/settings/prod.py`
  - 生产设置；强制走 PostgreSQL
- `/config/settings/test.py`
  - 测试设置；使用 SQLite 测试库和更快的密码哈希

## dashboard 目录

- `/dashboard/__init__.py`
  - 工作台 app 初始化文件
- `/dashboard/apps.py`
  - 工作台 app 配置，并在启动时设置 Django Admin 标题
- `/dashboard/views.py`
  - 工作台首页、报表中心、CSV 导出、Excel 报表生成视图
- `/dashboard/urls.py`
  - 工作台与报表相关路由

## students 目录

- `/students/__init__.py`
  - 学员 app 初始化文件
- `/students/apps.py`
  - 学员 app 配置
- `/students/models.py`
  - `TimeStampedModel`、`Student`、`ServicePlan` 模型定义
- `/students/forms.py`
  - 学员档案表单、服务方案表单，以及服务方案内联 formset
- `/students/views.py`
  - 学员列表、新增、编辑视图，负责学员中心录入与汇总展示
- `/students/urls.py`
  - 学员中心路由
- `/students/admin.py`
  - 学员与服务方案的 Admin 注册和学员内联展示
- `/students/migrations/__init__.py`
  - 学员迁移包初始化文件
- `/students/migrations/0001_initial.py`
  - 学员和服务方案初始迁移

## schedules 目录

- `/schedules/__init__.py`
  - 排课 app 初始化文件
- `/schedules/apps.py`
  - 排课 app 配置
- `/schedules/models.py`
  - `Schedule` 模型、冲突校验、日历颜色和系列分组逻辑
- `/schedules/forms.py`
  - 排课表单，包含系列规则与修改范围
- `/schedules/services.py`
  - 系列排课创建与系列范围更新服务
- `/schedules/views.py`
  - 日历页、事件接口、排课新增/编辑页
- `/schedules/urls.py`
  - 排课路由
- `/schedules/admin.py`
  - 排课 Admin 配置
- `/schedules/migrations/__init__.py`
  - 排课迁移包初始化文件
- `/schedules/migrations/0001_initial.py`
  - 排课初始迁移

## sessions 目录

- `/sessions/__init__.py`
  - 完成记录 app 初始化文件
- `/sessions/apps.py`
  - 完成记录 app 配置，使用 `lesson_sessions` 作为 app label
- `/sessions/models.py`
  - `LessonSession` 模型定义
- `/sessions/forms.py`
  - 完成记录表单
- `/sessions/services.py`
  - 完成流程服务，负责课时扣减、欠课时记录、完成记录写入
- `/sessions/views.py`
  - “完成上课”流程页视图
- `/sessions/urls.py`
  - 完成流程路由
- `/sessions/admin.py`
  - 完成记录 Admin 配置
- `/sessions/migrations/__init__.py`
  - 完成记录迁移包初始化文件
- `/sessions/migrations/0001_initial.py`
  - 完成记录初始迁移

## notes 目录

- `/notes/__init__.py`
  - 备注 app 初始化文件
- `/notes/apps.py`
  - 备注 app 配置
- `/notes/models.py`
  - `SessionNote` 模型定义
- `/notes/forms.py`
  - 备注表单
- `/notes/views.py`
  - 备注新增/编辑视图
- `/notes/urls.py`
  - 备注路由
- `/notes/admin.py`
  - 备注 Admin 配置
- `/notes/migrations/__init__.py`
  - 备注迁移包初始化文件
- `/notes/migrations/0001_initial.py`
  - 备注初始迁移

## payments 目录

- `/payments/__init__.py`
  - 收款 app 初始化文件
- `/payments/apps.py`
  - 收款 app 配置
- `/payments/models.py`
  - `Receivable` 与 `PaymentEntry` 模型定义，以及收款状态汇总逻辑
- `/payments/forms.py`
  - 应收表单与实收流水表单
- `/payments/views.py`
  - 应收列表、新增、编辑和实收流水录入视图
- `/payments/urls.py`
  - 收款路由
- `/payments/admin.py`
  - 收款 Admin 配置与流水内联展示
- `/payments/migrations/__init__.py`
  - 收款迁移包初始化文件
- `/payments/migrations/0001_initial.py`
  - 应收与实收流水初始迁移

## reminders 目录

- `/reminders/__init__.py`
  - 提醒 app 初始化文件
- `/reminders/apps.py`
  - 提醒 app 配置
- `/reminders/models.py`
  - `ReminderConfig` 与 `ReminderTask` 模型定义
- `/reminders/forms.py`
  - 提醒配置表单
- `/reminders/services.py`
  - 课程提醒扫描、待收款提醒扫描、标记完成逻辑
- `/reminders/views.py`
  - 提醒中心、提醒配置保存、提醒扫描、提醒完成视图
- `/reminders/urls.py`
  - 提醒路由
- `/reminders/admin.py`
  - 提醒任务和提醒配置 Admin 配置
- `/reminders/migrations/__init__.py`
  - 提醒迁移包初始化文件
- `/reminders/migrations/0001_initial.py`
  - 提醒模型初始迁移

### 提醒管理命令

- `/reminders/management/__init__.py`
  - 管理命令包初始化文件
- `/reminders/management/commands/__init__.py`
  - 管理命令子包初始化文件
- `/reminders/management/commands/scan_course_reminders.py`
  - 课程提醒扫描命令
- `/reminders/management/commands/scan_receivable_reminders.py`
  - 待收款提醒扫描命令
- `/reminders/management/commands/scan_all_reminders.py`
  - 统一扫描两类提醒的命令

## templates 目录

- `/templates/base.html`
  - 全站基础模板，含导航、Bootstrap、HTMX、消息提示和移动端布局
- `/templates/registration/login.html`
  - 登录页模板

### dashboard 模板

- `/templates/dashboard/home.html`
  - 工作台首页模板，展示今日课程、待收款、待提醒
- `/templates/dashboard/report_center.html`
  - 报表中心模板

### students 模板

- `/templates/students/student_list.html`
  - 学员列表页模板，提供搜索、筛选、汇总卡片和快速操作按钮
- `/templates/students/student_form.html`
  - 学员新增/编辑模板，集中维护学员档案、服务方案与关联业务摘要
- `/templates/students/_service_plan_form.html`
  - 服务方案行模板，供学员表单和动态新增方案行复用

### schedules 模板

- `/templates/schedules/calendar.html`
  - FullCalendar 日历页模板
- `/templates/schedules/schedule_form.html`
  - 排课新增/编辑模板，含完成记录和备注快捷入口

### sessions 模板

- `/templates/sessions/complete_form.html`
  - 完成上课流程模板

### notes 模板

- `/templates/notes/note_form.html`
  - 备注新增/编辑模板

### payments 模板

- `/templates/payments/receivable_list.html`
  - 应收列表与汇总模板
- `/templates/payments/receivable_form.html`
  - 应收新增/编辑模板，集成流水追加入口
- `/templates/payments/payment_entry_form.html`
  - 独立实收流水录入模板

### reminders 模板

- `/templates/reminders/center.html`
  - 提醒中心模板，展示配置、任务列表、扫描按钮、完成按钮

## tests 目录

- `/tests/conftest.py`
  - pytest 公共 fixture，负责创建用户、学员、服务方案
- `/tests/test_workflows.py`
  - 核心业务自动化测试，覆盖登录保护、冲突校验、系列排课、课时扣减、收款状态、提醒生成和报表下载

## deploy 目录

- `/deploy/nginx/default.conf`
  - Nginx 反向代理与静态/媒体文件分发配置
- `/deploy/cron/app.cron`
  - 课程提醒和待收款提醒的 Cron 示例配置

## 资源目录

- `/static/.gitkeep`
  - 静态资源目录占位文件
- `/media/.gitkeep`
  - 媒体文件目录占位文件

## memory 文档

- `/memory/tutoring_consulting_system_design.md`
  - 最高优先级设计文档
- `/memory/implementation_plan.md`
  - 分阶段实施计划
- `/memory/tutoring_consulting_system_tech_stack.md`
  - 技术栈说明
- `/memory/progress.md`
  - 当前开发进度记录
- `/memory/architecture.md`
  - 当前文件职责说明

## 2026-04-22 UI 补充

- `/config/context_processors.py`
  - 向全站模板注入壳层所需的提醒数量和当前登录用户显示名
- `/templates/base.html`
  - 全站新 UI 壳层模板，负责侧边导航、顶部搜索、提醒徽标、报表导出按钮和移动端底部导航
- `/templates/dashboard/home.html`
  - 新版工作台首页模板，按参考图组织 KPI 卡片、今日课程、提醒中心、学员概览、收款趋势与最近记录
- `/templates/dashboard/report_center.html`
  - 与新版壳层统一后的报表中心模板
- `/templates/students/student_list.html`
  - 新版学员管理列表页模板，含筛选条、概览卡片和快捷业务入口
- `/templates/students/student_form.html`
  - 新版学员档案页模板，含档案录入、服务方案维护和业务摘要区
- `/templates/students/_service_plan_form.html`
  - 服务方案子表单模板，适配新版表单卡片风格
- `/templates/schedules/calendar.html`
  - 新版排课日历页模板，统一日历面板与近期排课侧栏视觉
- `/templates/schedules/schedule_form.html`
  - 新版排课编辑页模板，统一表单、当前记录、完成记录和备注侧栏布局
- `/templates/payments/receivable_list.html`
  - 新版收款列表页模板，含筛选、汇总卡片和状态化表格
- `/templates/payments/receivable_form.html`
  - 新版应收详情页模板，支持账款概况、快速录入实收和流水列表
- `/templates/payments/payment_entry_form.html`
  - 新版实收流水录入模板
- `/templates/reminders/center.html`
  - 新版提醒中心模板，统一配置面板和任务列表卡片样式
- `/templates/sessions/complete_form.html`
  - 新版完成上课录入模板
- `/templates/notes/note_form.html`
  - 新版课后备注录入模板
- `/start_local.bat`
  - Windows 本地一键启动脚本，自动设置本地自检环境变量、执行迁移并启动开发服务
- `/students/migrations/0002_alter_student_status_alter_student_tags.py`
  - 补充 `Student.status` 与 `Student.tags` 的字段变更迁移，消除启动时的未迁移告警
- `/config/views.py`
  - 放置全局级别的配置相关视图，目前包含自定义 CSRF 失败页视图
- `/templates/errors/csrf_failure.html`
  - 自定义 CSRF 失败页面，替代 Django 默认调试报错页，给出刷新和重新登录指引
- `/templates/dashboard/home.html`
  - 当前版本的工作台模板已移除右侧移动端演示区，保留纯桌面主内容布局，并新增首页快捷入口卡片区

## 2026-05-03 本地一键登录

- `/config/settings/base.py`
  - 增加一键登录相关配置项，包括入口开关、默认用户名和默认密码
- `/config/settings/dev.py`
  - 在开发环境默认跟随本地自检模式开启一键登录，并允许通过环境变量覆盖
- `/config/context_processors.py`
  - 向全站模板注入 `one_click_login_enabled`，用于控制登录页是否展示快捷入口
- `/config/views.py`
  - 新增 `quick_login_view`，负责本地一键登录、自动创建账号与安全跳转
- `/config/urls.py`
  - 挂载 `/accounts/quick-login/` 路由
- `/templates/registration/login.html`
  - 登录页模板，新增“本地快速入口”和“一键登录”按钮
- `/.env.example`
  - 补充一键登录相关环境变量示例
- `/tests/test_workflows.py`
  - 覆盖登录页快捷入口展示和一键登录流程
