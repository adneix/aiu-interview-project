<template>
  <div class="app-container">
    <header class="header">
      <h1>🖥️ 桌面鉴定师</h1>
      <p>上传你的桌面照片，或者手动输入物品清单接受审判！</p>
    </header>

    <!-- 图片上传区域 -->
    <div class="upload-area">
      <input type="file" ref="fileInputRef" accept="image/*" @change="handleFileUpload" style="display: none;" />
      <button class="upload-btn" @click="triggerUpload" :disabled="loading">
        📷 上传桌面照片 (AI自动识别)
      </button>
      <span v-if="isUploading" class="preview-text">正在识别桌面...</span>
    </div>

    <main class="chat-box" ref="chatBoxRef">
      <div v-for="(msg, index) in messages" :key="index" :class="['message-wrapper', msg.role]">
        <div class="avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
        <div class="bubble" v-html="formatMessage(msg.content)"></div>
      </div>
      <div v-if="loading" class="message-wrapper assistant">
        <div class="avatar">🤖</div>
        <div class="bubble loading">正在扫描混沌物质...</div>
      </div>
    </main>

    <footer class="input-area">
      <input v-model="inputText" @keyup.enter="sendMessage" placeholder="也可以手动输入物品，例如：键盘、鼠标、外卖盒" :disabled="loading" />
      <button @click="sendMessage" :disabled="loading || !inputText.trim()">发送审判</button>
    </footer>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import axios from 'axios'

const inputText = ref('')
const loading = ref(false)
const isUploading = ref(false)
const messages = ref([
  { role: 'assistant', content: '你好，我是你的桌面鉴定师。点击上方按钮上传桌面照片，或者直接打字告诉我桌面上有什么，准备好接受吐槽了吗？' }
])
const chatBoxRef = ref(null)
const fileInputRef = ref(null)

const formatMessage = (text) => {
  return text.replace(/\n/g, '<br>')
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatBoxRef.value) {
    chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight
  }
}

// 触发文件选择
const triggerUpload = () => {
  fileInputRef.value.click()
}

// 核心：处理图片上传并联动 YOLO + Dify
const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  isUploading.value = true
  loading.value = true
  scrollToBottom()

  try {
    // 1. 把图片发给本地FastAPI (YOLO)
    const formData = new FormData()
    formData.append("file", file)

    messages.value.push({ role: 'user', content: '📷 [已上传桌面图片]' })

    const yoloResponse = await axios.post("http://localhost:8000/detect", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    })

    const objects = yoloResponse.data.objects // 拿到 ["键盘", "鼠标", "水杯"]

    if (objects.length === 0) {
      messages.value.push({ role: 'assistant', content: '⚠️ 未识别到任何物品，请拍清楚一点。' })
      return
    }

    // 2. 把识别的结果拼成文本发给Dify
    const promptText = `我上传了一张桌面图片，YOLO识别到的物品有：${objects.join('、')}。请开始你的鉴定。`
    
    // 在界面上显示"用户"发了识别结果
    messages.value.push({ role: 'user', content: `🔍 YOLO识别结果：${objects.join('、')}` })

    // 3. 调用Dify API
    const difyResponse = await axios.post(
      import.meta.env.VITE_DIFY_API_URL,
      { inputs: {}, query: promptText, response_mode: 'blocking', user: 'web-user-001' },
      { headers: { 'Authorization': `Bearer ${import.meta.env.VITE_DIFY_API_KEY}`, 'Content-Type': 'application/json' } }
    )

    messages.value.push({ role: 'assistant', content: difyResponse.data.answer })

  } catch (error) {
    console.error(error)
    messages.value.push({ role: 'assistant', content: '⚠️ 识别失败，请确认后端(8000端口)和Dify已启动。' })
  } finally {
    isUploading.value = false
    loading.value = false
    // 清空input，方便下次上传
    event.target.value = ''
    scrollToBottom()
  }
}

// 手动发送文本消息（保持不变）
const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const response = await axios.post(
      import.meta.env.VITE_DIFY_API_URL,
      { inputs: {}, query: text, response_mode: 'blocking', user: 'web-user-001' },
      { headers: { 'Authorization': `Bearer ${import.meta.env.VITE_DIFY_API_KEY}`, 'Content-Type': 'application/json' } }
    )
    messages.value.push({ role: 'assistant', content: response.data.answer })
  } catch (error) {
    console.error(error)
    messages.value.push({ role: 'assistant', content: '⚠️ 连接鉴定师失败，请检查Dify服务。' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
/* 新增上传区域的样式 */
.upload-area { padding: 15px; text-align: center; background: #fff; border-bottom: 1px solid #eee; }
.upload-btn { padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 1rem; transition: 0.3s; }
.upload-btn:hover { background: #218838; }
.upload-btn:disabled { background: #ccc; cursor: not-allowed; }
.preview-text { margin-left: 10px; color: #28a745; font-size: 0.9rem; }

/* 原有样式 */
.app-container { max-width: 800px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f9f9f9; }
.header { text-align: center; padding: 20px; background: #fff; box-shadow: 0 2px 10px rgba(0,0,0,0.05); z-index: 10; }
.header h1 { margin: 0; color: #333; font-size: 1.5rem; }
.header p { margin: 5px 0 0; color: #888; font-size: 0.9rem; }
.chat-box { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
.message-wrapper { display: flex; align-items: flex-start; gap: 10px; max-width: 80%; }
.message-wrapper.user { align-self: flex-end; flex-direction: row-reverse; }
.message-wrapper.assistant { align-self: flex-start; }
.avatar { width: 36px; height: 36px; background: #eee; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0; }
.message-wrapper.user .avatar { background: #007bff; color: white; }
.bubble { padding: 12px 16px; border-radius: 12px; line-height: 1.5; font-size: 0.95rem; word-break: break-word; }
.message-wrapper.assistant .bubble { background: #fff; color: #333; border: 1px solid #e0e0e0; border-top-left-radius: 2px; }
.message-wrapper.user .bubble { background: #007bff; color: white; border-top-right-radius: 2px; }
.bubble.loading { color: #999; font-style: italic; }
.input-area { padding: 20px; background: #fff; display: flex; gap: 10px; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); }
.input-area input { flex: 1; padding: 12px 16px; border: 1px solid #ddd; border-radius: 24px; outline: none; transition: 0.3s; }
.input-area input:focus { border-color: #007bff; }
.input-area button { padding: 0 24px; background: #007bff; color: white; border: none; border-radius: 24px; cursor: pointer; font-weight: bold; transition: 0.3s; }
.input-area button:hover { background: #0056b3; }
.input-area button:disabled { background: #ccc; cursor: not-allowed; }
</style>