# ASR 配置指南

## 概述

Video Learner skill 现在支持两种 ASR（语音识别）引擎：

1. **阿里云 ASR**（推荐）- 速度快（2-3 秒），准确率高
2. **本地 Whisper** - 免费，但速度较慢

## 阿里云 ASR 配置

### 1. 获取 API Key

从阿里云控制台获取 API Key，或使用提供的测试 Key：
```
your_aliyun_api_key
```

### 2. 设置环境变量

```bash
# 选择 ASR 引擎
export ASR_ENGINE="aliyun"

# 设置 API Key
export ALIYUN_ASR_API_KEY="your_aliyun_api_key"

# 选择模型（可选）
export ASR_MODEL="fun-asr-mtl"  # 默认模型

# 设置超时时间（可选）
export ASR_TIMEOUT="60"  # 默认 60 秒
```

### 3. 可用模型

- `fun-asr-mtl` - 多语言模型（默认，推荐）
- `paraformer-realtime-8k-v1` - 8k 采样率实时模型
- `paraformer-realtime-16k-v1` - 16k 采样率实时模型

## 本地 Whisper 配置

### 1. 安装 Whisper

```bash
pip install openai-whisper
```

### 2. 设置环境变量

```bash
# 选择 ASR 引擎
export ASR_ENGINE="whisper"

# 选择模型（可选）
export WHISPER_MODEL="base"  # 默认模型
```

### 3. 可用模型

- `tiny` - 最快，准确率低
- `base` - 平衡（默认）
- `small` - 较好
- `medium` - 更好
- `large` - 最好，但最慢

## 使用方法

### 命令行使用

```bash
# 使用阿里云 ASR
python3 scripts/asr_router.py \
  --engine aliyun \
  --api-key "your_aliyun_api_key" \
  --model fun-asr-mtl \
  --output transcript.txt \
  audio.m4a

# 使用本地 Whisper
python3 scripts/asr_router.py \
  --engine whisper \
  --whisper-model base \
  --output transcript.txt \
  audio.m4a
```

### 在脚本中使用

#### video_with_feishu.sh

```bash
# 设置环境变量
export ASR_ENGINE="aliyun"
export ALIYUN_ASR_API_KEY="your_aliyun_api_key"

# 运行脚本
./scripts/video_with_feishu.sh "https://www.bilibili.com/video/BVxxxxx"
```

#### process_douyin.sh

```bash
# 设置环境变量
export ASR_ENGINE="aliyun"
export ALIYUN_ASR_API_KEY="your_aliyun_api_key"

# 运行脚本
./scripts/process_douyin.sh "https://www.douyin.com/video/1234567890"
```

## 测试 ASR

```bash
# 测试阿里云 ASR（使用 5 秒测试音频）
./scripts/test_asr.sh

# 测试自定义音频文件
./scripts/test_asr.sh /path/to/audio.m4a
```

## 性能对比

| 引擎 | 速度 | 准确率 | 成本 | 推荐场景 |
|------|------|--------|------|----------|
| 阿里云 ASR | ⚡⚡⚡ (2-3s) | 高 | 付费（少量） | 生产环境、大量视频 |
| 本地 Whisper | ⚡ (30-60s) | 中-高 | 免费 | 测试、个人使用 |

## 故障排除

### 阿里云 ASR 错误

1. **API Key 无效**
   ```
   错误：API 调用失败 (HTTP 401)
   解决：检查 ALIYUN_ASR_API_KEY 是否正确
   ```

2. **超时错误**
   ```
   错误：转录超时（60秒）
   解决：增加 ASR_TIMEOUT 环境变量值
   ```

3. **网络错误**
   ```
   错误：连接失败
   解决：检查网络连接，确保可以访问阿里云 API
   ```

### Whisper 错误

1. **模型下载慢**
   ```
   解决：使用较小的模型（tiny/base），或手动下载模型
   ```

2. **内存不足**
   ```
   解决：使用较小的模型（tiny/base/small）
   ```

## 最佳实践

1. **生产环境** - 使用阿里云 ASR，速度快，准确率高
2. **个人使用** - 可以使用本地 Whisper，节省成本
3. **批量处理** - 推荐阿里云 ASR，避免本地资源占用
4. **测试验证** - 使用 `test_asr.sh` 脚本验证配置

## 环境变量完整列表

```bash
# ASR 引擎选择
ASR_ENGINE="aliyun"  # 或 "whisper"

# 阿里云 ASR 配置
ALIYUN_ASR_API_KEY="your_aliyun_api_key"
ASR_MODEL="fun-asr-mtl"
ASR_TIMEOUT="60"

# Whisper 配置（仅当 ASR_ENGINE=whisper 时使用）
WHISPER_MODEL="base"

# 飞书配置
FEISHU_SPACE_ID="your_space_id"
FEISHU_PARENT_TOKEN="your_parent_token"
```

## 更多信息

- [阿里云 ASR 文档](https://help.aliyun.com/product/30413.html)
- [OpenAI Whisper 文档](https://github.com/openai/whisper)
- [Video Learner Skill 文档](./SKILL.md)
