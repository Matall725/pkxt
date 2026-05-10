# Tutoring / Consulting System Tech Stack

## 1. 技术栈结论

本系统建议采用 **Django 单体架构**，配合 **PostgreSQL**，以前后端不过度分离的方式实现轻后台。  
目标是用最少的自研代码，直接复用成熟框架能力，优先保证稳定性、可维护性、移动端可用性和上线速度。

**推荐组合：**

- 语言：Python 3.12
- Web 框架：Django 5.x
- 数据库：PostgreSQL 16
- 后台界面：Django Admin + 少量自定义页面
- 模板层：Django Templates
- 响应式样式：Bootstrap 5
- 交互增强：HTMX
- 日历排课：FullCalendar
- 数据导出：`django-import-export`
- 报表模板：`openpyxl`
- 定时提醒：系统 Cron + Django management commands
- 部署：Docker Compose + Nginx + Gunicorn
- 监控与错误追踪：Sentry
- 测试：pytest + pytest-django

## 2. 为什么这是最简洁而健壮的方案

- 这是典型的中小型内部运营后台，核心是 CRUD、排期、统计、提醒、导出、报表，不需要一开始拆成前后端分离或微服务。
- Django 自带 ORM、鉴权、Admin、表单、迁移、管理命令、日志接入，能直接承担大部分底层能力。
- PostgreSQL 对排课、收款、统计这类强结构化数据更稳妥，也更适合后续报表查询。
- Django Admin 可以直接覆盖学员、收款、备注、课时记录等高频后台操作，显著减少页面开发量。
- 排课日历只针对一个关键页面做定制，接入 FullCalendar 即可，不需要额外搭建复杂前端工程。
- 自动提醒在 MVP 阶段直接使用 Cron 调度 Django 命令，比引入消息队列和分布式任务系统更简单，也更容易维护。
- 导出与报表优先复用成熟库，不自行实现底层文件格式。

## 3. 首版架构边界

- 首版采用单账号模式。
- 直接复用 Django 内建认证体系，不自定义复杂用户模型。
- 后台以 Django Admin 为主，自定义页面只覆盖工作台、日历、报表、少量关键录入页。
- 自定义页面必须提供移动端适配。
- 保留与 Django `User` 的关联字段，为后续多账号扩展预留空间，但首版不启用多角色权限边界。

## 4. 各层技术选型

### 4.1 后端

**Django 5.x**

外部依赖直接提供以下成熟能力，本项目不应重复实现：

- `django.contrib.auth`：登录、用户、权限基础设施
- `django.contrib.admin`：后台管理界面
- Django ORM：模型定义、查询、聚合统计
- Django Migration：数据库结构迁移
- Django Form / ModelForm：后台录入与校验
- Django management commands：定时任务执行入口
- Django logging：标准日志接入

适用原因：

- 强关系数据建模成熟
- 后台型系统开发效率高
- 生态稳定，长期维护成本低

### 4.2 数据库

**PostgreSQL 16**

适用对象：

- 学员档案
- 服务方案
- 排课记录
- 完成记录
- 应收记录
- 实收流水
- 课后备注
- 提醒任务

选择原因：

- 事务能力稳定，适合收款、课时扣减与欠课时记录
- 聚合统计能力强
- 约束、索引、唯一性校验清晰

### 4.3 页面层

采用 **Django Admin 为主，自定义页面为辅** 的策略：

- 学员管理：优先直接用 Django Admin
- 应收与实收流水：优先直接用 Django Admin
- 课后备注：优先直接用 Django Admin
- 课时统计：Admin 列表 + 自定义统计页
- 排课日历：首页或单独页面定制开发
- 报表导出：单独报表页

### 4.4 响应式与交互

**Bootstrap 5 + HTMX**

- Bootstrap 5 用于自定义页面响应式布局与移动端适配
- HTMX 用于局部刷新、表单异步提交、列表局部更新

这样可以避免引入完整 SPA 框架，同时保留足够顺滑的后台交互体验。

### 4.5 日历组件

**FullCalendar**

外部依赖直接提供：

- 日/周/月视图
- 拖拽调整排课
- 时间段展示
- 事件颜色区分
- 冲突感知展示基础能力

本项目只负责：

- 提供课程数据接口
- 处理新增、改期、取消、系列规则的业务规则

不应自行实现日历渲染与交互组件。

### 4.6 导出与报表

**django-import-export + openpyxl**

外部依赖直接提供：

- Admin 导出能力
- CSV / Excel 文件生成
- Excel 报表模板填充

本项目只负责：

- 定义报表字段与模板结构
- 组织数据查询与填充流程

不应自行实现底层 Excel 编码逻辑。

## 5. 自动提醒方案

### 5.1 MVP 方案

采用 **系统 Cron + Django management command**：

- 每 5 分钟扫描即将开始的课程提醒
- 每天固定时间扫描待收款提醒
- 通过系统内提醒中心展示未完成与已完成提醒

优点：

- 组件少
- 可运维性强
- 故障定位直接
- 不需要引入 Redis、Celery 等额外基础设施

### 5.2 升级方案

如果后续提醒量变大，或需要异步短信/邮件/微信通知，可升级为：

- Redis
- Celery
- `django-celery-beat`

但不建议在首版直接引入。

## 6. 推荐部署方式

### 6.1 运行环境

- Ubuntu 22.04 LTS
- Docker Compose
- Nginx
- Gunicorn

### 6.2 部署结构

- `nginx`：反向代理、静态文件分发
- `web`：Django 应用
- `db`：PostgreSQL

MVP 不强制增加 Redis、消息队列、搜索引擎。

## 7. 测试、日志与监控

### 7.1 测试

- `pytest`
- `pytest-django`

重点测试：

- 排课冲突校验
- 课时扣减与欠课时记录
- 收款状态统计与多笔流水汇总
- 提醒扫描逻辑
- 导出与报表模板生成
- 登录保护

### 7.2 日志与异常追踪

- Django Admin 自带操作日志
- Django 标准 logging
- Sentry

重点监控：

- 排课保存失败
- 收款入账失败
- 报表导出失败
- 提醒任务执行失败

## 8. 建议的数据模块划分

建议保持单体仓库，但按业务拆分 Django app：

- `students`：学员档案
- `schedules`：排课
- `sessions`：完成记录与课时统计
- `payments`：应收记录与实收流水
- `notes`：课后备注
- `reminders`：提醒任务与提醒配置
- `dashboard`：工作台、统计页、报表页

## 9. 明确不推荐的首版方案

以下方案不适合当前项目首版：

- 前后端完全分离的 React/Vue + API 双工程
- 微服务架构
- MongoDB 作为主库
- 一开始就接入复杂消息队列
- 为了排课单独自研日历与提醒引擎
- 自行实现底层导出引擎或报表文件格式

这些方案都会显著增加开发量和维护成本，不符合“轻后台、快落地、低复杂度”的目标。

## 10. 最终建议

如果目标是 **尽快上线一个简洁、稳、够用、移动端可用的小系统**，最推荐的技术栈是：

**Python 3.12 + Django 5 + PostgreSQL + Django Admin + Bootstrap 5 + HTMX + FullCalendar + django-import-export + openpyxl + Cron + Docker Compose + Sentry**

这套组合能够最大化复用成熟生产级能力，把当前项目严格控制在：

- 业务流程编排
- 模型定义
- 页面少量定制
- 规则校验
- 导出与报表填充
- 提醒调度

而不把时间浪费在重复实现权限、后台框架、表单系统、日历控件、导出引擎和任务基础设施上。
