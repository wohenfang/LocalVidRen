"""
配置管理模块
加载和保存配置文件
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "model": {
        "mode": "local",  # "local" or "api"
        "audio_model": {
            "type": "faster-whisper",
            "size": "base",  # tiny, base, small, medium
            "device": "auto"  # cpu, cuda, auto
        },
        "visual_model": {
            "type": "llama-cpp",  # "llama-cpp" or "openai-compatible"
            "path": "",  # GGUF 模型路径
            "device": "auto",
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4v"
        },
        "summary": {
            "length": "short",  # short, medium, long
            "style": "concise"  # concise, event, keyword
        }
    },
    "video": {
        "max_size_mb": 500,
        "keyframe_interval": 3,  # 关键帧提取间隔（秒）
        "formats": [".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm"]
    },
    "naming": {
        "template": "[summary].[ext]",  # [summary], [date]_[summary], [prefix]_[summary]
        "max_history": 50
    },
    "processing": {
        "concurrency": 2,  # 并发处理数
        "max_retries": 1,  # 最大重试次数
        "skip_processed": True  # 跳过已处理视频
    },
    "monitor": {
        "folders": [],  # 监控文件夹列表
        "delay_seconds": 10,  # 监控延迟（秒）
        "recursive": True  # 是否递归子文件夹
    },
    "automation": {
        "auto_start": False,  # 开机自启动
        "minimize_to_tray": True,  # 最小化到托盘
        "shutdown_after": False,  # 处理后自动关机
        "notify": True  # 系统通知
    },
    "ui": {
        "theme": "auto",  # light, dark, auto
        "font_size": 10
    }
}


@dataclass
class Config:
    """配置类"""
    model: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["model"].copy())
    video: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["video"].copy())
    naming: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["naming"].copy())
    processing: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["processing"].copy())
    monitor: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["monitor"].copy())
    automation: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["automation"].copy())
    ui: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG["ui"].copy())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """从字典创建配置"""
        # 合并默认配置
        merged = DEFAULT_CONFIG.copy()
        for key in data:
            if key in merged and isinstance(merged[key], dict) and isinstance(data[key], dict):
                merged[key].update(data[key])
            else:
                merged[key] = data[key]

        return cls(
            model=merged["model"],
            video=merged["video"],
            naming=merged["naming"],
            processing=merged["processing"],
            monitor=merged["monitor"],
            automation=merged["automation"],
            ui=merged["ui"]
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "model": self.model,
            "video": self.video,
            "naming": self.naming,
            "processing": self.processing,
            "monitor": self.monitor,
            "automation": self.automation,
            "ui": self.ui
        }

    def save(self, path: str):
        """保存配置到文件"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)
            logger.info(f"配置已保存：{path}")
        except Exception as e:
            logger.error(f"保存配置失败：{e}")

    @classmethod
    def load(cls, path: str) -> 'Config':
        """从文件加载配置"""
        if not os.path.exists(path):
            logger.info(f"配置文件不存在，使用默认配置：{path}")
            return cls()

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            config = cls.from_dict(data)
            logger.info(f"配置已加载：{path}")
            return config
        except Exception as e:
            logger.error(f"加载配置失败：{e}，使用默认配置")
            return cls()


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置目录，默认为应用目录下的 config 文件夹
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')

        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        self.config_path = os.path.join(config_dir, 'config.yaml')
        self.config: Optional[Config] = None
        logger.info(f"配置管理器初始化，配置目录：{config_dir}")

    def get_config(self) -> Config:
        """获取配置（延迟加载）"""
        if self.config is None:
            self.config = Config.load(self.config_path)
        return self.config

    def save_config(self):
        """保存当前配置"""
        if self.config is not None:
            self.config.save(self.config_path)

    def get_audio_model_path(self) -> str:
        """获取音频模型路径（faster-whisper）"""
        # faster-whisper 会自动下载模型到~/.cache/whisper
        return ""

    def get_visual_model_path(self) -> str:
        """获取视觉模型路径"""
        return self.config.model.visual_model.get("path", "")

    def set_visual_model_path(self, path: str):
        """设置视觉模型路径"""
        self.config.model.visual_model["path"] = path
        self.save_config()

    def get_api_key(self) -> str:
        """获取 API 密钥"""
        return self.config.model.visual_model.get("api_key", "")

    def set_api_key(self, key: str):
        """设置 API 密钥"""
        self.config.model.visual_model["api_key"] = key
        self.save_config()

    def get_base_url(self) -> str:
        """获取 API 基础 URL"""
        return self.config.model.visual_model.get("base_url", "")

    def set_base_url(self, url: str):
        """设置 API 基础 URL"""
        self.config.model.visual_model["base_url"] = url
        self.save_config()

    def add_monitor_folder(self, folder: str):
        """添加监控文件夹"""
        if folder not in self.config.monitor["folders"]:
            self.config.monitor["folders"].append(folder)
            self.save_config()

    def remove_monitor_folder(self, folder: str):
        """移除监控文件夹"""
        if folder in self.config.monitor["folders"]:
            self.config.monitor["folders"].remove(folder)
            self.save_config()

    def get_monitor_folders(self) -> list:
        """获取监控文件夹列表"""
        return self.config.monitor["folders"].copy()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def init_config(config_path: str):
    """初始化配置"""
    global _config_manager
    _config_manager = ConfigManager(config_path)
