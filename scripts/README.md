# 数据库初始化脚本

## MySQL 初始化

### 方式一：使用命令行工具

```bash
# 使用 root 用户初始化
mysql -u root -p < scripts/init_db.sql

# 或指定 host
mysql -h localhost -u root -p123456 < scripts/init_db.sql
```

### 方式二：应用自动初始化

设置环境变量启用 MySQL：

```bash
# Windows PowerShell
$env:USE_MYSQL="true"
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="123456"
$env:MYSQL_DATABASE="qrc_session"
python main.py

# Linux/Mac
export USE_MYSQL=true
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
export MYSQL_DATABASE=qrc_session
python main.py
```

应用启动时会自动创建表结构（如果不存在）。

## 配置说明

在 `src/config/config.py` 中修改 MySQL 配置：

```python
MYSQL_HOST: str = "localhost"
MYSQL_PORT: int = 3306
MYSQL_USER: str = "root"
MYSQL_PASSWORD: str = "123456"
MYSQL_DATABASE: str = "qrc_session"
USE_MYSQL: bool = False  # 默认使用内存存储
```

## 验证安装

```bash
# 连接到 MySQL 并检查表
mysql -u root -p -e "USE qrc_session; SHOW TABLES;"
```

应该看到：
```
+----------------------+
| Tables_in_qrc_session |
+----------------------+
| sessions             |
| turns                |
+----------------------+
```
