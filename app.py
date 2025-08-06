import sys

from assets.DDCCI import DDCCIController
from assets.HotkeyManager import GlobalHotkeyManager
from assets.PresetManager import PresetManager
from assets.styles import StyleSheets
from assets.UIMode import UIMode
from PyQt6.QtCore import QRect, Qt, QTimer
from PyQt6.QtGui import QAction, QBrush, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (QApplication, QButtonGroup, QMenu, QMessageBox,
                             QStyleFactory, QSystemTrayIcon, QWidget)
from UI_files.UI import Ui_Form

QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

# VCP 代碼常數
BRIGHTNESS = 0x10
CONTRAST = 0x12
RED = 0x16
GREEN = 0x18
BLUE = 0x1A

# 初始化控制器
controller = DDCCIController()


class VCPCache:
    """VCP值緩存管理器"""

    def __init__(self):
        self._cache = {}

    def set(self, monitor_idx, vcp_code, value):
        """設置緩存值"""
        key = f"{monitor_idx}_{vcp_code}"
        self._cache[key] = value

    def get(self, monitor_idx, vcp_code):
        """獲取緩存值"""
        key = f"{monitor_idx}_{vcp_code}"
        return self._cache.get(key)

    def is_same_value(self, monitor_idx, vcp_code, value):
        """檢查是否與緩存值相同"""
        return self.get(monitor_idx, vcp_code) == value


