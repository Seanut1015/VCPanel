import configparser
import os

from PyQt6.QtCore import QTimer


class PresetManager:
    """預設配置管理器"""

    # 配置常數
    SETTINGS_SECTION = 'settings'
    HOTKEYS_SECTION = 'hotkeys'
    CONFIG_KEYS = {
        'brightness': 'brightness',
        'contrast': 'contrast',
        'red': 'red',
        'green': 'green',
        'blue': 'blue'
    }

    def __init__(self, config_file='presets.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._save_timer = None  # 延遲保存定時器
        self.load_config()

    def load_config(self):
        """載入配置文件"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            self._create_default_config()

    def _create_default_config(self):
        """創建預設配置"""
        # 設置預設值
        self.config[self.SETTINGS_SECTION] = {
            'last_preset': '1',
            'auto_hide_seconds': '5'
        }

        self.config[self.HOTKEYS_SECTION] = {
            'hotkey_show': 'alt+a',
            'hotkey_compact': 'alt+e',
            'preset_1': 'alt+1',
            'preset_2': 'alt+2',
            'preset_3': 'alt+3',
            'preset_4': 'alt+4',
            'brightness_up': 'alt+up',
            'brightness_down': 'alt+down'
        }

        # 創建空的預設區段
        for i in range(1, 5):
            self.config[f'preset{i}'] = {
                key: '' for key in self.CONFIG_KEYS.values()}

        self.save_config()

    def save_config(self):
        """保存配置文件（防抖處理）"""
        if self._save_timer is None:
            self._save_timer = QTimer()
            self._save_timer.setSingleShot(True)
            self._save_timer.timeout.connect(self._do_save_config)

        # 防抖：500ms後保存
        self._save_timer.start(500)

    def _do_save_config(self):
        """實際執行保存操作"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        except Exception as e:
            pass  # 靜默處理錯誤

    def get_preset(self, preset_id):
        """獲取預設值，如果為空返回None"""
        section = f'preset{preset_id}'
        if section not in self.config:
            return None

        values = [
            self.config.get(section, key, fallback='')
            for key in self.CONFIG_KEYS.values()
        ]

        # 如果任一值為空，返回None表示未設定
        if any(v == '' for v in values):
            return None

        try:
            return [int(v) for v in values]
        except ValueError:
            return None

    def save_preset(self, preset_id, values):
        """保存預設值"""
        section = f'preset{preset_id}'
        if section not in self.config:
            self.config.add_section(section)

        for key, value in zip(self.CONFIG_KEYS.values(), values):
            self.config.set(section, key, str(value))

        self.save_config()

    def is_preset_empty(self, preset_id):
        """檢查預設是否為空"""
        return self.get_preset(preset_id) is None

    def get_last_preset(self):
        """獲取最後使用的預設"""
        return self.config.getint(self.SETTINGS_SECTION, 'last_preset', fallback=1)

    def save_last_preset(self, preset_id):
        """保存最後使用的預設"""
        self._ensure_section_exists(self.SETTINGS_SECTION)
        self.config.set(self.SETTINGS_SECTION, 'last_preset', str(preset_id))
        self.save_config()

    def get_hotkey_config(self):
        """獲取快捷鍵配置"""
        return {
            'show': self.config.get(self.HOTKEYS_SECTION, 'hotkey_show', fallback='alt+a'),
            'compact': self.config.get(self.HOTKEYS_SECTION, 'hotkey_compact', fallback='alt+e'),
            'preset_1': self.config.get(self.HOTKEYS_SECTION, 'preset_1', fallback='alt+1'),
            'preset_2': self.config.get(self.HOTKEYS_SECTION, 'preset_2', fallback='alt+2'),
            'preset_3': self.config.get(self.HOTKEYS_SECTION, 'preset_3', fallback='alt+3'),
            'preset_4': self.config.get(self.HOTKEYS_SECTION, 'preset_4', fallback='alt+4'),
            'brightness_up': self.config.get(self.HOTKEYS_SECTION, 'brightness_up', fallback='alt+up'),
            'brightness_down': self.config.get(self.HOTKEYS_SECTION, 'brightness_down', fallback='alt+down')
        }

    def get_auto_hide_seconds(self):
        """獲取自動隱藏秒數"""
        return self.config.getint(self.SETTINGS_SECTION, 'auto_hide_seconds', fallback=5)

    def save_auto_hide_seconds(self, seconds):
        """保存自動隱藏秒數"""
        self._ensure_section_exists(self.SETTINGS_SECTION)
        self.config.set(self.SETTINGS_SECTION,
                        'auto_hide_seconds', str(seconds))
        self.save_config()

    def save_hotkey_config(self, hotkey_config):
        """保存快捷鍵配置"""
        self._ensure_section_exists(self.HOTKEYS_SECTION)
        for key, value in hotkey_config.items():
            self.config.set(self.HOTKEYS_SECTION, key, value)
        self.save_config()

    def _ensure_section_exists(self, section_name):
        """確保配置區段存在"""
        if section_name not in self.config:
            self.config.add_section(section_name)
