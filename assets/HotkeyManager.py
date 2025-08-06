import keyboard
from PyQt6.QtCore import QObject, pyqtSignal


class GlobalHotkeyManager(QObject):
    """全域快捷鍵管理器 - 使用keyboard.add_hotkey"""

    # 定義信號用於線程安全的通信
    show_requested = pyqtSignal()
    compact_requested = pyqtSignal()
    preset_requested = pyqtSignal(int)  # 預設快捷鍵信號
    brightness_adjust_requested = pyqtSignal(int)  # 亮度調整信號 (+5 或 -5)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.registered_hotkeys = []  # 存儲已註冊的快捷鍵
        self.parent_window = parent

        # 連接信號到主線程的槽函數
        if self.parent_window:
            self.show_requested.connect(self.parent_window.show_collapsed_ui)
            self.compact_requested.connect(self.parent_window.show_compact_ui)
            self.preset_requested.connect(
                self.parent_window.load_preset_and_show_compact)
            self.brightness_adjust_requested.connect(
                self.parent_window.adjust_brightness)

    def setup_hotkeys(self, show_hotkey, compact_hotkey, preset_hotkeys, brightness_up, brightness_down):
        """設置快捷鍵"""
        # 清理舊的快捷鍵
        self.cleanup()

        try:
            # 轉換快捷鍵格式
            show_key = self._convert_hotkey_format(show_hotkey)
            compact_key = self._convert_hotkey_format(compact_hotkey)
            brightness_up_key = self._convert_hotkey_format(brightness_up)
            brightness_down_key = self._convert_hotkey_format(brightness_down)

            # 註冊基本快捷鍵
            keyboard.add_hotkey(show_key, self._on_show_hotkey)
            keyboard.add_hotkey(compact_key, self._on_compact_hotkey)
            keyboard.add_hotkey(brightness_up_key,
                                lambda: self._on_brightness_adjust(5))
            keyboard.add_hotkey(brightness_down_key,
                                lambda: self._on_brightness_adjust(-5))

            self.registered_hotkeys = [
                show_key, compact_key, brightness_up_key, brightness_down_key]

            # 註冊preset快捷鍵
            for i, preset_hotkey in enumerate(preset_hotkeys, 1):
                preset_key = self._convert_hotkey_format(preset_hotkey)
                keyboard.add_hotkey(
                    preset_key, lambda preset_id=i: self._on_preset_hotkey(preset_id))
                self.registered_hotkeys.append(preset_key)

        except Exception as e:
            pass  # 靜默處理錯誤

    def _convert_hotkey_format(self, hotkey_string):
        """轉換快捷鍵格式"""
        return hotkey_string.lower()

    def _on_show_hotkey(self):
        """顯示UI快捷鍵回調 - 線程安全版本"""
        if self.parent_window and not self.parent_window.isVisible():
            self.show_requested.emit()

    def _on_compact_hotkey(self):
        """快捷模式快捷鍵回調 - 線程安全版本"""
        if self.parent_window and not self.parent_window.isVisible():
            self.compact_requested.emit()

    def _on_preset_hotkey(self, preset_id):
        """預設快捷鍵回調"""
        if self.parent_window and not self.parent_window.isVisible():
            self.preset_requested.emit(preset_id)

    def _on_brightness_adjust(self, adjustment):
        """亮度調整快捷鍵回調"""
        self.brightness_adjust_requested.emit(adjustment)

    def cleanup(self):
        """清理所有註冊的快捷鍵"""
        try:
            keyboard.unhook_all_hotkeys()
            self.registered_hotkeys.clear()
        except Exception as e:
            pass  # 靜默處理錯誤