class MyWindow(QWidget, Ui_Form):
    """主視窗類 - VCP控制器的核心UI"""

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)

        # 初始化核心組件
        self.preset_manager = PresetManager()
        self.hotkey_manager = GlobalHotkeyManager(self)
        self.ui_mode_manager = UIMode(self)
        self.vcp_cache = VCPCache()

        # 初始化狀態變數
        self._init_variables()

        # 設置UI組件
        self._setup_components()

        # 初始化應用程式
        self._initialize_app()

    def _init_variables(self):
        """初始化狀態變數"""
        # UI狀態
        self.is_expanded = False
        self.compact_mode = False
        self.ui_mode = None  # None, 'collapsed', 'expanded', 'compact'

        # VCP相關
        self.monitor_idx = 0  # 使用第一台顯示器
        self.current_preset = None
        self.vcp_changed = False
        self.cached_brightness = 50  # 預設亮度值

        # 配置相關
        self.auto_hide_seconds = self.preset_manager.get_auto_hide_seconds()

        # UI佈局
        self._calculate_default_position()

        # VCP控制配置
        self.vcp_controls = [
            (self.slider_1, self.label, BRIGHTNESS),
            (self.slider_2, self.label_2, CONTRAST),
            (self.slider_3, self.label_3, RED),
            (self.slider_4, self.label_4, GREEN),
            (self.slider_5, self.label_5, BLUE),
        ]

    def _calculate_default_position(self):
        """計算預設窗口位置"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        self.x_default = screen_geometry.width() // 2 - 115
        self.y_default = screen_geometry.height() - 110

    def _setup_components(self):
        """設置各種UI組件"""
        self._setup_window_properties()
        self._setup_system_tray()
        self._setup_auto_hide_timer()
        self._setup_button_group()
        self._connect_signals()
        self._setup_global_hotkeys()

    def _setup_window_properties(self):
        """設置窗口屬性"""
        # 設置窗口標誌：無邊框、始終在最上層、不顯示在工作列
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 應用樣式表
        self.setStyleSheet(StyleSheets.get_main_stylesheet())

        # 設置初始位置
        self.move(self.x_default, self.y_default)

    def _setup_system_tray(self):
        """設置系統托盤"""
        self.tray_icon = QSystemTrayIcon(self)

        # 創建托盤圖示
        self.tray_icon.setIcon(self._create_tray_icon())
        self.tray_icon.setToolTip("VCP 控制器")

        # 設置托盤選單
        self.tray_icon.setContextMenu(self._create_tray_menu())
        self.tray_icon.activated.connect(self._on_tray_activated)

        # 顯示托盤圖示
        self.tray_icon.show()

    def _create_tray_icon(self):
        """創建系統托盤圖示"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(QRect(2, 2, 12, 12))
        painter.end()

        return QIcon(pixmap)

    def _create_tray_menu(self):
        """創建系統托盤選單"""
        tray_menu = QMenu()

        # 添加選單項目
        show_action = QAction("顯示控制面板", self)
        show_action.triggered.connect(self.show_collapsed_ui)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        quit_action = QAction("結束程式", self)
        quit_action.triggered.connect(self._cleanup_and_quit)
        tray_menu.addAction(quit_action)

        return tray_menu

    def _setup_auto_hide_timer(self):
        """設置自動隱藏定時器"""
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self._auto_hide_ui)

    def _setup_button_group(self):
        """設置預設按鈕組"""
        self.button_group = QButtonGroup()

        # 按鈕配置
        buttons = [
            (self.button_1, 1), (self.button_2, 2),
            (self.button_3, 3), (self.button_4, 4)
        ]

        for button, btn_id in buttons:
            self.button_group.addButton(button, btn_id)
            button.clicked.connect(
                lambda checked, preset_id=btn_id: self._on_preset_button_clicked(
                    preset_id)
            )

        self.button_group.idClicked.connect(self.load_preset)

    def _connect_signals(self):
        """連接信號槽"""
        # 展開/收縮按鈕
        self.sun_button.clicked.connect(self._toggle_expand)

        # VCP滑條信號
        for i, (slider, label, vcp_code) in enumerate(self.vcp_controls):
            slider.valueChanged.connect(
                lambda value, idx=i, lbl=label: self._on_slider_changed(
                    idx, value, lbl)
            )

    def _setup_global_hotkeys(self):
        """設置全域快捷鍵"""
        hotkey_config = self.preset_manager.get_hotkey_config()

        preset_hotkeys = [
            hotkey_config['preset_1'], hotkey_config['preset_2'],
            hotkey_config['preset_3'], hotkey_config['preset_4']
        ]

        self.hotkey_manager.setup_hotkeys(
            hotkey_config['show'], hotkey_config['compact'],
            preset_hotkeys, hotkey_config['brightness_up'],
            hotkey_config['brightness_down']
        )

    def _initialize_app(self):
        """初始化應用程式數據"""
        self._initialize_presets()
        self.hide()  # 初始隱藏

    def _initialize_presets(self):
        """初始化預設配置"""
        # 檢查並初始化空預設
        self._create_empty_presets()

        # 緩存當前亮度值
        self._cache_current_brightness()

        # 載入當前VCP值到UI
        self._loading_preset = True
        self._load_current_vcp_values()
        self._loading_preset = False

        # 設置當前預設
        self.current_preset = self.preset_manager.get_last_preset()
        self._update_button_selection()

    def _create_empty_presets(self):
        """為空的預設填入當前VCP值"""
        empty_presets = [
            i for i in range(1, 5)
            if self.preset_manager.is_preset_empty(i)
        ]

        if empty_presets:
            current_values = self._get_current_vcp_values()
            for preset_id in empty_presets:
                self.preset_manager.save_preset(preset_id, current_values)

    def _get_current_vcp_values(self):
        """獲取當前所有VCP值"""
        values = []
        for _, _, vcp_code in self.vcp_controls:
            try:
                value = controller.VCP_get(self.monitor_idx, vcp_code)[0]
                values.append(value)
            except Exception:
                values.append(50)  # 預設值
        return values

    def _cache_current_brightness(self):
        """緩存當前亮度值"""
        try:
            self.cached_brightness = controller.VCP_get(
                self.monitor_idx, BRIGHTNESS)[0]
        except Exception:
            self.cached_brightness = 50

    def _load_current_vcp_values(self):
        """載入當前VCP值到UI"""
        for slider, label, vcp_code in self.vcp_controls:
            try:
                current_value = controller.VCP_get(
                    self.monitor_idx, vcp_code)[0]
                slider.setValue(current_value)
            except Exception:
                slider.setValue(50)

    # 事件處理方法
    def enterEvent(self, event):
        """滑鼠進入事件 - 暫停自動隱藏"""
        if self.auto_hide_timer.isActive():
            self.auto_hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """滑鼠離開事件 - 開始自動隱藏倒數"""
        self._start_auto_hide_timer()
        super().leaveEvent(event)

    def closeEvent(self, event):
        """關閉事件 - 最小化到系統托盤"""
        event.ignore()
        self.ui_mode_manager.hide_all_panels()
        self.hide()
        self.ui_mode = None

    # 快捷鍵和按鈕事件處理
    def _on_tray_activated(self, reason):
        """系統托盤激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_collapsed_ui()

    def _on_preset_button_clicked(self, preset_id):
        """預設按鈕點擊事件"""
        if self.ui_mode == 'compact':
            # 快捷模式：載入預設後立即隱藏
            self.load_preset(preset_id)
            self.ui_mode_manager.hide_all_panels()
            self.hide()
            self.ui_mode = None

    def _on_slider_changed(self, control_index, value, label):
        """滑條值改變事件"""
        # 更新標籤顯示
        label.setText(str(value))
        self.vcp_changed = True

        # 防止載入預設時觸發VCP設定
        if hasattr(self, '_loading_preset') and self._loading_preset:
            return

        # 更新亮度緩存
        if control_index == 0:
            self.cached_brightness = value

        # 設定VCP值
        self._set_vcp_value_with_cache(control_index, value)

    def _toggle_expand(self):
        """切換展開/收縮狀態"""
        if self.compact_mode:
            return  # 快捷模式下不響應

        if self.is_expanded:
            self.ui_mode_manager.set_collapsed()
        else:
            self.ui_mode_manager.set_expanded()

    # UI顯示方法
    def show_collapsed_ui(self):
        """顯示收縮狀態UI"""
        self.ui_mode = 'collapsed'
        self.ui_mode_manager.set_collapsed()
        self._show_and_activate()

    def show_compact_ui(self):
        """顯示快捷模式UI"""
        self.ui_mode = 'compact'
        self.ui_mode_manager.set_compact()
        self._show_and_activate()

    def _show_and_activate(self):
        """顯示並激活窗口"""
        self.show()
        self.activateWindow()
        self.raise_()
        self._start_auto_hide_timer()

    # 自動隱藏相關
    def _start_auto_hide_timer(self):
        """啟動自動隱藏定時器"""
        # 保存VCP變更
        if self.vcp_changed:
            self._save_current_preset()
            self.vcp_changed = False

        # 啟動定時器
        self.auto_hide_timer.start(self.auto_hide_seconds * 1000)

    def _auto_hide_ui(self):
        """自動隱藏UI"""
        self.ui_mode_manager.hide_all_panels()
        self.hide()
        self.ui_mode = None

    def load_preset_and_show_compact(self, preset_id):
        """載入預設並顯示快捷模式UI"""
        self.show_compact_ui()
        self.load_preset(preset_id)

    # VCP操作方法

    def adjust_brightness(self, adjustment):
        """調整亮度（快捷鍵觸發）"""
        try:
            # 計算新亮度值
            new_brightness = max(
                0, min(100, self.cached_brightness + adjustment))

            # 更新緩存
            self.cached_brightness = new_brightness

            # 更新UI（會自動觸發VCP設定）
            self.slider_1.setValue(new_brightness)

            # 顯示UI
            if not self.isVisible():
                self.show_collapsed_ui()
            else:
                self._start_auto_hide_timer()

        except Exception:
            pass  # 靜默處理錯誤

    def _set_vcp_value_with_cache(self, control_index, value):
        """設定VCP值（帶緩存優化）"""
        try:
            _, _, vcp_code = self.vcp_controls[control_index]

            # 檢查緩存，避免重複設定相同值
            if not self.vcp_cache.is_same_value(self.monitor_idx, vcp_code, value):
                controller.VCP_set(self.monitor_idx, vcp_code, value)
                self.vcp_cache.set(self.monitor_idx, vcp_code, value)

        except Exception:
            pass  # 靜默處理錯誤

    # 預設管理方法
    def load_preset(self, preset_id):
        """載入預設配置"""
        values = self.preset_manager.get_preset(preset_id)
        if not values:
            return

        # 防止觸發VCP設定
        self._loading_preset = True

        # 設定所有滑條值並更新VCP
        for i, ((slider, _, _), value) in enumerate(zip(self.vcp_controls, values)):
            slider.setValue(value)
            self._set_vcp_value_with_cache(i, value)

        # 完成載入
        self._loading_preset = False

        # 更新狀態
        self.current_preset = preset_id
        self.cached_brightness = values[0]  # 更新亮度緩存
        self.preset_manager.save_last_preset(preset_id)
        self._update_button_selection()

    def _save_current_preset(self):
        """保存當前值到選中的預設"""
        if self.current_preset is not None:
            current_values = [slider.value()
                              for slider, _, _ in self.vcp_controls]
            self.preset_manager.save_preset(
                self.current_preset, current_values)

    def _update_button_selection(self):
        """更新按鈕選取效果"""
        # 避免重複更新相同狀態
        if hasattr(self, '_last_selected_preset') and self._last_selected_preset == self.current_preset:
            return

        buttons = [self.button_1, self.button_2, self.button_3, self.button_4]

        for i, button in enumerate(buttons, 1):
            if i == self.current_preset:
                button.setStyleSheet(StyleSheets.get_selected_button_style())
            else:
                button.setStyleSheet(StyleSheets.get_normal_button_style())

        self._last_selected_preset = self.current_preset

    # 清理和退出
    def _cleanup_and_quit(self):
        """清理資源並退出程式"""
        self.hotkey_manager.cleanup()
        controller.cleanup()
        QApplication.quit()


def main():
    """主程式入口點"""
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("WindowsVista"))

    # 設置程式不會因為所有窗口關閉而結束
    app.setQuitOnLastWindowClosed(False)

    # 檢查系統托盤可用性
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "系統托盤", "系統托盤不可用")
        return 1

    # 創建主窗口
    window = MyWindow()

    # 運行應用程式
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
