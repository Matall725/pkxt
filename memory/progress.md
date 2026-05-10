# 开发进度记录

## 2026-04-22 10:00 +08:00

### 学员中心补充

- 新增独立学员管理入口 `/students/`，不再只依赖 Django Admin
- 新增学员列表页，支持按状态筛选、按姓名/昵称/手机号/家长联系方式搜索
- 新增学员创建与编辑页，支持同页维护服务方案
- 学员页补充最近排课、最近应收、最近备注与汇总信息
- 从学员页可直接跳转到“新增排课”和“新增应收”
- 排课与应收创建页支持通过 query string 预填学员和服务方案

### 本轮目标

- 按设计文档完成首版系统主体实现
- 不再停在方案层，直接落地模型、后台、流程、提醒、报表、测试与部署物料

### 已完成阶段

#### 阶段一：基础工程

- 已完成 Django 单体工程骨架
- 已补充 `manage.py`、`config`、7 个业务 app、模板目录、静态目录、媒体目录
- 已加入 `config.bootstrap` 以自动加载工作区 `.packages` 依赖目录
- 已将配置拆分为 `base / dev / prod / test`
- 已加入 `.env.example`
- 已实现显式环境变量读取与错误提示

说明：

- 正式开发/生产配置以 PostgreSQL 为目标
- 当前工作区为了在无 PostgreSQL 服务环境下持续推进，实现了显式启用的 `DJANGO_ALLOW_SQLITE_BOOTSTRAP=1` 自检模式
- 该模式仅用于当前受限环境中的本地验证，不作为正式部署方案

#### 阶段二：核心数据模型

已完成模型：

- 学员 `Student`
- 服务方案 `ServicePlan`
- 排课 `Schedule`
- 完成记录 `LessonSession`
- 课后备注 `SessionNote`
- 应收记录 `Receivable`
- 实收流水 `PaymentEntry`
- 提醒配置 `ReminderConfig`
- 提醒任务 `ReminderTask`

已落地的关键约束：

- 学员唯一性采用“姓名 + 手机号”
- 同一学员仅允许一个生效中的服务方案
- 排课必须关联学员、服务方案、执行账号
- 排课冲突同时校验执行账号与学员
- 已取消记录不参与冲突判断
- 一条排课仅允许一条完成记录
- 一条排课允许多条备注
- 应收记录允许多笔实收流水
- 收款状态由流水汇总自动驱动
- 提醒任务通过 `window_key` 去重

#### 阶段三：后台录入与管理

已完成 Admin 注册与配置：

- `StudentAdmin`
- `ServicePlanAdmin`
- `ScheduleAdmin`
- `LessonSessionAdmin`
- `SessionNoteAdmin`
- `ReceivableAdmin`
- `PaymentEntryAdmin`
- `ReminderTaskAdmin`
- `ReminderConfigAdmin`

已完成：

- 学员详情页内联展示服务方案
- 应收页内联展示实收流水
- Admin 站点标题改为中文单账号工作台

#### 阶段四：排课主流程

已完成：

- FullCalendar 日历页
- 排课新增页
- 排课编辑页
- 系列排课规则：支持按天/按周生成多条排课
- 系列修改范围：仅本次 / 本次及未来 / 整个系列
- 状态支持待上课、已完成、已取消、已改期

修复记录：

- 排课批量创建首次失败，原因是 `start_at` 被重复传入
- 已在 `schedules.services.create_schedule_batch()` 中修复

#### 阶段五：上课完成、课时与备注

已完成：

- “完成上课”自定义流程页
- 课包制课时扣减
- 课包不足时的欠课时记录
- 完成记录回写排课状态
- 备注新增与编辑

验证结果：

- 完成课程后可正确扣减 `remaining_hours`
- 欠课时逻辑已由 pytest 覆盖

#### 阶段六：收款、汇总与报表

已完成：

- 应收列表页
- 应收新增/编辑页
- 实收流水新增页
- 实收汇总自动更新
- 状态自动切换：待收 / 部分收款 / 已收
- 报表中心
- 学员 CSV 导出
- 应收 CSV 导出
- 学员课时报表 Excel 下载
- 经营收款报表 Excel 下载

#### 阶段七：提醒机制

已完成：

