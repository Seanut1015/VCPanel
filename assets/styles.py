"""
樣式表配置文件
包含所有UI元素的樣式定義
"""


class StyleSheets:
    """樣式表管理類"""

    @staticmethod
    def get_main_stylesheet():
        """獲取主要樣式表"""
        return """
            QWidget {
                background-color: rgba(50, 50, 50, 220);
                border-radius: 7px;
            }
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(150, 150, 150, 220);
            }
            QLabel {
                background: transparent;
                color: white;
                font-weight: bold;
            }
            QSlider {
                background: transparent;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: transparent;
            }
            QSlider::sub-page:horizontal {
                background: #3daee9; /* 左側（目前值） */
                height: 4px;
            }
            QSlider::add-page:horizontal {
                background: #cccccc; /* 右側（剩餘） */
                height: 4px;
            }
            QSlider::handle:horizontal {
                background: transparent;
                border: none;
                width: 2px;
                margin: -6px 0;
            }


            """
        # """
        # QSlider::groove:horizontal {
        #         border: 1px solid #999999;
        #         height: 8px;
        #         background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
        #         margin: 2px 0;
        #         border-radius: 4px;
        #     }
        #     QSlider::handle:horizontal {
        #         background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
        #         border: 1px solid #5c5c5c;
        #         width: 18px;
        #         margin: -2px 0;
        #         border-radius: 9px;
        #     }
        # """

    @staticmethod
    def get_selected_button_style():
        """獲取選中按鈕樣式"""
        return """
            QPushButton {
                background-color: rgba(100, 150, 255, 150);
                border: 2px solid #4A90E2;
                border-radius: 7px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(120, 170, 255, 220);
            }
        """

    @staticmethod
    def get_normal_button_style():
        """獲取普通按鈕樣式"""
        return """
            QPushButton {
                background-color: rgba(100, 100, 100, 220);
                border: none;
                border-radius: 7px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(150, 150, 150, 220);
            }
        """

    @staticmethod
    def get_tray_menu_style():
        """獲取系統托盤選單樣式"""
        return """
            QMenu {
                background-color: rgba(40, 40, 40, 240);
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 8px 16px;
                color: white;
            }
            QMenu::item:selected {
                background-color: rgba(100, 150, 255, 150);
            }
        """
