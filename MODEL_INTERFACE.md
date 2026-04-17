# LocalVidRen 模型接口开发文档

## 概述

本文档介绍如何为 LocalVidRen 添加自定义 AI 模型。

## 模型接口设计

LocalVidRen 使用统一的抽象模型接口，所有模型都实现相同的方法。

### 核心接口

#### 1. 音频模型接口 (BaseAudioModel)

```python
class BaseAudioModel(ABC):
    """语音识别基类"""
    
    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """识别音频内容"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """获取模型信息"""
        pass
    
    def cleanup(self):
        """释放模型资源"""
        pass
```

#### 2. 视觉模型接口 (BaseVisualModel)

```python
class BaseVisualModel(ABC):
    """视觉分析基类"""
    
    @abstractmethod
    def analyze(self, image_path: str) -> str:
        """分析图像内容"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """获取模型信息"""
        pass
    
    def cleanup(self):
        """释放模型资源"""
        pass
```

#### 3. 视频分析器接口 (BaseVideoModel)

```python
class BaseVideoModel(ABC):
    """视频分析基类 - 整合音频和视觉"""
    
    @abstractmethod
    def analyze(self, video_path: str, config: Dict[str, Any]) -> AnalysisResult:
        """分析视频并生成内容总结"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """获取模型信息"""
        pass
    
    def cleanup(self):
        """释放模型资源"""
        pass
```

## 添加自定义模型步骤

### 步骤 1: 创建模型类

创建新文件 `src/custom_models.py`：

```python
from src.ai_models import BaseAudioModel, BaseVisualModel
from typing import Dict, Any

class MyCustomAudioModel(BaseAudioModel):
    """自定义音频模型"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # 初始化模型资源
    
    def transcribe(self, audio_path: str) -> str:
        """实现语音识别逻辑"""
        # 你的代码
        return "识别结果"
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "name": "My Custom Audio Model",
            "version": "1.0"
        }
    
    def cleanup(self):
        """释放资源"""
        pass


class MyCustomVisualModel(BaseVisualModel):
    """自定义视觉模型"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # 初始化模型资源
    
    def analyze(self, image_path: str) -> str:
        """实现视觉分析逻辑"""
        # 你的代码
        return "分析结果"
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "name": "My Custom Visual Model",
            "version": "1.0"
        }
    
    def cleanup(self):
        """释放资源"""
        pass
```

### 步骤 2: 注册模型

在 `src/ai_models.py` 中添加导入和注册：

```python
from src.custom_models import MyCustomAudioModel, MyCustomVisualModel

# 在配置加载时自动注册
MODEL_REGISTRY = {
    "audio": {
        "faster-whisper": FasterWhisperModel,
        "custom-audio": MyCustomAudioModel,
    },
    "visual": {
        "llama-cpp": LlamaCppVisualModel,
        "openai-compatible": OpenAICompatibleModel,
        "custom-visual": MyCustomVisualModel,
    }
}
```

### 步骤 3: 配置使用

在 `config/config.yaml` 中配置：

```yaml
model:
  audio_model:
    type: custom-audio
    config:
      # 你的自定义配置
      param1: value1
  
  visual_model:
    type: custom-visual
    config:
      # 你的自定义配置
      param2: value2
```

## 示例：添加 Whisper 模型

```python
from src.ai_models import BaseAudioModel
import whisper

class WhisperAudioModel(BaseAudioModel):
    """Whisper 语音识别模型"""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None
    
    def _load_model(self):
        if self._model is None:
            self._model = whisper.load_model(self.model_size)
    
    def transcribe(self, audio_path: str) -> str:
        self._load_model()
        result = self._model.transcribe(audio_path)
        return result["text"]
    
    def get_model_info(self) -> Dict[str, str]:
        return {
            "name": "Whisper",
            "size": self.model_size
        }
    
    def cleanup(self):
        if self._model is not None:
            del self._model
            self._model = None
```

## 示例：添加 HuggingFace 模型

```python
from src.ai_models import BaseVisualModel
from transformers import AutoProcessor, AutoModelForVision2Seq

class HuggingFaceVisualModel(BaseVisualModel):
    """HuggingFace 多模态模型"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._processor = None
        self._model = None
    
    def _load_model(self):
        if self._processor is None:
            self._processor = AutoProcessor.from_pretrained(self.model_name)
            self._model = AutoModelForVision2Seq.from_pretrained(
                self.model_name, 
                torch_dtype="auto",
                device_map="auto"
            )
    
    def analyze(self, image_path: str) -> str:
        self._load_model()
        
        # 处理图像
        prompts = ["请描述这张图片"]
        inputs = self._processor(
            images=[image_path],
            text=prompts,
            return_tensors="pt",
            padding=True
        ).to(self._model.device)
        
        # 生成描述
        generated_ids = self._model.generate(**inputs, max_new_tokens=100)
        generated_text = self._processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]
        
        return generated_text
    
    def get_model_info(self) -> Dict[str, str]:
        return {"name": "HuggingFace", "model": self.model_name}
    
    def cleanup(self):
        if self._model is not None:
            del self._model
            del self._processor
            self._model = None
            self._processor = None
```

## 调试技巧

1. **启用详细日志**：
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **测试模型加载**：
   ```python
   from src.ai_models import FasterWhisperModel
   
   model = FasterWhisperModel()
   print(model.get_model_info())
   ```

3. **性能测试**：
   ```python
   import time
   
   start = time.time()
   result = model.transcribe("test.wav")
   print(f"耗时：{time.time() - start:.2f}秒")
   ```

## 注意事项

1. **资源管理**：务必实现 `cleanup()` 方法释放资源
2. **错误处理**：添加适当的异常处理
3. **线程安全**：确保模型在多线程环境下安全
4. **内存优化**：避免内存泄漏，及时释放不用的资源

## 参考资源

- [faster-whisper 文档](https://github.com/guillaumekln/faster-whisper)
- [llama-cpp-python 文档](https://github.com/abetlen/llama-cpp-python)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
