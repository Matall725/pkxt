# 家教/咨询排课与收款系统

## 项目说明

本项目采用 Django 单体架构，服务于单账号场景下的家教/咨询排课、课时、收款、备注、提醒与报表管理。

当前实现重点：

- 学员与服务方案
- 排课与系列规则
- 上课完成、课时扣减与欠课时记录
- 应收记录与多笔实收流水
- 课后备注
- 课程提醒与待收款提醒
- 工作台、报表中心、移动端基础适配
- Django Admin 后台录入

## 环境变量

参考 `.env.example`：

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_ENABLE_SENTRY`
- `SENTRY_DSN`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

## 本地启动

### PostgreSQL 正式模式

1. 准备 PostgreSQL 16 数据库
2. 配置环境变量
3. 执行：

```bash
python manage.py migrate --settings=config.settings.dev
python manage.py createsuperuser --settings=config.settings.dev
python manage.py runserver --settings=config.settings.dev
```

### 当前工作区自检模式

当前仓库为了便于在受限环境中验证，支持显式启用 SQLite 自检模式：

```bash
set DJANGO_SECRET_KEY=dev-secret-key
set DJANGO_ALLOW_SQLITE_BOOTSTRAP=1
python manage.py migrate
python manage.py runserver
```

该模式仅用于本地自检，不作为正式部署方案。

## 测试

```bash
python -m pytest -q
```

## 核心管理命令

- `python manage.py scan_course_reminders`
- `python manage.py scan_receivable_reminders`
- `python manage.py scan_all_reminders`

## 部署

### Docker Compose

1. 准备 `.env`
2. 执行：

```bash
docker compose up --build -d
```

### 部署顺序

1. 启动 PostgreSQL
2. 启动 Django 容器
3. 自动执行迁移与静态资源收集
4. 由 Gunicorn 提供应用服务
5. 由 Nginx 反向代理并分发静态文件
6. 按 `deploy/cron/app.cron` 配置提醒扫描任务

## 报表与导出

- `/reports/students.csv`
- `/reports/receivables.csv`
- `/reports/hours.xlsx`
- `/reports/finance.xlsx`

## 默认单账号

当前本地自检已创建：

- 用户名：`owner`
- 密码：`ChangeMe123!`

上线前必须改为正式密码或重新创建账号。

## Windows 一键启动

如果你只是本地使用，不想每次打开 PowerShell 手动输入命令，可以直接双击项目根目录下的：

- `start_local.bat`

这个脚本会自动：

1. 进入项目目录
2. 设置本地自检所需环境变量
3. 执行 `manage.py migrate`
4. 启动本地服务
5. 自动打开登录页

额外参数：

- `start_local.bat --check`
  - 只执行 `manage.py check`
- `start_local.bat --migrate-only`
  - 只执行数据库迁移，不启动服务

## 本地一键登录

本地自检模式下，登录页会显示 `本地一键登录` 按钮，点击后会直接进入系统，无需手动输入账号密码。

- 入口地址：`/accounts/login/`
- 提交地址：`/accounts/quick-login/`
- 默认账号：`owner`
- 默认密码：`ChangeMe123!`

控制开关如下：

- `DJANGO_ENABLE_ONE_CLICK_LOGIN=1`
  - 强制显示一键登录入口
- `DJANGO_ONE_CLICK_LOGIN_USERNAME`
  - 指定一键登录使用的本地账号
- `DJANGO_ONE_CLICK_LOGIN_PASSWORD`
  - 当账号不存在时，自动创建账号并写入这个密码

说明：

- `start_local.bat` 默认会进入本地自检模式，因此登录页会显示这个入口
- 正式环境默认关闭，不建议对公网环境开启
