import sys

from PyQt6.QtCore import QRect, Qt, QTimer
from PyQt6.QtGui import QAction, QBrush, QCursor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (QApplication, QButtonGroup, QMenu, QMessageBox,
                             QStyleFactory, QSystemTrayIcon, QWidget)

from assets.DDCCI import DDCCIController
from assets.HotkeyManager import GlobalHotkeyManager
from assets.PresetManager import PresetManager
from assets.styles import StyleSheets
from assets.UIMode import UIMode
from UI_files.UI import Ui_Form

QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

# VCP 代碼常數
BRIGHTNESS = 0x10
CONTRAST = 0x12
RED = 0x16
GREEN = 0x18
BLUE = 0x1A

# X偏移與Y偏移
X_OFFSET = 0
Y_OFFSET = 0.9


# 初始化控制器
controller = DDCCIController()


class MyWindow(QWidget, Ui_Form):
    """主視窗類 - VCP控制器的核心UI"""

    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)

        # 初始化核心組件
        self.preset_manager = PresetManager()
        self.hotkey_manager = GlobalHotkeyManager(self)
        self.ui_mode_manager = UIMode(self)

        # 初始化狀態變數
        self._init_variables()

        # 設置UI組件
        self._setup_components()

        # 初始化應用程式
        self._init_app()

    def _init_variables(self):
        """初始化狀態變數"""
        # UI狀態
        self.is_expanded = False
        self.compact_mode = False
        self.ui_mode = None  # None, 'collapsed', 'expanded', 'compact'

        # VCP相關
        self.monitor_idx = 0  # 使用第一台顯示器
        self.current_preset = [0]*len(controller.monitors)
        self.vcp_changed = False
        self.screen_count = len(controller.monitors)

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

    def _init_presets(self):
        """初始化預設配置"""
        # 檢查並初始化空預設
        self.preset_manager.initialize_screens(self.screen_count)
        self._create_empty_presets()

        # 緩存當前亮度值
        self._load_current_vcp_values()

        # 設置當前預設
        for i in range(self.screen_count):
            self.current_preset[i] = self.preset_manager.get_last_preset(i)
        self._update_button_selection()

    def _init_app(self):
        """初始化應用程式數據"""
        self._init_presets()
        self.hide()  # 初始隱藏

    def _get_current_screen_index(self):
        """獲取滑鼠當前所在螢幕的索引"""
        try:
            # 獲取滑鼠位置
            cursor_pos = QCursor.pos()

            # 遍歷所有螢幕
            screens = QApplication.screens()
            for i, screen in enumerate(screens):
                if screen.geometry().contains(cursor_pos):
                    self.monitor_idx = i
                    break
            else:
                # 如果沒找到，返回主螢幕
                self.monitor_idx = 0

        except Exception:
            self.monitor_idx = 0  # 預設返回第一個螢幕

    def _calculate_default_position(self):
        """更新每個螢幕的UI預設位置"""
        self.screen_pos = []
        screens = QApplication.screens()
        for screen in screens:
            geom = screen.availableGeometry()
            pos = (
                geom.x() + geom.width() // 2 - 115,
                geom.y() + geom.height() - geom.height() // 9
            )
            self.screen_pos.append(pos)
        self.x_default, self.y_default = self.screen_pos[0]

    def _position_ui_on_current_screen(self):
        """根據目前螢幕 index 顯示 UI"""
        self._get_current_screen_index()
        if not hasattr(self, 'screen_pos') or len(self.screen_pos) != len(QApplication.screens()):
            self._calculate_default_position()
        self.x_default, self.y_default = self.screen_pos[self.monitor_idx]

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

    def _create_empty_presets(self):
        """為空的預設填入當前VCP值"""
        for screen_idx in range(self.screen_count):
            empty_presets = [
                i for i in range(1, 5)
                if self.preset_manager.is_preset_empty(screen_idx, i)
            ]

            if empty_presets:
                # 切換到該螢幕獲取VCP值
                old_monitor = self.monitor_idx
                self.monitor_idx = screen_idx
                current_values = self._get_current_vcp_values()

                # 為空預設填入值
                for preset_id in empty_presets:
                    self.preset_manager.save_preset(
                        screen_idx, preset_id, current_values)

                # 恢復原來的螢幕
                self.monitor_idx = old_monitor

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

    def _load_current_vcp_values(self):
        """載入當前VCP值到UI"""
        self.vcp_temp = []
        for i in range(self.screen_count):
            self.vcp_temp.append([])
            for slider, label, vcp_code in self.vcp_controls:
                current_value = controller.VCP_get(
                    i, vcp_code)[0]
                self.vcp_temp[i].append(current_value)

    def _set_current_slider_values(self):
        """載入當前VCP值到UI"""
        self._loading_preset = True
        i = 0
        for slider, label, vcp_code in self.vcp_controls:
            try:
                slider.setValue(self.vcp_temp[self.monitor_idx][i])
            except Exception:
                slider.setValue(50)
            i += 1
        self._loading_preset = False

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
            # self.load_preset(preset_id)
            self.ui_mode_manager.hide_all_panels()
            self.hide()
            self.ui_mode = None

    def _on_slider_changed(self, vcp_index, value, label):
        """滑條值改變事件"""
        # 更新標籤顯示
        label.setText(str(value))
        self.vcp_changed = True

        # 防止載入預設時觸發VCP設定
        if hasattr(self, '_loading_preset') and self._loading_preset:
            return

        # 設定VCP值
        self._set_vcp_value(vcp_index, self.vcp_controls[vcp_index][2], value)

    # UI顯示方法

    def show_collapsed_ui(self):
        """顯示收縮狀態UI"""
        self._position_ui_on_current_screen()
        self.slider_1.setValue(self.vcp_temp[self.monitor_idx][0])
        self.ui_mode = 'collapsed'
        self.ui_mode_manager.set_collapsed()
        self._show_and_activate()

    def show_compact_ui(self):
        """顯示快捷模式UI"""
        self._position_ui_on_current_screen()
        self.ui_mode = 'compact'
        self.ui_mode_manager.set_compact()
        self._show_and_activate()

    def _toggle_expand(self):
        """切換展開/收縮狀態"""
        if self.is_expanded:
            self.ui_mode_manager.set_collapsed()
        else:
            self._set_current_slider_values()
            self._update_button_selection()
            self.ui_mode_manager.set_expanded()

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
            # 顯示UI
            if not self.isVisible():
                self.show_collapsed_ui()
            else:
                self._start_auto_hide_timer()

            # 計算新亮度值
            new_brightness = max(
                0, min(100, self.vcp_temp[self.monitor_idx][0] + adjustment))

            # 更新UI（會自動觸發VCP設定）
            self.slider_1.setValue(new_brightness)

        except Exception:
            pass  # 靜默處理錯誤

    def _set_vcp_value(self, vcp_index, vcp_code, value):
        """設定VCP值"""
        try:
            if not self.vcp_temp[self.monitor_idx][vcp_index] == value:
                controller.VCP_set(self.monitor_idx, vcp_code, value)
                self.vcp_temp[self.monitor_idx][vcp_index] = value
        except Exception:
            pass  # 靜默處理錯誤

    # 預設管理方法
    def load_preset(self, preset_id):
        """載入預設配置"""
        values = self.preset_manager.get_preset(self.monitor_idx, preset_id)
        if not values:
            return

        # 防止觸發VCP設定
        self._loading_preset = True

        # 設定所有滑條值並更新VCP
        for vcp_index, ((slider, _, vcp_code), value) in enumerate(zip(self.vcp_controls, values)):
            slider.setValue(value)
            self._set_vcp_value(
                vcp_index, self.vcp_controls[vcp_index][2], value)

        # 完成載入
        self._loading_preset = False

        # 更新狀態
        self.current_preset[self.monitor_idx] = preset_id
        self.preset_manager.save_last_preset(preset_id, self.monitor_idx)
        self._update_button_selection()

    def _save_current_preset(self):
        """保存當前值到選中的預設"""
        if self.current_preset[self.monitor_idx] is not None:
            self.preset_manager.save_preset(
                self.monitor_idx, self.current_preset[self.monitor_idx], self.vcp_temp[self.monitor_idx])

    def _update_button_selection(self):
        """更新按鈕選取效果"""
        # 避免重複更新相同狀態
        if hasattr(self, '_last_selected_preset') and self._last_selected_preset == self.current_preset[self.monitor_idx]:
            return
        buttons = [self.button_1, self.button_2, self.button_3, self.button_4]
        for i, button in enumerate(buttons, 1):
            if i == self.current_preset[self.monitor_idx]:
                button.setStyleSheet(StyleSheets.get_selected_button_style())
            else:
                button.setStyleSheet(StyleSheets.get_normal_button_style())
        self._last_selected_preset = self.current_preset[self.monitor_idx]

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
