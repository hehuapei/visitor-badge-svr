# visitor-badge-svr

一个基于 FastAPI + MySQL 的访客计数服务，兼容旧 `api-svr` 的核心 `/count` 行为，可作为 README visitor badge 的后端。

## 功能

- `GET /count` 查询计数值
- `action=update` 时原子递增
- 缺失 key 自动初始化
- MySQL 唯一键保证并发正确性
- 所有启动参数集中在 `config.toml`

## 环境要求

- Python `3.9+`
- MySQL / MariaDB

## 快速开始

### 1) 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -r requirements.txt
```

### 2) 配置数据库连接

编辑根目录下的 `config.toml`：

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

如果设置了 `mysql.url`，它会优先于拆分式 MySQL 配置。

如果要使用别的配置文件路径：

```bash
CONFIG_FILE=/etc/visitor-badge-svr/config.toml python -m app.main
```

### 3) 初始化表结构

服务**不会**在启动时自动建表，请先执行：

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

### 5) 验证接口

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

返回示例：

```json
{"value": 0}
```

## 数据库说明

- 启动时会检查 `count.keyword` 是否满足 `NOT NULL` 和 `UNIQUE`
- `schema.sql` 当前使用 `VARCHAR(191)`，兼容较老版本 MySQL / MariaDB 的索引长度限制
- 如果数据库表结构不满足要求，服务会在启动时直接失败

## 开发

运行测试：

```bash
pytest
```

静态检查：

```bash
ruff check .
```

## 许可证

MIT，详见 [`LICENSE`](LICENSE)。
