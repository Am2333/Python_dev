class BackgroundAutomation:
    def __init__(self, target_process_name):
        self.target_process_name = target_process_name
        self.target_window = None
        self.is_running = False
        self.lock = threading.Lock()
        
    def find_target_window(self):
        """查找目标程序窗口"""
        try:
            windows = gw.getWindowsWithTitle(self.target_process_name)
            if windows:
                self.target_window = windows[0]
                return True
            return False
        except Exception as e:
            print(f"查找窗口错误: {e}")
            return False
    
    def capture_window(self):
        """捕获目标窗口截图"""
        if not self.target_window:
            return None
        
        try:
            # 获取窗口位置和大小
            left, top, right, bottom = self.target_window.left, self.target_window.top, \
                                      self.target_window.right, self.target_window.bottom
            width, height = right - left, bottom - top
            
            # 截图
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"截图错误: {e}")
            return None
    
    def image_recognition(self, template_path, screenshot, threshold=0.8):
        """图像识别匹配"""
        try:
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                print(f"无法加载模板图像: {template_path}")
                return None
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 计算中心点坐标（相对窗口）
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y, max_val)
            return None
        except Exception as e:
            print(f"图像识别错误: {e}")
            return None
    
    def send_background_click(self, rel_x, rel_y):
        """后台发送鼠标点击（不夺取焦点）"""
        if not self.target_window:
            return False
        
        try:
            # 获取窗口句柄
            hwnd = self.target_window._hWnd
            
            # 计算绝对坐标
            abs_x = self.target_window.left + rel_x
            abs_y = self.target_window.top + rel_y
            
            # 发送后台鼠标消息
            lParam = win32api.MAKELONG(rel_x, rel_y)
            
            # 鼠标移动
            win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
            
            # 鼠标左键按下和释放
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            time.sleep(0.1)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
            
            return True
        except Exception as e:
            print(f"后台点击错误: {e}")
            return False
    
    def send_background_key(self, key):
        """后台发送键盘输入"""
        if not self.target_window:
            return False
        
        try:
            hwnd = self.target_window._hWnd
            
            # 发送键盘消息
            if isinstance(key, str) and len(key) == 1:
                # 单个字符
                win32gui.SendMessage(hwnd, win32con.WM_CHAR, ord(key), 0)
            else:
                # 特殊键（需要映射）
                key_mapping = {
                    'enter': win32con.VK_RETURN,
                    'tab': win32con.VK_TAB,
                    'esc': win32con.VK_ESCAPE,
                    'space': win32con.VK_SPACE,
                }
                if key.lower() in key_mapping:
                    vk_code = key_mapping[key.lower()]
                    win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)
                    time.sleep(0.05)
                    win32gui.SendMessage(hwnd, win32con.WM_KEYUP, vk_code, 0)
            
            return True
        except Exception as e:
            print(f"后台键盘输入错误: {e}")
            return False
    
    def automation_logic(self):
        """主要的自动化逻辑"""
        while self.is_running:
            with self.lock:
                if not self.target_window or not self.target_window.isActive:
                    if not self.find_target_window():
                        print("未找到目标窗口，等待...")
                        time.sleep(2)
                        continue
                
                # 捕获窗口截图
                screenshot = self.capture_window()
                if screenshot is None:
                    time.sleep(1)
                    continue
                
                # 图像识别和逻辑判断
                # 示例：识别"开始"按钮并点击
                button_pos = self.image_recognition('start_button.png', screenshot)
                if button_pos:
                    print(f"识别到按钮，置信度: {button_pos[2]:.2f}")
                    self.send_background_click(button_pos[0], button_pos[1])
                    time.sleep(1)
                
                # 可以添加更多识别逻辑...
                
            time.sleep(0.5)  # 降低CPU使用率
    
    def start(self):
        """启动自动化"""
        if self.is_running:
            print("自动化已在运行")
            return
        
        if not self.find_target_window():
            print("未找到目标程序")
            return
        
        self.is_running = True
        self.automation_thread = threading.Thread(target=self.automation_logic)
        self.automation_thread.daemon = True
        self.automation_thread.start()
        print("自动化已启动")
    
    def stop(self):
        """停止自动化"""
        self.is_running = False
        if hasattr(self, 'automation_thread'):
            self.automation_thread.join(timeout=2)
        print("自动化已停止")

# 使用示例
if __name__ == "__main__":
    # 创建自动化实例（替换为您的目标程序名）
    automator = BackgroundAutomation("目标程序名")
    
    try:
        automator.start()
        
        # 主线程继续运行，不影响用户操作
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        automator.stop()