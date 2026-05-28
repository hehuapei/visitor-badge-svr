# 部署说明

这份文档面向把 `api-svr-py` 部署到真实服务器的人，重点覆盖：

- 是否需要数据库迁移
- 如何初始化或迁移 `count` 表
- 如何准备运行环境
- 如何启动服务
- 如何做上线后验证

---

## 1. 部署结论

如果你是**全新空库部署**：

- 直接执行 `schema.sql`
- 编辑 `config.toml`
- 启动服务

如果你是**从旧版 `api-svr` 迁移现有数据库**：

- **不能直接启动这个 Python 版本**
- 需要先检查并迁移 `count` 表
- 原因是新版本要求：
  - `count` 表必须存在
  - `count.keyword` 必须 `NOT NULL`
  - `count.keyword` 必须 `UNIQUE`

当前旧库备份显示：

- `keyword` 允许 `NULL`
- `keyword` 没有唯一索引
- 还存在重复 `keyword`

所以旧库场景需要先迁移，再部署。

---

## 2. 服务器要求

建议环境：

- Python `3.9+`
- MySQL `8.x`
- Linux 服务器，建议配合 systemd 或其他进程管理器

Python 依赖统一从 `requirements.txt` 安装。

---

## 3. 部署过程中会用到的文件

部署时主要会用到这些文件：

- `requirements.txt`
- `config.toml`
- `schema.sql`
- `app/main.py`

---

## 4. 准备 Python 运行环境

在服务器上进入项目目录后执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 5. 配置文件

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
password = "change-me"
pool_size = 20
max_overflow = 40
pool_timeout = 30
pool_recycle = 1800
# url = "mysql+pymysql://root:change-me@127.0.0.1:3306/api-svr?charset=utf8mb4"
```

### 生产环境建议

- 不要继续使用默认密码
- 如果你已经有统一的数据库连接串，可以直接设置 `mysql.url`，它会优先于拆分式的 MySQL 配置
- 仓库自带的 `config.toml` 默认带的是开发环境配置；生产环境推荐把生产配置放在仓库外，例如 `/etc/api-svr/config.toml`，然后通过 `CONFIG_FILE` 环境变量指向它
- 如果想在仓库内维护本地覆盖，可以新建 `config.local.toml`（已经在 `.gitignore` 里），用 `CONFIG_FILE=config.local.toml` 启动

---

## 6. 全新数据库初始化

如果目标数据库里还没有 `count` 表，先执行：

```bash
mysql -h <host> -P <port> -u <user> -p <database> < schema.sql
```

例如：

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p api-svr < schema.sql
```

`schema.sql` 内容如下：

```sql
CREATE TABLE IF NOT EXISTS `count` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `keyword` VARCHAR(255) NOT NULL,
  `total` BIGINT NOT NULL,
  `create_time` BIGINT DEFAULT NULL,
  `update_time` BIGINT DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `keyword` (`keyword`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
```

---

## 7. 从旧版 `api-svr` 数据库迁移

如果你使用旧版数据库备份恢复数据后再部署 Python 版本，**先不要直接启动服务**。

### 7.1 为什么必须迁移

新版本启动时会校验：

- `count` 表必须存在
- `keyword` 必须 `NOT NULL`
- `keyword` 必须 `UNIQUE`

而旧备份中的 `count` 表通常是：

```sql
CREATE TABLE `count` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `create_time` bigint(20) DEFAULT NULL,
  `keyword` varchar(255) COLLATE utf8mb4_bin DEFAULT NULL,
  `total` bigint(20) NOT NULL,
  `update_time` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
)
```

这和新版本要求不兼容。

### 7.2 迁移前先检查外键风险

先确认没有别的表依赖 `count.id`：

```sql
SELECT
  TABLE_NAME,
  COLUMN_NAME,
  CONSTRAINT_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE REFERENCED_TABLE_SCHEMA = DATABASE()
  AND REFERENCED_TABLE_NAME = 'count';
```

如果结果不是空，请先停下来评估依赖关系，再决定迁移策略。

### 7.3 迁移脚本

下面这份脚本适用于当前这个 Python 服务的数据模型。

它的去重策略是：

- 保留最小 `id`
- `total` 取最大值
- `create_time` 取最早
- `update_time` 取最新