- 提醒配置页
- 提醒中心
- 标记提醒完成
- 课程提醒扫描服务
- 待收款提醒扫描服务
- 3 个管理命令：
  - `scan_course_reminders`
  - `scan_receivable_reminders`
  - `scan_all_reminders`

验证结果：

- 已验证待收款提醒生成
- 已验证课程提醒生成
- 已验证重复扫描不会重复生成同一窗口提醒

#### 阶段八：质量、交付与部署

已完成：

- `pytest.ini`
- `tests/conftest.py`
- `tests/test_workflows.py`
- `Dockerfile`
- `docker-compose.yml`
- `entrypoint.sh`
- `deploy/nginx/default.conf`
- `deploy/cron/app.cron`
- `README.md`

### 验证结果

#### 配置与框架验证

1. `E:\\python.exe manage.py check`
   - 结果：通过
2. 登录页 `POST /accounts/login/`
   - 结果：302 跳转到 `/`，通过
3. 匿名访问 `/`、`/schedules/`、`/payments/`、`/reminders/`、`/reports/`
   - 结果：均正确跳转登录页

#### 数据库与迁移验证

1. 已生成全部业务迁移
2. 已执行 `manage.py migrate`
3. SQLite 自检数据库迁移通过

#### 业务链路验证

通过 Django `Client()` + ORM 走通链路：

1. 建学员
2. 配服务方案
3. 新建系列排课 2 条
4. 完成第一条课程
5. 录入课后备注
6. 新建应收记录
7. 录入首笔实收流水
8. 扫描提醒
9. 打开工作台、日历、收款、提醒中心
10. 下载 4 个报表/导出端点

结果：

- 全部返回 200 或正确跳转
- 系列排课生成成功
- 完成课程后剩余课时从 `10.00` 扣减到 `8.50`
- 收款状态从待收切换为部分收款
- 已生成待收款提醒与课程提醒

#### 自动化测试验证

执行：

```bash
python -m pytest -q
```

结果：

- `7 passed`

覆盖点：

- 登录保护
- 排课冲突校验
- 系列排课创建
- 课时扣减与欠课时
- 多笔流水收款状态流转
- 课程提醒与待收款提醒生成
- 报表导出下载

#### 部署相关验证

1. `manage.py collectstatic --noinput`
   - 结果：通过，收集到 `127` 个静态文件
2. `manage.py check --settings=config.settings.prod`
   - 结果：通过

### 修复与调整记录

- 修复 `sessions` app 与 Django 内建 `sessions` 标签冲突，改用 `lesson_sessions`
- 修复 `ALLOWED_HOSTS` 开发环境问题
- 修复 `ScheduleForm` 使用 `forms.TextChoices` 的错误写法，改为 `models.TextChoices`
- 修复 `create_schedule_batch()` 的 `start_at` 重复传参
- 为 pytest 增加 `testpaths = tests`，避免权限异常目录被错误收集
- 增加 `static/.gitkeep` 与 `media/.gitkeep`，消除静态目录缺失告警

### 当前遗留问题

- 当前机器没有可用的本地 PostgreSQL 服务，因此未执行“真实 PostgreSQL 连接 + 迁移 + 业务流”实连验证
- 当前机器没有 Docker 运行环境，因此未实际执行 `docker compose up`
- 当前机器未配置有效 Sentry DSN，因此仅完成代码接入，未执行真实上报验证
- 当前工作区 `.packages` 目录用于受限环境下的本地依赖验证；正式环境应按 `requirements.txt` 正常安装依赖

### 当前状态结论

- 设计文档约束已同步到代码实现
- 首版核心闭环已可运行
- 自定义页面、Admin、提醒、导出、报表、测试、部署物料均已落地
- 当前剩余缺口主要是“受限环境下无法完成的外部基础设施实连验证”，不是业务代码未实现

## 2026-04-22 21:40 +08:00

### UI 重做与统一

- 按用户提供的参考图，重做了整套后台的视觉外壳，统一为玻璃态卡片、左侧导航、顶部搜索与移动端底部标签栏
- 重写了 `templates/base.html`，解决了 `content` block 重复定义问题，并补充了全局颜色变量与壳层布局
- 重做了 `templates/dashboard/home.html`，加入 KPI 卡片、今日课程、提醒中心、学员概览、收款趋势图、最近记录和移动端预览区
- 重做了 `templates/students/student_list.html`、`templates/students/student_form.html` 和 `templates/students/_service_plan_form.html`，让学员中心与新工作台风格保持一致
- 统一了排课日历、排课表单、收款列表、应收表单、实收流水表单、提醒中心、完成上课、课后备注等核心业务页面的视觉样式
- 新增 `config/context_processors.py`，将提醒数量和当前登录人标签注入全站壳层

