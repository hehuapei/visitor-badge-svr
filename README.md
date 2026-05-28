# api-svr-py

一个小而清晰的 FastAPI + MySQL 计数服务，实现与原始 `api-svr` 一致的核心接口行为。

## 项目状态

这个项目目前适合作为：

- 一个简洁的 FastAPI + SQLAlchemy 示例服务
- 一个可运行、可测试、可继续扩展的小型计数 API
- 一个从旧服务行为迁移到 Python 实现的参考版本

## 功能

- `GET /count` 查询计数值
- 缺失 key 从 `0` 开始初始化
- `action=update` 时原子递增
- MySQL 唯一键保证并发正确性
- 使用 SQLite 内存库的本地测试，跑得快

## 快速开始

### 1) 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) 准备 MySQL

默认开发配置（仅供本地使用）：

- host: `127.0.0.1`
- port: `3306`
- database: `api-svr`
- username: `root`
- password: `110`

如需修改，直接编辑根目录下的 `config.toml`。

### 3) 初始化表结构

服务**不会**在启动时自动建表，请先执行根目录下的 SQL 脚本：

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p api-svr < schema.sql
```

### 4) 启动服务

```bash
python -m app.main
```

默认监听：

```text
http://127.0.0.1:8080
```

### 5) 调接口

```bash
curl "http://127.0.0.1:8080/count"
curl "http://127.0.0.1:8080/count?keyword=demo"
curl "http://127.0.0.1:8080/count?keyword=demo&action=update"
```

## 接口说明

### `GET /count`

查询参数：

- `keyword`: 计数 key
- `action`: 当值为 `update` 时执行递增；其他值只读取当前值

行为：

- `keyword` 为空时返回 `0`
- key 不存在时：
  - 普通查询返回 `0`
  - `action=update` 返回 `1`
- 已存在 key 的 `update` 请求会原子递增并返回新值

返回值：

```json
{"value": 0}
```

## 配置

所有启动参数集中在根目录的 `config.toml`：

```toml
[server]
port = 8080
workers = 1

[mysql]
host = "127.0.0.1"
port = 3306
database = "api-svr"
username = "root"
password = "110"
pool_size = 20
max_overflow = 40
pool_timeout = 30
pool_recycle = 1800
# url = "mysql+pymysql://root:110@127.0.0.1:3306/api-svr?charset=utf8mb4"
```

如果设置了 `mysql.url`，它会优先于拆分式 MySQL 配置项。

需要在不同环境下使用不同配置，可以通过 `CONFIG_FILE` 环境变量指定其它配置文件路径，例如：

```bash
CONFIG_FILE=/etc/api-svr/config.toml python -m app.main
```

## 开发

### 运行测试

```bash
pytest
```

### 静态检查

```bash
ruff check .
```

## 项目结构

```text
app/
  config.py      配置加载
  db.py          数据库引擎与会话
  main.py        应用入口与路由
  models.py      数据模型
  repository.py  持久化逻辑
  service.py     业务逻辑

tests/
  test_api.py     API 层测试
  test_service.py 服务与并发测试

config.toml      启动参数配置
schema.sql       MySQL 初始化脚本
```

## 表结构说明

服务启动时会检查 `count.keyword` 是否满足：

- `NOT NULL`
- `UNIQUE`

如果数据库里还没有 `count` 表，或者表结构不满足要求，启动会失败，并提示你先执行 `schema.sql` 或手工迁移。

## 贡献

欢迎提交 issue 和 PR。开始之前请先阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 许可证

MIT，详见 [`LICENSE`](LICENSE)。