```sql
USE `api-svr`;

SELECT COUNT(*) AS null_keywords
FROM `count`
WHERE `keyword` IS NULL;

SELECT `keyword`, COUNT(*) AS row_count
FROM `count`
GROUP BY `keyword`
HAVING `keyword` IS NULL OR COUNT(*) > 1
ORDER BY row_count DESC, `keyword`
LIMIT 200;

SET @backup_table = CONCAT('count_backup_', DATE_FORMAT(NOW(), '%Y%m%d_%H%i%s'));

SET @sql = CONCAT('CREATE TABLE `', @backup_table, '` LIKE `count`');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = CONCAT('INSERT INTO `', @backup_table, '` SELECT * FROM `count`');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

START TRANSACTION;

DROP TEMPORARY TABLE IF EXISTS count_dedup;

CREATE TEMPORARY TABLE count_dedup AS
SELECT
  MIN(`id`) AS keep_id,
  `keyword`,
  MAX(`total`) AS keep_total,
  MIN(`create_time`) AS keep_create_time,
  MAX(`update_time`) AS keep_update_time
FROM `count`
WHERE `keyword` IS NOT NULL
GROUP BY `keyword`;

UPDATE `count` c
JOIN count_dedup d ON c.`id` = d.keep_id
SET
  c.`keyword` = d.`keyword`,
  c.`total` = d.keep_total,
  c.`create_time` = d.keep_create_time,
  c.`update_time` = d.keep_update_time;

DELETE c
FROM `count` c
LEFT JOIN count_dedup d ON c.`id` = d.keep_id
WHERE d.keep_id IS NULL;

ALTER TABLE `count`
  MODIFY COLUMN `keyword` VARCHAR(255) COLLATE utf8mb4_bin NOT NULL;

ALTER TABLE `count`
  ADD UNIQUE KEY `keyword` (`keyword`);

COMMIT;

SELECT COUNT(*) AS total_rows
FROM `count`;

SELECT COUNT(*) AS null_keywords
FROM `count`
WHERE `keyword` IS NULL;

SELECT COUNT(*) AS duplicate_keywords
FROM (
  SELECT `keyword`
  FROM `count`
  GROUP BY `keyword`
  HAVING COUNT(*) > 1
) t;

SHOW CREATE TABLE `count`;
```

### 7.4 迁移完成后的预期结果

迁移后你应该看到：

- `null_keywords = 0`
- `duplicate_keywords = 0`
- `SHOW CREATE TABLE count` 中有：
  - `keyword` `NOT NULL`
  - `UNIQUE KEY keyword (keyword)`

---

## 8. 启动服务

准备好 schema 和 `config.toml` 后，启动：

```bash
python -m app.main
```

如果你想用其它路径下的配置文件启动，比如生产环境的配置：

```bash
CONFIG_FILE=/etc/api-svr/config.toml python -m app.main
```

---

## 9. 上线后验证

### 基础 smoke test

```bash
curl "http://127.0.0.1:8080/count"
curl "http://127.0.0.1:8080/count?keyword=demo"
curl "http://127.0.0.1:8080/count?keyword=demo&action=update"
```

预期行为：

- `GET /count` -> `{"value": 0}`
- 不存在的 key 查询 -> `0`
- 不存在的 key 更新 -> `1`
- 重复更新会持续递增

### 表结构验证

如果服务启动失败，请优先检查：

- `count` 表是否存在
- `keyword` 是否 `NOT NULL`
- `keyword` 是否有唯一索引

---

## 10. 常见失败场景

### 1) 启动时报表结构缺失

例如：

```text
count table is missing; initialize the database with schema.sql before startup
```

说明：
- 你还没有执行 `schema.sql`
- 或者当前数据库里根本没有 `count` 表

### 2) 启动时报唯一约束或非空约束不兼容

说明：
- 你恢复的是旧版数据库
- 但还没做迁移

### 3) 迁移时加唯一索引失败

说明：
- 还有重复 `keyword` 没被清理干净
- 或者迁移脚本执行过程中被中断

---

## 11. 推荐部署顺序

推荐顺序：

1. 备份现有数据库
2. 检查是否有外键依赖 `count.id`
3. 如果是旧库，执行迁移脚本
4. 编辑 `config.toml`
5. 安装 Python 依赖
6. 启动服务
7. 跑 smoke test
8. 再切流量

---

## 12. 补充说明

- 当前版本不会自动建表，这是刻意设计，避免服务启动时偷偷修改数据库
- 对已有生产库，优先用迁移而不是删表重建
- 如果你希望我进一步给你补 `systemd` 服务文件、`nginx` 反代示例或者上线 checklist，我可以继续补
