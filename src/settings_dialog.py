"""
设置对话框
"""

import os
import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFileDialog, QComboBox,
    QSpinBox, QCheckBox, QTabWidget, QMessageBox, QListWidget,
    QListWidgetItem, QDoubleSpinBox
)
from PyQt6.QtCore import Qt

from src.config import ConfigManager, Config

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config = config_manager.get_config()

        self.setWindowTitle("设置 - LocalVidRen")
        self.setMinimumSize(700, 600)

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)

        # 选项卡
        self.tabs = QTabWidget()

        # 模型设置
        self.tabs.addTab(self._create_model_tab(), "模型配置")

        # 重命名设置
        self.tabs.addTab(self._create_naming_tab(), "重命名设置")

        # 处理设置
        self.tabs.addTab(self._create_processing_tab(), "处理设置")

        # 监控设置
        self.tabs.addTab(self._create_monitor_tab(), "文件夹监控")

        # 自动化设置
        self.tabs.addTab(self._create_automation_tab(), "自动化设置")

        layout.addWidget(self.tabs)

        # 底部按钮
        button_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 保存")
        self.btn_save.clicked.connect(self._save_settings)
        button_layout.addWidget(self.btn_save)

        self.btn_reset = QPushButton("↺ 重置")
        self.btn_reset.clicked.connect(self._reset_settings)
        button_layout.addWidget(self.btn_reset)

        button_layout.addStretch()

        self.btn_cancel = QPushButton("✗ 取消")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)

        layout.addLayout(button_layout)

    def _create_model_tab(self) -> QGroupBox:
        """创建模型设置选项卡"""
        group = QGroupBox("AI 模型配置")
        layout = QVBoxLayout()

        # 模型模式
        layout.addWidget(QLabel("分析模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["本地模式", "API 模式"])
        mode = self.config.model.get("mode", "local")
        self.mode_combo.setCurrentIndex(0 if mode == "local" else 1)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        layout.addWidget(self.mode_combo)

        # 音频模型设置
        audio_group = QGroupBox("语音识别模型")
        audio_layout = QVBoxLayout()

        audio_layout.addWidget(QLabel("模型大小:"))
        self.audio_size_combo = QComboBox()
        self.audio_size_combo.addItems(["tiny", "base", "small", "medium"])
        size = self.config.model.get("audio_model", {}).get("size", "base")
        self.audio_size_combo.setCurrentText(size)
        audio_layout.addWidget(self.audio_size_combo)

        audio_layout.addWidget(QLabel("设备:"))
        self.audio_device_combo = QComboBox()
        self.audio_device_combo.addItems(["auto", "cpu", "cuda"])
        device = self.config.model.get("audio_model", {}).get("device", "auto")
        self.audio_device_combo.setCurrentText(device)
        audio_layout.addWidget(self.audio_device_combo)

        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)

        # 视觉模型设置
        visual_group = QGroupBox("视觉分析模型")
        visual_layout = QVBoxLayout()

        # 模型类型
        visual_layout.addWidget(QLabel("模型类型:"))
        self.visual_type_combo = QComboBox()
        self.visual_type_combo.addItems(["本地 GGUF 模型", "OpenAI 兼容 API"])
        visual_type = self.config.model.get("visual_model", {}).get("type", "llama-cpp")
        self.visual_type_combo.setCurrentIndex(0 if visual_type == "llama-cpp" else 1)
        self.visual_type_combo.currentTextChanged.connect(self._on_visual_type_changed)
        visual_layout.addWidget(self.visual_type_combo)

        # 本地模型路径
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("选择 GGUF 模型文件...")
        model_path = self.config.model.get("visual_model", {}).get("path", "")
        self.model_path_edit.setText(model_path)
        self.model_path_btn = QPushButton("浏览...")
        self.model_path_btn.clicked.connect(self._select_model_path)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.model_path_edit)
        path_layout.addWidget(self.model_path_btn)
        visual_layout.addLayout(path_layout)

        # API 设置（初始隐藏）
        self.api_group = QGroupBox("API 配置")
        self.api_layout = QVBoxLayout()

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入 API 密钥")
        self.api_key_edit.setText(self.config.model.get("visual_model", {}).get("api_key", ""))
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_layout.addWidget(QLabel("API 密钥:"))
        self.api_layout.addWidget(self.api_key_edit)

        self.api_url_edit = QLineEdit()
        self.api_url_edit.setPlaceholderText("输入 API 基础 URL")
        self.api_url_edit.setText(self.config.model.get("visual_model", {}).get("base_url", ""))
        self.api_layout.addWidget(QLabel("API URL:"))
        self.api_layout.addWidget(self.api_url_edit)

        self.api_model_edit = QLineEdit()
        self.api_model_edit.setPlaceholderText("模型名称")
        self.api_model_edit.setText(self.config.model.get("visual_model", {}).get("model_name", "gpt-4v"))
        self.api_layout.addWidget(QLabel("模型名称:"))
        self.api_layout.addWidget(self.api_model_edit)

        self.api_group.setLayout(self.api_layout)
        self.api_group.setVisible(False)
        visual_layout.addWidget(self.api_group)

        visual_group.setLayout(visual_layout)
        layout.addWidget(visual_group)

        # 总结设置
        summary_group = QGroupBox("内容总结配置")
        summary_layout = QVBoxLayout()

        summary_layout.addWidget(QLabel("总结长度:"))
        self.summary_length_combo = QComboBox()
        self.summary_length_combo.addItems(["短 (10-15 字)", "中 (15-25 字)", "长 (25-40 字)"])
        length = self.config.model.get("summary", {}).get("length", "short")
        length_map = {"short": 0, "medium": 1, "long": 2}
        self.summary_length_combo.setCurrentIndex(length_map.get(length, 0))
        summary_layout.addWidget(self.summary_length_combo)

        summary_layout.addWidget(QLabel("总结风格:"))
        self.summary_style_combo = QComboBox()
        self.summary_style_combo.addItems(["简洁描述型", "事件概括型", "关键词型"])
        style = self.config.model.get("summary", {}).get("style", "concise")
        style_map = {"concise": 0, "event": 1, "keyword": 2}
        self.summary_style_combo.setCurrentIndex(style_map.get(style, 0))
        summary_layout.addWidget(self.summary_style_combo)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        group.setLayout(layout)
        return group

    def _create_naming_tab(self) -> QGroupBox:
        """创建重命名设置选项卡"""
        group = QGroupBox("重命名配置")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("文件名模板:"))
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "[内容总结].[扩展名]",
            "[日期]_[内容总结].[扩展名]",
            "[原文件名前缀]_[内容总结].[扩展名]"
        ])
        template = self.config.naming.get("template", "[summary].[ext]")
        template_map = {
            "[summary].[ext]": 0,
            "[date]_[summary].[ext]": 1,
            "[prefix]_[summary].[ext]": 2
        }
        self.template_combo.setCurrentIndex(template_map.get(template, 0))
        layout.addWidget(self.template_combo)

        layout.addWidget(QLabel("历史记录数量:"))
        self.history_spin = QSpinBox()
        self.history_spin.setMinimum(10)
        self.history_spin.setMaximum(100)
        self.history_spin.setValue(self.config.naming.get("max_history", 50))
        layout.addWidget(self.history_spin)

        group.setLayout(layout)
        return group

    def _create_processing_tab(self) -> QGroupBox:
        """创建处理设置选项卡"""
        group = QGroupBox("处理配置")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("并发处理数:"))
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setMinimum(1)
        self.concurrency_spin.setMaximum(8)
        self.concurrency_spin.setValue(self.config.processing.get("concurrency", 2))
        layout.addWidget(self.concurrency_spin)

        layout.addWidget(QLabel("最大重试次数:"))
        self.retry_spin = QSpinBox()
        self.retry_spin.setMinimum(0)
        self.retry_spin.setMaximum(5)
        self.retry_spin.setValue(self.config.processing.get("max_retries", 1))
        layout.addWidget(self.retry_spin)

        self.skip_check = QCheckBox("跳过已处理视频")
        self.skip_check.setChecked(self.config.processing.get("skip_processed", True))
        layout.addWidget(self.skip_check)

        layout.addWidget(QLabel("视频大小限制 (MB):"))
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setMinimum(10)
        self.size_spin.setMaximum(5000)
        self.size_spin.setSuffix(" MB")
        self.size_spin.setValue(self.config.video.get("max_size_mb", 500))
        layout.addWidget(self.size_spin)

        group.setLayout(layout)
        return group

    def _create_monitor_tab(self) -> QGroupBox:
        """创建监控设置选项卡"""
        group = QGroupBox("文件夹监控配置")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("监控文件夹列表:"))
        self.monitor_list = QListWidget()
        for folder in self.config.monitor.get("folders", []):
            self.monitor_list.addItem(folder)
        layout.addWidget(self.monitor_list)

        button_layout = QHBoxLayout()

        self.btn_add_folder = QPushButton("➕ 添加")
        self.btn_add_folder.clicked.connect(self._add_monitor_folder)
        button_layout.addWidget(self.btn_add_folder)

        self.btn_remove_folder = QPushButton("➖ 删除")
        self.btn_remove_folder.clicked.connect(self._remove_monitor_folder)
        button_layout.addWidget(self.btn_remove_folder)

        layout.addLayout(button_layout)

        layout.addWidget(QLabel("监控延迟 (秒):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(1)
        self.delay_spin.setMaximum(60)
        self.delay_spin.setValue(self.config.monitor.get("delay_seconds", 10))
        layout.addWidget(self.delay_spin)

        self.recursive_check = QCheckBox("监控子文件夹")
        self.recursive_check.setChecked(self.config.monitor.get("recursive", True))
        layout.addWidget(self.recursive_check)

        group.setLayout(layout)
        return group

    def _create_automation_tab(self) -> QGroupBox:
        """创建自动化设置选项卡"""
        group = QGroupBox("自动化配置")
        layout = QVBoxLayout()

        self.auto_start_check = QCheckBox("开机自动启动")
        self.auto_start_check.setChecked(self.config.automation.get("auto_start", False))
        layout.addWidget(self.auto_start_check)

        self.tray_check = QCheckBox("最小化到系统托盘")
        self.tray_check.setChecked(self.config.automation.get("minimize_to_tray", True))
        layout.addWidget(self.tray_check)

        self.shutdown_check = QCheckBox("处理完成后自动关机")
        self.shutdown_check.setChecked(self.config.automation.get("shutdown_after", False))
        layout.addWidget(self.shutdown_check)

        self.notify_check = QCheckBox("显示系统通知")
        self.notify_check.setChecked(self.config.automation.get("notify", True))
        layout.addWidget(self.notify_check)

        group.setLayout(layout)
        return group

    def _load_settings(self):
        """加载设置"""
        # 已在初始化时加载
        pass

    def _save_settings(self):
        """保存设置"""
        try:
            # 模型设置
            self.config.model["mode"] = "local" if self.mode_combo.currentIndex() == 0 else "api"
            self.config.model["audio_model"]["size"] = self.audio_size_combo.currentText()
            self.config.model["audio_model"]["device"] = self.audio_device_combo.currentText()
            self.config.model["visual_model"]["type"] = "llama-cpp" if self.visual_type_combo.currentIndex() == 0 else "openai-compatible"
            self.config.model["visual_model"]["path"] = self.model_path_edit.text()
            self.config.model["visual_model"]["api_key"] = self.api_key_edit.text()
            self.config.model["visual_model"]["base_url"] = self.api_url_edit.text()
            self.config.model["visual_model"]["model_name"] = self.api_model_edit.text()
            self.config.model["summary"]["length"] = ["short", "medium", "long"][self.summary_length_combo.currentIndex()]
            self.config.model["summary"]["style"] = ["concise", "event", "keyword"][self.summary_style_combo.currentIndex()]

            # 重命名设置
            templates = ["[summary].[ext]", "[date]_[summary].[ext]", "[prefix]_[summary].[ext]"]
            self.config.naming["template"] = templates[self.template_combo.currentIndex()]
            self.config.naming["max_history"] = self.history_spin.value()

            # 处理设置
            self.config.processing["concurrency"] = self.concurrency_spin.value()
            self.config.processing["max_retries"] = self.retry_spin.value()
            self.config.processing["skip_processed"] = self.skip_check.isChecked()
            self.config.video["max_size_mb"] = self.size_spin.value()

            # 监控设置
            self.config.monitor["folders"] = [
                self.monitor_list.item(i).text()
                for i in range(self.monitor_list.count())
            ]
            self.config.monitor["delay_seconds"] = self.delay_spin.value()
            self.config.monitor["recursive"] = self.recursive_check.isChecked()

            # 自动化设置
            self.config.automation["auto_start"] = self.auto_start_check.isChecked()
            self.config.automation["minimize_to_tray"] = self.tray_check.isChecked()
            self.config.automation["shutdown_after"] = self.shutdown_check.isChecked()
            self.config.automation["notify"] = self.notify_check.isChecked()

            # 保存配置
            self.config_manager.save_config()

            QMessageBox.information(self, "成功", "设置已保存")
            self.accept()

        except Exception as e:
            logger.error(f"保存设置失败：{e}")
            QMessageBox.critical(self, "错误", f"保存设置失败：{e}")

    def _reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要重置所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 重新加载默认配置
            self.config = Config()
            self.config_manager.config = self.config
            self._load_settings()
            QMessageBox.information(self, "成功", "已重置为默认设置")

    def _on_mode_changed(self, mode: str):
        """模式改变事件"""
        pass

    def _on_visual_type_changed(self, type: str):
        """视觉模型类型改变事件"""
        is_local = type == "本地 GGUF 模型"
        self.model_path_edit.setVisible(is_local)
        self.model_path_btn.setVisible(is_local)
        self.api_group.setVisible(not is_local)

    def _select_model_path(self):
        """选择模型路径"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 GGUF 模型文件", "", "GGUF Files (*.gguf)"
        )
        if path:
            self.model_path_edit.setText(path)

    def _add_monitor_folder(self):
        """添加监控文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择监控文件夹")
        if folder:
            item = QListWidgetItem(folder)
            self.monitor_list.addItem(item)

    def _remove_monitor_folder(self):
        """删除监控文件夹"""
        current = self.monitor_list.currentItem()
        if current:
            self.monitor_list.takeItem(self.monitor_list.row(current))
