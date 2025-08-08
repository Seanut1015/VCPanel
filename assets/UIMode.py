from PyQt6.QtWidgets import QApplication


class UIMode:
    """UI模式管理器 - 負責不同UI狀態的切換"""

    def __init__(self, window):
        self.window = window
        self._init_ui_elements()
        self._hide_initial_panels()

    def _init_ui_elements(self):
        """初始化UI元素引用"""
        # UI面板
        self.button_panel = self.window.widget  # 按鈕面板
        self.slider_panel = self.window.widget_2  # 滑條面板

        # 額外的滑條和標籤
        self.additional_sliders = [
            self.window.slider_2, self.window.slider_3,
            self.window.slider_4, self.window.slider_5
        ]

        self.additional_labels = [
            self.window.c_label, self.window.r_label,
            self.window.g_label, self.window.b_label
        ]

    def _hide_initial_panels(self):
        """初始化時隱藏所有面板"""
        self.button_panel.hide()
        self.slider_panel.hide()

    def hide_all_panels(self):
        """隱藏所有面板並強制處理事件"""
        self.button_panel.hide()
        self.slider_panel.hide()
        QApplication.processEvents()  # 強制立即處理隱藏事件

    def set_collapsed(self):
        """設置收縮模式 - 只顯示亮度滑條"""
        # 隱藏按鈕面板
        self.button_panel.hide()

        # 隱藏額外的控制項
        self._hide_additional_elements()

        # 顯示並設置滑條面板
        self.slider_panel.show()
        self.slider_panel.resize(210, 45)
        self.window.move(self.window.x_default, self.window.y_default)

        # 更新窗口狀態
        self._update_window_state(expanded=False, compact=False)

    def set_expanded(self):
        """設置展開模式 - 顯示所有控制項"""
        # 顯示所有UI元素
        self.button_panel.show()
        self._show_additional_elements()
        self.slider_panel.show()

        # 調整窗口大小和位置
        self.slider_panel.resize(210, 165)
        self.window.move(self.window.x_default, self.window.y_default - 120)

        # 更新窗口狀態
        self._update_window_state(expanded=True, compact=False)

    def set_compact(self):
        """設置快捷模式 - 只顯示預設按鈕"""
        # 隱藏滑條面板，只顯示按鈕面板
        self.slider_panel.hide()
        self.button_panel.show()

        # 調整窗口位置
        self.window.move(self.window.x_default, self.window.y_default + 49)

        # 更新窗口狀態
        self._update_window_state(expanded=False, compact=True)

    def _hide_additional_elements(self):
        """隱藏額外的滑條和標籤"""
        for element in self.additional_sliders + self.additional_labels:
            element.hide()

    def _show_additional_elements(self):
        """顯示額外的滑條和標籤"""
        for element in self.additional_sliders + self.additional_labels:
            element.show()

    def _update_window_state(self, expanded, compact):
        """更新窗口內部狀態"""
        self.window.is_expanded = expanded
        self.window.compact_mode = compact