### 页面级回归

- `manage.py check` 通过
- `pytest -q` 通过，结果为 `8 passed`
- 额外使用 Django `Client()` 对以下页面逐一执行 GET 回归，均返回 `200`
- `/`
- `/reports/`
- `/students/`
- `/students/new/`
- `/students/<id>/edit/`
- `/schedules/`
- `/schedules/new/`
- `/schedules/<id>/edit/`
- `/payments/`
- `/payments/new/`
- `/payments/<id>/edit/`
- `/payments/<id>/entries/new/`
- `/reminders/`
- `/sessions/schedule/<id>/complete/`
- `/notes/schedule/<id>/new/`

### 额外说明

- Playwright 可执行环境已打通，但自动浏览器核对受本机 `npm` 权限限制影响，需要将缓存目录切到工作区本地目录才能运行
- 终端中看到的部分中文乱码属于 PowerShell 控制台显示问题，不是模板文件本身的 UTF-8 编码损坏

## 2026-04-22 21:55 +08:00

### Windows 简化启动

- 新增根目录脚本 `start_local.bat`
- 脚本默认使用本地自检模式启动，不再要求用户每次手动打开 PowerShell 输入环境变量和启动命令
- 脚本会自动执行迁移并启动本地开发服务，同时自动打开登录页
- 额外支持 `--check` 和 `--migrate-only` 两个参数，便于快速检查和单独迁移
- 在验证启动脚本时发现 `students` app 存在缺失迁移，已补充 `0002_alter_student_status_alter_student_tags.py`
- 重新执行 `start_local.bat --migrate-only` 后已无未迁移模型告警

## 2026-04-22 22:10 +08:00

### CSRF 失败页优化

- 验证了登录页的 CSRF 链路本身是正常的：登录页会下发 `csrftoken`，带正确 token 提交可正常登录
- 结合用户实际遇到的 403 场景，将系统默认的 Django 调试版 CSRF 报错页替换为自定义友好提示页
- 新增 `config.views.csrf_failure` 并在 settings 中接入 `CSRF_FAILURE_VIEW`
- 新增模板 `templates/errors/csrf_failure.html`，明确提示“刷新当前页再提交”或“重新登录”的处理方式
- 新增自动化测试覆盖 CSRF 失败页，当前测试结果提升为 `9 passed`

## 2026-04-22 22:18 +08:00

### 工作台右侧演示区删除

- 按用户要求，删除了工作台右侧的伪移动端演示区，不再使用手机外框展示预览内容
- `templates/dashboard/home.html` 已改为纯桌面主内容布局，首页不再为右侧预览保留额外列宽
- `dashboard/views.py` 中对应的 `quick_preview_*` 上下文数据已一并清理
- 已验证首页返回 `200`，且 HTML 输出中不再包含 `preview-rail` 与 `phone-screen` 结构

## 2026-04-22 22:26 +08:00

### 工作台快捷入口补充

- 在工作台首屏新增“快捷入口”区域，直接提供新增学员、快速排课、登记应收、扫描提醒、报表中心、后台设置 6 个高频入口
- 快捷入口采用卡片式布局，和 KPI 卡片保持同一套视觉语言，桌面端为多列展示，移动端自动折叠为单列
- “扫描提醒”入口直接在首页发起 POST，不需要先进入提醒中心
- 新增自动化测试覆盖首页快捷入口文案，当前测试结果提升为 `10 passed`

## 2026-05-03 10:20 +08:00

### 登录页一键登录入口

- 在登录页新增“本地一键登录”入口，仅在本地自检或显式开启配置时显示
- 新增 `/accounts/quick-login/` POST 入口，支持自动创建本地账号并直接完成登录
- 一键登录默认使用 `owner` 账号，并允许通过环境变量覆盖用户名与初始密码
- 新增全局模板上下文，使登录页和其他模板都能感知一键登录开关状态
- 补充自动化测试覆盖登录页入口展示和一键登录跳转，当前测试结果提升为 `12 passed`
