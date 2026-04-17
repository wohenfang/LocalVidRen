"""
AI 模型接口抽象层
提供统一的模型接口，支持本地模型和 API 模型
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """视频分析结果"""
    audio_transcript: str  # 语音识别结果
    visual_description: str  # 画面描述
    summary: str  # 最终内容总结
    key_frames: List[str] = None  # 关键帧路径列表
    processing_time: float = 0  # 处理耗时（秒）

    def __post_init__(self):
        if self.key_frames is None:
            self.key_frames = []


class BaseVideoModel(ABC):
    """视频分析基类 - 所有视频分析模型必须继承此类"""

    @abstractmethod
    def analyze(self, video_path: str, config: Dict[str, Any]) -> AnalysisResult:
        """
        分析视频并生成内容总结

        Args:
            video_path: 视频文件路径
            config: 分析配置（关键帧数量、总结长度等）

        Returns:
            AnalysisResult: 分析结果
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """获取模型信息"""
        pass

    def cleanup(self):
        """释放模型资源，子类可重写"""
        pass


class BaseAudioModel(ABC):
    """语音识别基类 - 所有语音识别模型必须继承此类"""

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """
        识别音频内容

        Args:
            audio_path: 音频文件路径

        Returns:
            str: 识别的文本内容
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """获取模型信息"""
        pass

    def cleanup(self):
        """释放模型资源"""
        pass


class BaseVisualModel(ABC):
    """视觉分析基类 - 所有视觉分析模型必须继承此类"""

    @abstractmethod
    def analyze(self, image_path: str) -> str:
        """
        分析图像内容

        Args:
            image_path: 图像文件路径

        Returns:
            str: 图像描述
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """获取模型信息"""
        pass

    def cleanup(self):
        """释放模型资源"""
        pass


# ============================================================================
# 本地语音识别模型 - faster-whisper
# ============================================================================

class FasterWhisperModel(BaseAudioModel):
    """faster-whisper 语音识别模型"""

    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        初始化 faster-whisper 模型

        Args:
            model_size: 模型大小 (tiny, base, small, medium)
            device: 运行设备 (cpu, cuda, auto)
        """
        self.model_size = model_size
        self.device = device
        self._model = None
        logger.info(f"初始化 faster-whisper 模型：{model_size}, 设备：{device}")

    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type="float16" if self.device == "cuda" else "int8"
                )
                logger.info("faster-whisper 模型加载成功")
            except Exception as e:
                logger.error(f"加载 faster-whisper 模型失败：{e}")
                raise

    def transcribe(self, audio_path: str) -> str:
        """识别音频内容"""
        self._load_model()
        try:
            segments, info = self._model.transcribe(audio_path)
            transcript = " ".join(seg.text for seg in segments)
            logger.info(f"语音识别完成：{len(transcript)} 字符")
            return transcript
        except Exception as e:
            logger.error(f"语音识别失败：{e}")
            return ""

    def get_model_info(self) -> Dict[str, str]:
        return {
            "name": "faster-whisper",
            "size": self.model_size,
            "device": self.device
        }

    def cleanup(self):
        """释放模型资源"""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("faster-whisper 模型资源已释放")


# ============================================================================
# 本地多模态模型 - llama-cpp-python
# ============================================================================

class LlamaCppVisualModel(BaseVisualModel):
    """llama-cpp-python 多模态视觉分析模型"""

    def __init__(self, model_path: str, device: str = "auto", n_ctx: int = 2048):
        """
        初始化 llama-cpp-python 模型

        Args:
            model_path: GGUF 模型文件路径
            device: 运行设备 (cpu, cuda, auto)
            n_ctx: 上下文长度
        """
        self.model_path = model_path
        self.device = device
        self.n_ctx = n_ctx
        self._model = None
        logger.info(f"初始化 llama-cpp-python 模型：{model_path}")

    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from llama_cpp import Llama
                self._model = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_gpu_layers=-1 if self.device == "cuda" else 0,
                    verbose=False
                )
                logger.info("llama-cpp-python 模型加载成功")
            except Exception as e:
                logger.error(f"加载 llama-cpp-python 模型失败：{e}")
                raise

    def analyze(self, image_path: str) -> str:
        """分析图像内容"""
        self._load_model()
        try:
            # 构建提示词
            prompt = f"""请详细描述这张图片的内容。包括：
