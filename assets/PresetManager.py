import configparser
import os

from PyQt6.QtCore import QTimer


class PresetManager:
    """預設配置管理器 - 支援多螢幕"""

    # 配置常數
    SETTINGS_SECTION = 'settings'
    HOTKEYS_SECTION = 'hotkeys'

    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._save_timer = None
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
            'auto_hide_seconds': '2'
        }

        self.config[self.HOTKEYS_SECTION] = {
            'hotkey_show': 'alt+a',
            'hotkey_compact': 'alt+e',
            'preset_1': 'alt+1',
            'preset_2': 'alt+2',
            'preset_3': 'alt+3',
            'preset_4': 'alt+4',
            'brightness_up': 'alt+x',
            'brightness_down': 'alt+z'
        }

        # 創建預設的 screen0 區段
        self._create_screen_section(0)
        self.save_config()

    def _create_screen_section(self, screen_index):
        """為指定螢幕創建配置區段"""
        section_name = f'screen{screen_index}'
        if section_name not in self.config:
            self.config[section_name] = {
                'preset_1': '',
                'preset_2': '',
                'preset_3': '',
                'preset_4': ''
            }

    def ensure_screen_exists(self, screen_index):
        """確保指定螢幕的配置區段存在"""
        section_name = f'screen{screen_index}'
        if section_name not in self.config:
            self._create_screen_section(screen_index)
            self.save_config()

    def get_preset(self, screen_index, preset_id):
        """獲取指定螢幕的預設值"""
        self.ensure_screen_exists(screen_index)

        section_name = f'screen{screen_index}'
        preset_key = f'preset_{preset_id}'

        preset_value = self.config.get(section_name, preset_key, fallback='')

        if not preset_value:
            return None

        try:
            # 解析類似 "[15, 80, 100, 98, 91]" 的字符串
            # 移除方括號並分割
            clean_value = preset_value.strip('[]')
            values = [int(x.strip()) for x in clean_value.split(',')]

            if len(values) == 5:
                return values
            else:
                return None

        except (ValueError, AttributeError):
            return None

    def save_preset(self, screen_index, preset_id, values):
        """保存指定螢幕的預設值"""
        self.ensure_screen_exists(screen_index)

        section_name = f'screen{screen_index}'
        preset_key = f'preset_{preset_id}'

        # 格式化為 "[15, 80, 100, 98, 91]" 格式
        preset_value = f"[{', '.join(map(str, values))}]"

        self.config.set(section_name, preset_key, preset_value)
        self.save_config()

    def is_preset_empty(self, screen_index, preset_id):
        """檢查指定螢幕的預設是否為空"""
        return self.get_preset(screen_index, preset_id) is None

    def get_last_preset(self, screen_index):
        """獲取指定螢幕最後使用的預設"""
        key = f'last_preset_screen_{screen_index}'
        return self.config.getint(self.SETTINGS_SECTION, key, fallback=1)

    def save_last_preset(self, preset_id, screen_index):
        """保存指定螢幕最後使用的預設"""
        self._ensure_section_exists(self.SETTINGS_SECTION)
        key = f'last_preset_screen_{screen_index}'
        self.config.set(self.SETTINGS_SECTION, key, str(preset_id))
        self.save_config()

    def get_all_screens(self):
        """獲取所有螢幕配置區段"""
        screen_sections = []
        for section_name in self.config.sections():
            if section_name.startswith('screen'):
                try:
                    screen_index = int(section_name[6:])  # 提取 "screen0" 中的數字
                    screen_sections.append(screen_index)
                except ValueError:
                    continue
        return sorted(screen_sections)

    def initialize_screens(self, monitor_count):
        """初始化指定數量的螢幕配置"""
        for i in range(monitor_count):
            self.ensure_screen_exists(i)

    def save_config(self):
        """保存配置文件（防抖處理）"""
        if self._save_timer is None:
            self._save_timer = QTimer()
            self._save_timer.setSingleShot(True)
            self._save_timer.timeout.connect(self._do_save_config)

        self._save_timer.start(500)

    def _do_save_config(self):
        """實際執行保存操作"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        except Exception as e:
            pass

    def get_hotkey_config(self):
        """獲取快捷鍵配置"""
        return {
            'show': self.config.get(self.HOTKEYS_SECTION, 'hotkey_show', fallback='alt+a'),
            'compact': self.config.get(self.HOTKEYS_SECTION, 'hotkey_compact', fallback='alt+e'),
            'preset_1': self.config.get(self.HOTKEYS_SECTION, 'preset_1', fallback='alt+1'),
            'preset_2': self.config.get(self.HOTKEYS_SECTION, 'preset_2', fallback='alt+2'),
            'preset_3': self.config.get(self.HOTKEYS_SECTION, 'preset_3', fallback='alt+3'),
            'preset_4': self.config.get(self.HOTKEYS_SECTION, 'preset_4', fallback='alt+4'),
            'brightness_up': self.config.get(self.HOTKEYS_SECTION, 'brightness_up', fallback='alt+x'),
            'brightness_down': self.config.get(self.HOTKEYS_SECTION, 'brightness_down', fallback='alt+z')
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
