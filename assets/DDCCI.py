import ctypes
import time
from ctypes import windll, wintypes

# Windows API 常數
PHYSICAL_MONITOR_DESCRIPTION_SIZE = 128
VCP_CODES = {
    0x10: "Brightness",
    0x12: "Contrast",
    0x16: "Red Gain",
    0x18: "Green Gain",
    0x1A: "Blue Gain",

    # 其他常用 VCP code
    0xF0: "Low Blue Light",
    0xEC: "Crosshair",  # 5紅點 6綠點
    0xEF: "Shadow Boost",
}
INPUT_CODE = 0x60

INPUT_SOURCE = {
    0x11: "HDMI1",
    0x12: "HDMI2",
    0x0F: "DisplayPort"
}


class PHYSICAL_MONITOR(ctypes.Structure):
    _fields_ = [
        ('hPhysicalMonitor', wintypes.HANDLE),
        ('szPhysicalMonitorDescription', wintypes.WCHAR *
         PHYSICAL_MONITOR_DESCRIPTION_SIZE)
    ]


class DDCCIController:
    def __init__(self):
        self.user32 = windll.user32
        self.dxva2 = windll.dxva2
        self.monitors = []
        self._discover_monitors()
        self.input_source = {0x11: 'HDMI1', 0x12: 'HDMI2', 0x0F: 'DisplayPort'}

    def _discover_monitors(self):
        """發現所有支援DDC/CI的顯示器"""
        def enum_callback(hmonitor, hdc, lprect, lparam):
            # 獲取物理顯示器數量
            num_monitors = wintypes.DWORD()
            if self.dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(
                hmonitor, ctypes.byref(num_monitors)
            ):
                # 創建物理顯示器陣列
                monitors_array = (PHYSICAL_MONITOR * num_monitors.value)()

                # 獲取物理顯示器
                if self.dxva2.GetPhysicalMonitorsFromHMONITOR(
                    hmonitor, num_monitors.value, monitors_array
                ):
                    for monitor in monitors_array:
                        self.monitors.append({
                            'handle': monitor.hPhysicalMonitor,
                            'description': monitor.szPhysicalMonitorDescription
                        })
            return True

        # 定義回調函數類型
        MONITORENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM
        )

        callback = MONITORENUMPROC(enum_callback)
        self.user32.EnumDisplayMonitors(None, None, callback, 0)

    def get_vcp_feature(self, monitor_idx, vcp_code):
        """獲取VCP功能值"""
        if monitor_idx >= len(self.monitors):
            return None

        handle = self.monitors[monitor_idx]['handle']
        current_value = wintypes.DWORD()
        max_value = wintypes.DWORD()
        # result = self.dxva2.SetVCPFeature(handle, vcp_code, current_value)
        result = self.dxva2.GetVCPFeatureAndVCPFeatureReply(
            handle,
            vcp_code,
            None,  # VCP type (can be None)
            ctypes.byref(current_value),
            ctypes.byref(max_value)
        )

        if result:
            return {
                'current': current_value.value,
                'max': max_value.value
            }
        return None

    def VCP_set(self, monitor_idx, vcp_code, value):
        """設定VCP功能值"""
        if monitor_idx >= len(self.monitors):
            return False

        handle = self.monitors[monitor_idx]['handle']
        for _ in range(3):  # 嘗試三次以確保設定成功
            result = self.dxva2.SetVCPFeature(handle, vcp_code, value)
            if result:
                time.sleep(0.1)  # 給顯示器時間處理
                return True
            time.sleep(0.05)
        return False

    def VCP_get(self, monitor_idx, VCP_code):
        time.sleep(0.05)
        result = self.get_vcp_feature(monitor_idx, VCP_code)
        return result['current'], result['max'] if result else None

    def get_input_source(self, monitor_idx=0):
        """獲取輸入源 (VCP code 0x60)"""
        time.sleep(0.05)
        result = self.get_vcp_feature(monitor_idx, 0x60)
        return result['current'] if result else None

    def set_input_source(self, monitor_idx, source):
        """設定輸入源 (常見值: 0x11=HDMI1, 0x12=HDMI2, 0x0F=DisplayPort)"""
        return self.VCP_set(monitor_idx, 0x60, source)

    def list_monitors(self):
        """列出所有發現的顯示器"""
        for i, monitor in enumerate(self.monitors):
            print(f"Monitor {i}: {monitor['description']}")

    def cleanup(self):
        """清理資源"""
        for monitor in self.monitors:
            self.dxva2.DestroyPhysicalMonitor(monitor['handle'])

# 使用範例


def main():
    controller = DDCCIController()

    try:
        print("發現的顯示器:")
        controller.list_monitors()

        if not controller.monitors:
            print("未發現支援DDC/CI的顯示器")
            return

        # 使用第一台顯示器
        monitor_idx = 0

        # 獲取當前亮度
        current_brightness = controller.get_brightness(monitor_idx)
        print(f"當前亮度: {current_brightness}")

        # 設定亮度為80
        if controller.set_brightness(monitor_idx, 80):
            print("亮度設定成功")
            time.sleep(1)

            # 驗證設定
            new_brightness = controller.get_brightness(monitor_idx)
            print(f"新亮度: {new_brightness}")

        # 獲取對比度
        contrast = controller.get_contrast(monitor_idx)
        print(f"當前對比度: {contrast}")
        time.sleep(0.05)
        # 獲取輸入源
        input_source = controller.get_input_source(monitor_idx)
        if input_source in controller.input_source:
            print(f"當前輸入源: {controller.input_source[input_source]}")
        else:
            print(
                f"當前輸入源: 0x{input_source:02X}" if input_source else "無法獲取輸入源")

    finally:
        controller.cleanup()


if __name__ == "__main__":
    main()