- 场景描述（在哪里）
- 主要人物或物体
- 正在发生的事件
- 任何可见的文字
请用简洁的中文描述，100 字以内。

图片路径：{image_path}

描述："""

            output = self._model(
                prompt,
                max_tokens=128,
                stop=["\n", "图片"],
                echo=False
            )

            result = output['choices'][0]['text'].strip()
            logger.info(f"视觉分析完成：{len(result)} 字符")
            return result
        except Exception as e:
            logger.error(f"视觉分析失败：{e}")
            return ""

    def get_model_info(self) -> Dict[str, str]:
        return {
            "name": "llama-cpp-python",
            "path": self.model_path,
            "device": self.device
        }

    def cleanup(self):
        """释放模型资源"""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("llama-cpp-python 模型资源已释放")


# ============================================================================
# API 模型 - OpenAI 兼容接口
# ============================================================================

class OpenAICompatibleModel(BaseVisualModel):
    """OpenAI 兼容的多模态 API 模型"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str = "gpt-4v",
        timeout: int = 60
    ):
        """
        初始化 OpenAI 兼容模型

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model_name: 模型名称
            timeout: 超时时间（秒）
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout
        logger.info(f"初始化 OpenAI 兼容模型：{model_name}")

    def analyze(self, image_path: str) -> str:
        """分析图像内容"""
        try:
            import base64
            import requests

            # 读取并编码图片
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            # 构建请求
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "请详细描述这张图片的内容。包括场景、人物、事件和可见文字。用简洁的中文描述，100 字以内。"
                            }
                        ]
                    }
                ],
                "max_tokens": 200
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()['choices'][0]['message']['content']
                logger.info(f"API 视觉分析完成：{len(result)} 字符")
                return result
            else:
                logger.error(f"API 请求失败：{response.status_code} {response.text}")
                return ""

        except Exception as e:
            logger.error(f"视觉分析失败：{e}")
            return ""

    def get_model_info(self) -> Dict[str, str]:
        return {
            "name": "OpenAI Compatible",
            "model": self.model_name,
            "url": self.base_url
        }


# ============================================================================
# 内容总结模型 - 整合语音和视觉结果
# ============================================================================

class SummaryModel(BaseVisualModel):
    """内容总结生成模型"""

    def __init__(self, model: BaseVisualModel):
        """
        初始化总结模型

        Args:
            model: 用于生成总结的视觉模型
        """
        self.model = model
        logger.info("初始化内容总结模型")

    def generate_summary(
        self,
        transcript: str,
        visual_description: str,
        config: Dict[str, Any]
    ) -> str:
        """
        生成内容总结

        Args:
            transcript: 语音识别结果
            visual_description: 视觉描述
            config: 总结配置（长度、风格等）

        Returns:
            str: 内容总结
        """
        try:
            # 根据配置生成总结
            length = config.get("summary_length", "short")
            style = config.get("summary_style", "concise")

            # 构建提示词
            prompt = self._build_summary_prompt(transcript, visual_description, length, style)

            # 调用模型生成总结
            summary = self.model.analyze(prompt)
            return summary

        except Exception as e:
            logger.error(f"生成总结失败：{e}")
            return "视频内容分析中..."

    def _build_summary_prompt(
        self,
        transcript: str,
        visual: str,
        length: str,
        style: str
    ) -> str:
        """构建总结提示词"""

        length_desc = {
            "short": "10-15 字",
            "medium": "15-25 字",
            "long": "25-40 字"
        }.get(length, "10-20 字")

        style_desc = {
            "concise": "简洁描述型",
            "event": "事件概括型",
            "keyword": "关键词型"
        }.get(style, "简洁描述型")

        return f"""根据以下视频内容，生成一个{length_desc}的{style_desc}总结：

