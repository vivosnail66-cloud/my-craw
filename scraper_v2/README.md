# FiverrSohimiScraper

## 运行环境

- Python 3.10 以上
- 安装 VS Code

具体 Google 一下。

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

将 `config.txt` 重命名为 `config.ini`，并修改里面的配置。

```ini
[RUNNING]
USE_PROXY = False
PROXY_TYPE = PROXY_ADDR
PAGE_WAITING_TIME = 1
THREADS = 1
RETRY_TIMES = 5
```

基本可以不用修改。

## 运行

本程序有 `自动` 和 `手动` 两种运行方式。

### 自动运行

```bash
python main.py --mode auto
```

### 手动运行

#### 1. 获取所有的 category

```bash
python main.py --mode task
```

#### 2. 获取所有的商品

```bash
python main.py --mode listing
```

#### 3. 获取所有的商品详情

```bash
python main.py --mode detail
```

#### 4. 获取所有的商品评论

```bash
python main.py --mode review
```

#### 5. 下载图片

```bash
python main.py --mode image
```

#### 6. 导出数据

```bash
python main.py --mode export
```

## 数据

数据会保存在 `data` 目录下，分为 `csv` 和 `图片` 两种格式。

分别存在 `data/output` 和 `data/media` 目录下。

## 说明

我已经按照你需要的更是更新了数据里面的图片 URL，需要你将图片上传到你的服务器上。

output 里面有两种格式，一种是完全按照你的要求的，一种我加了一些字段，你可以根据自己的需要选择。