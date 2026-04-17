"""
视频处理模块
使用 FFmpeg 进行视频处理（音频提取、关键帧提取等）
"""

import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import ffmpeg

logger = logging.getLogger(__name__)

# Windows 支持的短视频格式
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm'}

# Windows 文件名非法字符
INVALID_CHARS = '<>:|"？*\\'


class VideoProcessor:
    """视频处理器 - 提供视频处理相关功能"""

    def __init__(self, temp_dir: Optional[str] = None):
        """
        初始化视频处理器

        Args:
            temp_dir: 临时文件目录，默认为系统 TEMP 目录
        """
        if temp_dir is None:
            temp_dir = os.path.join(os.environ.get('TEMP', ''), 'LocalVidRen')

        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"视频处理器初始化，临时目录：{temp_dir}")

    def get_video_info(self, video_path: str) -> dict:
        """
        获取视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            dict: 视频信息（大小、时长、分辨率等）
        """
        try:
            # 使用 ffprobe 获取视频信息
            probe = ffmpeg.probe(video_path, cmd='ffprobe')

            # 查找视频流
            video_stream = None
            for stream in probe['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break

            if not video_stream:
                return {"error": "未找到视频流"}

            # 解析时长
            duration = float(probe['format']['duration'])

            # 解析分辨率
            width = int(video_stream['width'])
            height = int(video_stream['height'])

            # 解析文件大小
            file_size = int(probe['format']['size'])

            return {
                "path": video_path,
                "filename": os.path.basename(video_path),
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "duration": duration,
                "duration_str": self._format_duration(duration),
                "width": width,
                "height": height,
                "resolution": f"{width}x{height}"
            }

        except Exception as e:
            logger.error(f"获取视频信息失败：{e}")
            return {"error": str(e)}

    def extract_audio(self, video_path: str) -> str:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径

        Returns:
            str: 提取的音频文件路径
        """
        try:
            output_path = os.path.join(
                self.temp_dir,
                f"{Path(video_path).stem}_audio.wav"
            )

            # 使用 ffmpeg 提取音频
            (
                ffmpeg
                .input(video_path)
                .output(output_path, acodec='pcm_s16le', ar='16000', ac=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            logger.info(f"音频提取完成：{output_path}")
            return output_path

        except Exception as e:
            logger.error(f"音频提取失败：{e}")
            # 如果失败，返回原视频路径（faster-whisper 可以直接处理视频）
            return video_path

    def extract_keyframes(
        self,
        video_path: str,
        count: int = 3,
        output_dir: Optional[str] = None
    ) -> List[str]:
        """
        从视频中提取关键帧

        Args:
            video_path: 视频文件路径
            count: 提取的关键帧数量
            output_dir: 输出目录，默认为临时目录

        Returns:
            List[str]: 关键帧文件路径列表
        """
        if output_dir is None:
            output_dir = self.temp_dir

        os.makedirs(output_dir, exist_ok=True)

        try:
            # 获取视频时长
            info = self.get_video_info(video_path)
            duration = info.get('duration', 0)

            if duration <= 0:
                logger.warning(f"视频时长无效：{video_path}")
                return []

            # 计算帧间隔（针对短视频优化：每 2-3 秒 1 帧）
            if duration <= 60:  # 1 分钟以内
                interval = max(2, int(duration / count))
            else:
                interval = 3

            logger.info(f"提取 {count} 个关键帧，间隔：{interval}秒")

            keyframe_paths = []

            # 使用 ffmpeg 提取关键帧
            for i in range(count):
                # 计算当前帧的时间点
                timestamp = (duration / count) * i

                output_path = os.path.join(
                    output_dir,
                    f"{Path(video_path).stem}_kf_{i+1:02d}.jpg"
                )

                # 在指定时间点提取一帧
                (
                    ffmpeg
                    .input(video_path, ss=timestamp)
                    .output(
                        output_path,
                        vframes=1,
                        vcodec='mjpeg',
                        qscale=2
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )

                if os.path.exists(output_path):
                    keyframe_paths.append(output_path)
                else:
                    logger.warning(f"关键帧提取失败：{output_path}")

            logger.info(f"关键帧提取完成：{len(keyframe_paths)} 张")
            return keyframe_paths

        except Exception as e:
            logger.error(f"关键帧提取失败：{e}")
            return []

    def extract_audio_only(self, video_path: str) -> str:
        """
        提取音频（针对 faster-whisper 优化）

        Args:
            video_path: 视频文件路径

        Returns:
            str: 音频文件路径
        """
        return self.extract_audio(video_path)

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                logger.info(f"临时文件已清理：{self.temp_dir}")
        except Exception as e:
            logger.error(f"清理临时文件失败：{e}")

    def _format_duration(self, seconds: float) -> str:
        """格式化时长为 MM:SS 格式"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"


class VideoScanner:
    """视频扫描器 - 扫描文件夹中的视频文件"""

    def __init__(self, max_size_mb: float = 500):
        """
        初始化视频扫描器

        Args:
            max_size_mb: 最大文件大小（MB），默认 500M
        """
        self.max_size_mb = max_size_mb
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        logger.info(f"视频扫描器初始化，最大文件大小：{max_size_mb}MB")

    def scan_folder(
        self,
        folder_path: str,
        recursive: bool = True
    ) -> List[dict]:
        """
        扫描文件夹中的视频文件

        Args:
            folder_path: 文件夹路径
            recursive: 是否递归扫描子文件夹

        Returns:
            List[dict]: 视频文件信息列表
        """
        videos = []
        processor = VideoProcessor()

        try:
            path = Path(folder_path)

            if not path.exists():
                logger.warning(f"文件夹不存在：{folder_path}")
                return videos

            # 收集所有视频文件
            if recursive:
                files = path.rglob("*")
            else:
                files = path.glob("*")

            for file in files:
                if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:
                    # 检查文件大小
                    if file.stat().st_size > self.max_size_bytes:
                        logger.debug(f"跳过超过限制的文件：{file.name}")
                        continue

                    # 获取视频信息
                    info = processor.get_video_info(str(file))
                    if "error" not in info:
                        info["status"] = "pending"  # 待处理
                        info["new_filename"] = None
                        videos.append(info)

            logger.info(f"扫描完成：找到 {len(videos)} 个视频")
            return videos

        except Exception as e:
            logger.error(f"扫描文件夹失败：{e}")
            return videos

    def get_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希值（用于识别重复文件）

        Args:
            file_path: 文件路径

        Returns:
            str: 文件哈希值
        """
        import hashlib

        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                # 分块读取，避免大文件内存占用
                for chunk in iter(lambda: f.read(65536), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败：{e}")
            return ""


class VideoRenamer:
    """视频重命名器"""

    # Windows 文件名非法字符替换映射
    INVALID_CHAR_MAP = {
        c: '' for c in INVALID_CHARS
    }

    def __init__(self):
        """初始化重命名器"""
        self.history = []  # 重命名历史记录
        self.max_history = 50  # 最多保留 50 条记录
        logger.info("视频重命名器初始化完成")

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除 Windows 非法字符

        Args:
            filename: 原始文件名

        Returns:
            str: 清理后的文件名
        """
        result = filename

        # 替换非法字符
        for char, replacement in self.INVALID_CHAR_MAP.items():
            result = result.replace(char, replacement)

        # 移除首尾空格和点
        result = result.strip(' .')

        # 限制文件名长度（Windows 最大 255 字符）
        if len(result) > 100:
            result = result[:100]

        return result if result else "视频"

    def generate_new_filename(
        self,
        original_path: str,
        summary: str,
        template: str = "[summary].[ext]",
        add_date: bool = False
    ) -> str:
        """
        生成新文件名

        Args:
            original_path: 原始文件路径
            summary: 内容总结
            template: 文件名模板
            add_date: 是否添加日期

        Returns:
            str: 新文件名
        """
        import datetime

        path = Path(original_path)
        ext = path.suffix.lower()
        original_name = path.stem

        # 清理总结作为文件名
        clean_summary = self.sanitize_filename(summary)

        # 获取当前日期
        date_str = datetime.datetime.now().strftime("%Y%m%d")

        # 根据模板生成文件名
        if template == "[date]_[summary].[ext]":
            new_name = f"{date_str}_{clean_summary}"
        elif template == "[prefix]_[summary].[ext]":
            # 取原文件名前 10 个字符作为前缀
            prefix = self.sanitize_filename(original_name[:10])
            new_name = f"{prefix}_{clean_summary}"
        else:
            # 默认模板：[summary].[ext]
            new_name = clean_summary

        return f"{new_name}{ext}"

    def check_conflict(self, folder: str, filename: str) -> str:
        """
        检查文件名冲突，如有冲突则添加后缀

        Args:
            folder: 目标文件夹
            filename: 文件名

        Returns:
            str: 最终文件名（如有冲突已处理）
        """
        target_path = os.path.join(folder, filename)

        if not os.path.exists(target_path):
            return filename

        # 文件名冲突，添加后缀
        path = Path(filename)
        base = path.stem
        ext = path.suffix

        counter = 1
        while True:
            new_filename = f"{base}({counter}){ext}"
            target_path = os.path.join(folder, new_filename)

            if not os.path.exists(target_path):
                logger.info(f"文件名冲突，使用新名称：{new_filename}")
                return new_filename

            counter += 1

            # 防止无限循环
            if counter > 999:
                return filename

    def rename_video(
        self,
        video_info: dict,
        summary: str,
        template: str = "[summary].[ext]",
        add_date: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        重命名视频文件

        Args:
            video_info: 视频信息字典
            summary: 内容总结
            template: 文件名模板
            add_date: 是否添加日期

        Returns:
            Tuple[old_path, new_path]: 旧路径和新路径，失败返回 (None, None)
        """
        try:
            original_path = video_info['path']
            folder = os.path.dirname(original_path)

            # 生成新文件名
            new_filename = self.generate_new_filename(
                original_path,
                summary,
                template,
                add_date
            )

            # 检查冲突
            new_filename = self.check_conflict(folder, new_filename)

            # 生成完整新路径
            new_path = os.path.join(folder, new_filename)

            # 如果目标已存在，跳过
            if os.path.exists(new_path):
                logger.warning(f"目标文件已存在：{new_path}")
                return None, None

            # 执行重命名
            os.rename(original_path, new_path)

            # 记录历史
            self._add_history(original_path, new_path)

            logger.info(f"视频重命名：{os.path.basename(original_path)} -> {new_filename}")

            return original_path, new_path

        except Exception as e:
            logger.error(f"重命名失败：{e}")
            return None, None

    def _add_history(self, old_path: str, new_path: str):
        """添加重命名历史"""
        self.history.append({
            "old_path": old_path,
            "new_path": new_path,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })

        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def undo_last_rename(self) -> bool:
        """
        撤销最后一次重命名

        Returns:
            bool: 是否成功
        """
        if not self.history:
            logger.warning("没有可撤销的重命名记录")
            return False

        # 获取最后一条记录
        record = self.history.pop()

        try:
            # 检查新文件是否存在
            if not os.path.exists(record['new_path']):
                logger.warning(f"目标文件不存在：{record['new_path']}")
                return False

            # 撤销重命名
            os.rename(record['new_path'], record['old_path'])

            logger.info(f"撤销重命名：{os.path.basename(record['new_path'])}")
            return True

        except Exception as e:
            logger.error(f"撤销重命名失败：{e}")
            # 恢复历史记录
            self.history.append(record)
            return False

    def get_history(self) -> List[dict]:
        """获取重命名历史"""
        return self.history.copy()
