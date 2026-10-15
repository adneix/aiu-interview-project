# AIU 创智部二面任务

## 一. 大模型

1.大模型的部署

使用本地 Ollama 部署 Qwen2.5 模型

2.智能体的搭建

使用 Docker Compose部署dify

应用形式为web，具体结合下文的项目

## 二. yolo

跑通过程在文件yolo_demo中

接入了上文的web中

## 三. 测试 harness

后端通过 `create_app()` 创建应用，通过 `get_model()` 提供 YOLO 模型。正常运行时使用真实模型；测试时通过 FastAPI 的依赖覆盖机制换成 Mock 模型，返回预设的识别结果。
测试会在内存中生成小图片，再通过 TestClient 请求真实的 `/detect` 路由。因此可以检查上传、图片解析、类别去重和返回数据，无需启动外部服务器、加载真实权重或连接 Dify。
```text
运行 harness → 发现测试 → 每个用例在独立子进程执行                             
↓                 
模拟 YOLO + 请求 /detect + 校验结果                             
↓                    
终端摘要 + JSON / JUnit 报告
```
### 当前测试范围
| 用例     | 检查内容                 |
| ------ | -------------------- |
| 重复识别类别 | 返回去重后的物品清单，并保持首次出现顺序 |
| 无识别结果  | 返回空清单，数量为 0          |
| 无效图片   | 返回 HTTP 400，不执行推理    |
| 空文件    | 返回 HTTP 400，不执行推理    |
| 缺少上传文件 | 返回 HTTP 422，不执行推理    |
| 推理异常   | 返回 HTTP 500          |
这 6 个用例已在本机验证通过，同时验证了超时处理和报告生成。测试使用模拟模型，不能证明真实 YOLO 的识别精度、Dify 的连通性或网页完整流程正常。
### 运行测试
在项目根目录的 Windows CMD 中执行：
```bat
backend\venv\Scripts\python.exe scripts\run_tests.py
```
在 PowerShell 中可使用：
```powershell
.\backend\venv\Scripts\python.exe scripts/run_tests.py
```
可选参数示例：
```bat
backend\venv\Scripts\python.exe scripts\run_tests.py --pattern test_detect.py --timeout 10
```
默认每个测试最多运行 30 秒，不自动重试。退出码为：通过返回 `0`；失败、异常或超时返回 `1`；配置或测试发现错误返回 `2`。
报告位置：
- `reports/results.json`：各用例状态、耗时、日志和错误详情。
- `reports/junit.xml`：便于测试工具或 CI 读取的报告；当前尚未配置 CI 工作流。
新增测试放在 `backend/tests/test_*.py` 中。测试模块顶层应避免阻塞操作，因为发现用例时会导入模块。当前超时会终止对应测试进程；以后若用例启动额外子进程，还需补充进程树清理机制。（此部分均由ai完成）

## 四. 创意作品：桌面整理助手

### 基础介绍

用户在网页中上传图片，yolo识别物品发给网页连接dify中的智能体，智能体配备上面的大模型，结合自身身份给出回复传到网页中

### 打开方式

1 启动 YOLO 后端

cmd窗口输入cd C:\Users\27818\Desktop\AI_Project\backend

依次输入venv\Scripts\activate  

python main.py

2 启动 Vue 前端

cmd窗口输入cd C:\Users\27818\Desktop\AI_Project\frontend

npm run dev

3 启动dify

WSL终端 cd /mnt/c/Users/27818/dify/docker

docker compose up -d

docker compose ps

4 进入网页

http://localhost:5173/

## 五. 注意事项
文件不包含venv 和 node_modules

重现项目还需准备.env 文件来填入 Dify 的 API 密钥

ollama还需配置环境变量以供 Dify 访问

（代码均由ai完成，本人目前不会写代码，还在学习中，思路结合ai和网课学习）


