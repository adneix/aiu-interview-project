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

## 三. 创意作品：桌面整理助手

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

5 注意事项

文件不包含venv 和 node_modules

重现项目还需准备.env 文件来填入 Dify 的 API 密钥

ollama还需配置环境变量以供 Dify 访问

（代码均由ai完成，本人目前不会写代码，还在学习中，思路结合ai和网课学习）