【语音识别内容】：
{transcript[:500]}...

【画面描述】：
{visual}

要求：
1. 以语音识别内容为主要依据
2. 画面描述作为补充
3. {style_desc.replace('型', '')}
4. {length_desc}

总结："""

    def get_model_info(self) -> Dict[str, str]:
        return self.model.get_model_info()

    def cleanup(self):
        """释放模型资源"""
        if hasattr(self.model, 'cleanup'):
            self.model.cleanup()


# ============================================================================
# 视频分析器 - 整合所有组件
# ============================================================================

class VideoAnalyzer:
    """视频分析器 - 整合语音识别、视觉分析和内容总结"""

    def __init__(
        self,
        audio_model: BaseAudioModel,
        visual_model: BaseVisualModel,
        summary_config: Dict[str, Any] = None
    ):
        """
        初始化视频分析器

        Args:
            audio_model: 语音识别模型
            visual_model: 视觉分析/总结模型
            summary_config: 总结配置
        """
        self.audio_model = audio_model
        self.visual_model = visual_model
        self.summary_config = summary_config or {
            "summary_length": "short",
            "summary_style": "concise"
        }
        logger.info("视频分析器初始化完成")

    def analyze(
        self,
        video_path: str,
        config: Dict[str, Any] = None
    ) -> AnalysisResult:
        """
        分析视频

        Args:
            video_path: 视频路径
            config: 分析配置（关键帧数量等）

        Returns:
            AnalysisResult: 分析结果
        """
        import time
        start_time = time.time()
        config = config or {}

        try:
            # 1. 优先处理音频（语音识别）
            logger.info(f"开始语音识别：{video_path}")
            audio_transcript = self.audio_model.transcribe(video_path)

            # 2. 提取关键帧
            key_frames = self._extract_keyframes(video_path, config.get("keyframe_count", 3))

            # 3. 分析关键帧（视觉）
            visual_description = ""
            for kf in key_frames:
                desc = self.visual_model.analyze(kf)
                visual_description += desc + " "

            # 4. 生成内容总结
            summary = self._generate_summary(audio_transcript, visual_description)

            # 计算耗时
            processing_time = time.time() - start_time

            logger.info(f"视频分析完成：{processing_time:.2f}秒")

            return AnalysisResult(
                audio_transcript=audio_transcript,
                visual_description=visual_description.strip(),
                summary=summary,
                key_frames=key_frames,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"视频分析失败：{e}")
            return AnalysisResult(
                audio_transcript="",
                visual_description="",
                summary="分析失败",
                processing_time=time.time() - start_time
            )

    def _extract_keyframes(self, video_path: str, count: int) -> List[str]:
        """提取关键帧"""
        from src.video_processor import VideoProcessor
        processor = VideoProcessor()
        return processor.extract_keyframes(video_path, count)

    def _generate_summary(self, transcript: str, visual: str) -> str:
        """生成内容总结"""
        # 如果语音识别有结果，优先使用
        if transcript and len(transcript.strip()) > 5:
            # 截取关键信息
            summary = transcript[:20] if len(transcript) > 20 else transcript
            return summary.strip()

        # 否则使用视觉描述
        return visual[:20] if len(visual) > 20 else visual

    def get_model_info(self) -> Dict[str, str]:
        return {
            "audio": self.audio_model.get_model_info(),
            "visual": self.visual_model.get_model_info()
        }

    def cleanup(self):
        """释放所有模型资源"""
        logger.info("释放所有模型资源")
        self.audio_model.cleanup()
        self.visual_model.cleanup()
