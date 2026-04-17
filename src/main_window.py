"""
主窗口模块
"""

import os
import logging
from typing import List, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QProgressBar, QMessageBox, QFileDialog, QSplitter,
    QGroupBox, QTextEdit, QTabWidget, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

from src.video_processor import VideoProcessor, VideoScanner, VideoRenamer
from src.ai_models import VideoAnalyzer, FasterWhisperModel, LlamaCppVisualModel
from src.config import ConfigManager, get_config_manager

logger = logging.getLogger(__name__)


class ProcessingThread(QThread):
    """视频处理线程"""
    progress = pyqtSignal(int, int, str)  # 当前，总数，文件名
    finished = pyqtSignal(int, int)  # 成功数，失败数
    error = pyqtSignal(str)

    def __init__(
        self,
        videos: List[dict],
        analyzer: VideoAnalyzer,
        renamer: VideoRenamer,
        config: dict
    ):
        super().__init__()
        self.videos = videos
        self.analyzer = analyzer
        self.renamer = renamer
        self.config = config
        self._cancelled = False

    def cancel(self):
        """取消处理"""
        self._cancelled = True

    def run(self):
        """执行处理"""
        success_count = 0
        fail_count = 0

        for i, video in enumerate(self.videos):
            if self._cancelled:
                logger.info("处理已取消")
                break

            # 更新进度
            filename = video.get('filename', '未知文件')
            self.progress.emit(i + 1, len(self.videos), filename)

            try:
                # 分析视频
                result = self.analyzer.analyze(video['path'], self.config)

                # 重命名
                old_path, new_path = self.renamer.rename_video(
                    video,
                    result.summary,
                    self.config.get('naming', {}).get('template', '[summary].[ext]')
                )

                if new_path:
                    success_count += 1
                    video['status'] = 'completed'
                    video['new_filename'] = os.path.basename(new_path)
                else:
                    fail_count += 1
                    video['status'] = 'failed'

            except Exception as e:
                logger.error(f"处理视频失败：{video['path']} - {e}")
                fail_count += 1
                video['status'] = 'error'
                self.error.emit(f"{filename}: {str(e)}")

        self.finished.emit(success_count, fail_count)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.config_manager = get_config_manager()
        self.config = self.config_manager.get_config()

        # 初始化组件
        self.video_processor = VideoProcessor()
        self.video_scanner = VideoScanner(
            max_size_mb=self.config.video.get('max_size_mb', 500)
        )
        self.video_renamer = VideoRenamer()

        # 初始化 AI 模型（延迟加载）
        self.analyzer: Optional[VideoAnalyzer] = None

        # 视频列表
        self.videos: List[dict] = []

        # 处理线程
        self.process_thread: Optional[ProcessingThread] = None

        # 初始化 UI
        self._init_ui()
        self._setup_signals()

        logger.info("主窗口初始化完成")

    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("LocalVidRen - 本地短视频智能重命名系统")
        self.setMinimumSize(1000, 700)

        # 中央 widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 顶部按钮区
        self._create_top_buttons(main_layout)

        # 分割器（视频列表 + 日志）
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 视频列表区
        self._create_video_list(splitter)

        # 日志区
        self._create_log_area(splitter)

        main_layout.addWidget(splitter)

        # 底部状态栏
        self._create_status_bar()

    def _create_top_buttons(self, layout: QVBoxLayout):
        """创建顶部按钮区"""
        button_group = QGroupBox("功能按钮")
        button_layout = QHBoxLayout()

        # 选择文件夹按钮
        self.btn_select_folder = QPushButton("📁 选择文件夹")
        self.btn_select_folder.clicked.connect(self._select_folder)
        self.btn_select_folder.setMinimumSize(150, 40)
        button_layout.addWidget(self.btn_select_folder)

        # 开始处理按钮
        self.btn_start = QPushButton("▶ 开始处理")
        self.btn_start.clicked.connect(self._start_processing)
        self.btn_start.setMinimumSize(150, 40)
        button_layout.addWidget(self.btn_start)

        # 停止处理按钮
        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.clicked.connect(self._stop_processing)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setMinimumSize(100, 40)
        button_layout.addWidget(self.btn_stop)

        # 设置按钮
        self.btn_settings = QPushButton("⚙ 设置")
        self.btn_settings.clicked.connect(self._open_settings)
        self.btn_settings.setMinimumSize(100, 40)
        button_layout.addWidget(self.btn_settings)

        # 清空按钮
        self.btn_clear = QPushButton("🗑 清空已处理")
        self.btn_clear.clicked.connect(self._clear_completed)
        self.btn_clear.setMinimumSize(130, 40)
        button_layout.addWidget(self.btn_clear)

        button_layout.addStretch()

        button_group.setLayout(button_layout)
        layout.addWidget(button_group)

    def _create_video_list(self, splitter: QSplitter):
        """创建视频列表区"""
        # 视频列表
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(6)
        self.video_table.setHorizontalHeaderLabels([
            "原文件名", "大小 (MB)", "时长", "状态", "新文件名", "操作"
        ])
        self.video_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.video_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.video_table.setAlternatingRowColors(True)
        self.video_table.setMinimumHeight(300)

        # 连接双击事件
        self.video_table.itemDoubleClicked.connect(self._on_video_double_clicked)

        splitter.addWidget(self.video_table)

    def _create_log_area(self, splitter: QSplitter):
        """创建日志区"""
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        splitter.addWidget(log_group)

    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()

        # 进度标签
        self.progress_label = QLabel("准备就绪")
        self.status_bar.addWidget(self.progress_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # 时间标签
        self.time_label = QLabel("已用：0:00 | 预计剩余：0:00")
        self.status_bar.addPermanentWidget(self.time_label)

    def _setup_signals(self):
        """设置信号连接"""
        if self.process_thread:
            self.process_thread.progress.connect(self._on_progress)
            self.process_thread.finished.connect(self._on_finished)
            self.process_thread.error.connect(self._on_error)

    def _log(self, message: str):
        """添加日志"""
        self.log_text.append(f"[{self._get_time()}] {message}")
        logger.info(message)

    def _get_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def _select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择视频文件夹", ""
        )

        if folder:
            self._log(f"选择文件夹：{folder}")
            self._scan_folder(folder)

    def _scan_folder(self, folder: str):
        """扫描文件夹"""
        self._log(f"开始扫描：{folder}")

        # 扫描视频
        videos = self.video_scanner.scan_folder(folder)

        if not videos:
            self._log(f"未找到视频文件")
            return

        # 添加到列表
        self.videos.extend(videos)
        self._update_video_table()

        self._log(f"扫描完成：找到 {len(videos)} 个视频")

    def _update_video_table(self):
        """更新视频表格"""
        self.video_table.setRowCount(len(self.videos))

        for i, video in enumerate(self.videos):
            # 原文件名
            self.video_table.setItem(
                i, 0,
                QTableWidgetItem(video.get('filename', ''))
            )

            # 大小
            self.video_table.setItem(
                i, 1,
                QTableWidgetItem(f"{video.get('size_mb', 0):.1f}")
            )

            # 时长
            self.video_table.setItem(
                i, 2,
                QTableWidgetItem(video.get('duration_str', ''))
            )

            # 状态
            status_item = QTableWidgetItem(video.get('status', 'pending'))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 根据状态设置颜色
            status = video.get('status', 'pending')
            if status == 'completed':
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == 'failed' or status == 'error':
                status_item.setForeground(Qt.GlobalColor.red)
            elif status == 'processing':
                status_item.setForeground(Qt.GlobalColor.darkBlue)

            self.video_table.setItem(i, 3, status_item)

            # 新文件名
            new_name = video.get('new_filename')
            if new_name:
                new_item = QTableWidgetItem(new_name)
                new_item.setFlags(new_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.video_table.setItem(i, 4, new_item)
            else:
                self.video_table.setItem(i, 4, QTableWidgetItem(""))

            # 操作列
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 0, 4, 0)

            if status == 'pending':
                btn_preview = QPushButton("预览")
                btn_preview.clicked.connect(lambda checked, idx=i: self._preview_rename(idx))
                action_layout.addWidget(btn_preview)

            action_widget.setLayout(action_layout)
            self.video_table.setCellWidget(i, 5, action_widget)

    def _start_processing(self):
        """开始处理"""
        # 初始化 AI 模型（首次处理时）
        if self.analyzer is None:
            self._init_analyzer()

        if self.analyzer is None:
            QMessageBox.critical(self, "错误", "AI 模型初始化失败，请检查配置")
            return

        # 获取待处理视频
        pending_videos = [v for v in self.videos if v.get('status') == 'pending']

        if not pending_videos:
            QMessageBox.information(self, "提示", "没有待处理的视频")
            return

        # 确认
        reply = QMessageBox.question(
            self, "确认",
            f"准备处理 {len(pending_videos)} 个视频，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 更新状态
        for video in pending_videos:
            video['status'] = 'processing'

        self._update_video_table()

        # 创建处理线程
        self.process_thread = ProcessingThread(
            videos=pending_videos,
            analyzer=self.analyzer,
            renamer=self.video_renamer,
            config=self.config.to_dict()
        )

        # 连接信号
        self.process_thread.progress.connect(self._on_progress)
        self.process_thread.finished.connect(self._on_finished)
        self.process_thread.error.connect(self._on_error)

        # 更新按钮状态
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_select_folder.setEnabled(False)

        # 启动线程
        self.process_thread.start()
        self._log("开始处理视频")

    def _stop_processing(self):
        """停止处理"""
        if self.process_thread:
            self.process_thread.cancel()
            self._log("正在停止处理...")

    def _init_analyzer(self):
        """初始化 AI 分析器"""
        try:
            model_config = self.config.model

            # 初始化音频模型
            audio_config = model_config.get('audio_model', {})
            audio_model = FasterWhisperModel(
                model_size=audio_config.get('size', 'base'),
                device=audio_config.get('device', 'auto')
            )

            # 初始化视觉模型
            visual_config = model_config.get('visual_model', {})
            visual_type = visual_config.get('type', 'llama-cpp')

            if visual_type == 'llama-cpp':
                model_path = visual_config.get('path', '')
                if model_path and os.path.exists(model_path):
                    visual_model = LlamaCppVisualModel(
                        model_path=model_path,
                        device=visual_config.get('device', 'auto')
                    )
                else:
                    # 使用占位模型（实际使用需要用户配置）
                    self._log("警告：未配置本地视觉模型，使用简化模式")
                    visual_model = audio_model  # 降级使用音频模型
            else:
                # API 模式
                visual_model = None  # 待实现

            # 创建分析器
            self.analyzer = VideoAnalyzer(
                audio_model=audio_model,
                visual_model=visual_model,
                summary_config=model_config.get('summary', {})
            )

            self._log("AI 模型初始化完成")

        except Exception as e:
            logger.error(f"初始化 AI 模型失败：{e}")
            self._log(f"AI 模型初始化失败：{e}")
            self.analyzer = None

    def _on_progress(self, current: int, total: int, filename: str):
        """处理进度更新"""
        self._log(f"处理中：{filename} ({current}/{total})")

        # 更新进度条
        percent = int((current / total) * 100)
        self.progress_bar.setValue(percent)

        # 更新视频状态
        for video in self.videos:
            if video.get('filename') == filename and video.get('status') == 'processing':
                video['status'] = 'processing'
                break

        self._update_video_table()

    def _on_finished(self, success: int, failed: int):
        """处理完成"""
        self._log(f"处理完成：成功 {success} 个，失败 {failed} 个")

        # 更新按钮状态
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_select_folder.setEnabled(True)

        # 更新进度条
        self.progress_bar.setValue(100)

        # 更新表格
        self._update_video_table()

        # 系统通知
        if self.config.automation.get('notify', True):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, "处理完成",
                f"成功 {success} 个，失败 {failed} 个"
            )

    def _on_error(self, error_msg: str):
        """处理错误"""
        self._log(f"错误：{error_msg}")

    def _preview_rename(self, video_index: int):
        """预览重命名"""
        if video_index < 0 or video_index >= len(self.videos):
            return

        video = self.videos[video_index]

        # 简化预览：显示原文件名和可能的总结
        QMessageBox.information(
            self, "预览重命名",
            f"原文件名：{video.get('filename', '')}\n\n"
            f"新文件名：[AI 生成总结].[扩展名]\n\n"
            f"实际总结将在处理时生成"
        )

    def _clear_completed(self):
        """清空已处理视频"""
        # 确认
        reply = QMessageBox.question(
            self, "确认",
            "确定要清空所有已处理的视频吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 移除已处理视频
        self.videos = [v for v in self.videos if v.get('status') != 'completed']
        self._update_video_table()
        self._log("已清空已处理的视频")

    def _on_video_double_clicked(self, item):
        """视频双击事件"""
        row = item.row()
        if row < 0 or row >= len(self.videos):
            return

        video = self.videos[row]
        path = video.get('path', '')

        if path and os.path.exists(path):
            # 在文件资源管理器中打开
            os.startfile(os.path.dirname(path))

    def _open_settings(self):
        """打开设置窗口"""
        from src.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.config_manager, self)
        dialog.exec()

    def closeEvent(self, event):
        """关闭事件"""
        # 释放资源
        if self.analyzer:
            self.analyzer.cleanup()

        if self.process_thread and self.process_thread.isRunning():
            self.process_thread.cancel()
            self.process_thread.wait()

        event.accept()
