import pygetwindow as gw
import threading
import time
import pyautogui
import cv2
import numpy as np
import win32con
import win32gui
import win32api
import os
import pytesseract
from PIL import Image
from OCROptimizer import OCROptimizer
class BackgroundAutomation:
    def __init__(self, target_process_name, target_text, threshold=0.3):
        self.target_process_name = target_process_name
        self.target_window = None
        self.is_running = False
        self.target_text = target_text  # 需要识别的目标文字
        self.threshold = threshold  # 文字匹配阈值
        self.lock = threading.Lock()
        
    def find_target_window(self):
        """查找目标程序窗口（增强版）"""
        try:
            windows = gw.getWindowsWithTitle(self.target_process_name)
            if not windows:
                return False
            
            # 1. 优先选择激活的窗口（如果存在）
            active_windows = [w for w in windows if w.isActive]
            if active_windows:
                self.target_window = active_windows[0]
                return True
            
            # 2. 若无激活窗口，选择第一个可见窗口
            visible_windows = [w for w in windows if w.visible]
            if visible_windows:
                self.target_window = visible_windows[0]
                return True
            
            # 3. 最后选择第一个找到的窗口
            self.target_window = windows[0]
            return True
            
        except Exception as e:
            print(f"查找窗口错误: {e}")
            return False
    """
    OCR文字识别：从截图中识别文字，并判断是否包含目标文字
    返回：(是否匹配, 目标文字位置中心坐标, 匹配度)
    """
    def ocr_text_recognition(self, screenshot):
        try:
            # 1. 先检查输入图像有效性（避免格式错误）
            if screenshot is None or not isinstance(screenshot, np.ndarray):
                print(f"OCR输入无效：图像为{type(screenshot)}，需numpy数组")
                return (False, None, 0.0)
            
            # 2. 轻量预处理（适配中文识别，避免过度处理导致文字模糊）
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)  # 转灰度
            gray = cv2.medianBlur(gray, 3)  # 轻微去噪（保留文字细节）
            # 自适应阈值（应对不同光照，中文文字边缘更清晰）
            thresh = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                11, 2  # 块大小11、常数2，适合中文小字体
            )
            
            # 3. OCR识别（使用你验证过的有效配置：仅中文识别）
            pil_img = Image.fromarray(thresh)
            # 关键：保留你确认生效的 lang='chi_sim'，无需额外复杂配置
            data = pytesseract.image_to_data(
                pil_img,
                output_type=pytesseract.Output.DICT,
                lang='chi_sim'  # 已验证生效的中文配置
            )
            
            # 4. 打印完整识别结果（方便调试单个汉字问题）
            print("\n===== 中文OCR完整识别结果 =====")
            valid_results = []  # 存储非空、有置信度的结果
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()  # 去除空格
                conf = data['conf'][i]  # 置信度（百分比）
                if text and conf != '-1':  # 过滤空文本和无置信度的结果
                    valid_results.append({
                        "text": text,
                        "conf": float(conf),
                        "left": data['left'][i],
                        "top": data['top'][i],
                        "width": data['width'][i],
                        "height": data['height'][i]
                    })
                    print(f"文字: '{text}', 置信度: {conf}%, 位置: ({data['left'][i]}, {data['top'][i]})")
            print("==============================\n")
            
            # 5. 合并相邻的单个汉字（解决你之前的核心问题）
            merged_results = []
            if valid_results:
                # 按文字的“顶部坐标”分组（同一行的文字顶部接近）
                # 先按top排序，确保同一行文字挨在一起
                valid_results.sort(key=lambda x: (x["top"], x["left"]))
                current_group = [valid_results[0]]  # 第一组初始文字
                
                for res in valid_results[1:]:
                    # 判断是否与当前组属于“同一行且相邻”：
                    # 1. 顶部差距 < 当前文字高度的1/2（同一行）
                    # 2. 左侧间距 < 当前文字宽度的1/2（相邻）
                    last_res = current_group[-1]
                    same_line = abs(res["top"] - last_res["top"]) < last_res["height"] / 2
                    adjacent = res["left"] - (last_res["left"] + last_res["width"]) < last_res["width"] / 2
                    
                    if same_line and adjacent:
                        current_group.append(res)  # 加入当前组，后续合并
                    else:
                        # 合并当前组的单个汉字
                        merged_text = "".join([r["text"] for r in current_group])
                        # 取组内最低置信度（确保合并后结果可靠）
                        min_conf = min([r["conf"] for r in current_group])
                        # 取组内文字的中心位置（用于后续点击）
                        avg_left = sum([r["left"] + r["width"]//2 for r in current_group]) // len(current_group)
                        avg_top = sum([r["top"] + r["height"]//2 for r in current_group]) // len(current_group)
                        
                        merged_results.append({
                            "text": merged_text,
                            "conf": min_conf,
                            "pos": (avg_left, avg_top)
                        })
                        current_group = [res]  # 开始新组
                
                # 合并最后一组
                merged_text = "".join([r["text"] for r in current_group])
                min_conf = min([r["conf"] for r in current_group])
                avg_left = sum([r["left"] + r["width"]//2 for r in current_group]) // len(current_group)
                avg_top = sum([r["top"] + r["height"]//2 for r in current_group]) // len(current_group)
                merged_results.append({
                    "text": merged_text,
                    "conf": min_conf,
                    "pos": (avg_left, avg_top)
                })
            
            # 6. 打印合并后的结果（看单个汉字是否已连成词语）
            print("\n===== 合并后中文结果 =====")
            for res in merged_results:
                print(f"合并文字: '{res['text']}', 置信度: {res['conf']:.1f}%")
            print("==========================\n")
            
            # 7. 查找目标文字（基于合并后的结果）
            target_lower = self.target_text.lower()
            for res in merged_results:
                # 置信度达标（转换为0-1范围对比）
                if res["conf"] / 100 >= self.threshold:
                    # 模糊匹配（应对合并后可能的微小误差）
                    if target_lower in res["text"].lower():
                        print(f"✅ 找到目标：'{res['text']}'（置信度：{res['conf']/100:.2f}）")
                        return (True, res["pos"], res["conf"]/100)
            
            # 未找到目标（提示最高置信度结果）
            if merged_results:
                max_conf_res = max(merged_results, key=lambda x: x["conf"])
                print(f"❌ 未找到'{self.target_text}'，最高置信度结果：'{max_conf_res['text']}'（{max_conf_res['conf']/100:.2f}）")
            else:
                print(f"❌ 未识别到任何有效中文文字")
            return (False, None, 0.0)
            
        except Exception as e:
            print(f"OCR识别错误: {e}")
            # 若报错，可临时打印当前语言包路径（辅助排查）
            try:
                print(f"当前可用语言包：{pytesseract.get_languages()}")
            except:
                pass
            return (False, None, 0.0)


    def capture_window(self):
        save_path = r"D:\Tool\VS_Code\Python_dev\WindowAutoUI\screenshot\\"
        """捕获目标窗口截图"""
        if not self.target_window:
            return None
        
        try:
            hwnd = self.target_window._hWnd
            # 1. 获取窗口客户区坐标（相对窗口自身，不含边框）
            client_rect = win32gui.GetClientRect(hwnd)  # (left=0, top=0, right=宽, bottom=高)
            client_width = client_rect[2] - client_rect[0]
            client_height = client_rect[3] - client_rect[1]
            
            # 2. 将客户区坐标转换为屏幕绝对坐标（解决边框偏移问题）
            # （窗口左上角为原点，计算客户区左上角在屏幕上的位置）
            screen_point = win32gui.ClientToScreen(hwnd, (client_rect[0], client_rect[1]))
            left = screen_point[0]
            top = screen_point[1]
            width = client_width
            height = client_height
            
            # 3. 验证坐标有效性（避免无效截图）
            if width <= 0 or height <= 0:
                print("窗口客户区大小异常，跳过截图")
                return None
            print(f"QQ客户区屏幕坐标：left={left}, top={top}, width={width}, height={height}")
            
            # 4. 后台截图（不激活窗口）
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            cv_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 5. 保存截图（带时间戳）
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            save_path = os.path.join(save_path, f"qq_screenshot_{timestamp}.jpg")
            cv2.imwrite(save_path, cv_img)
            print(f"后台截图成功（未激活窗口），保存至: {save_path}")

            # optimizer = OCROptimizer(threshold=0.5)
            # found, pos, conf = optimizer.recognize(cv_img, "发送")
            optimizer = OCROptimizer(threshold=0.5)
            found, pos, confidence = optimizer.recognize(cv_img, "发送")
            # found, pos, confidence = self.ocr_text_recognition(cv_img)
            print("OCR is start")
            if found and confidence >= self.threshold:
                print(f"识别到目标文字'{self.target_text}'，置信度: {confidence:.2f}")
                # 点击文字位置
                self.send_background_click(pos[0], pos[1])
                time.sleep(2)  # 等待点击生效
                # 执行输入并终止
                self.send_input_and_terminate()

            return cv_img
        except Exception as e:
            print(f"后台截图错误: {e}")
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
                # button_pos = self.image_recognition('D:\Tool\VS_Code\Python_dev\WindowAutoUI\dist_img\QQ_1756734518968.png', screenshot)
                # if button_pos:
                #     print(f"识别到按钮，置信度: {button_pos[2]:.2f}")
                #     self.send_background_click(button_pos[0], button_pos[1])
                #     time.sleep(2)
                #     self.send_input_and_terminate()
                #     time.sleep(1)
                
                #可以添加更多识别逻辑...
                #OCR文字识别（替换原来的模板匹配）
                # 示例：识别"发送"按钮文字并点击
                found, pos, confidence = self.ocr_text_recognition(screenshot)
                if found and confidence >= self.threshold:
                    print(f"识别到目标文字'{self.target_text}'，置信度: {confidence:.2f}")
                    # 点击文字位置
                    self.send_background_click(pos[0], pos[1])
                    time.sleep(2)  # 等待点击生效
                    # 执行输入并终止
                    self.send_input_and_terminate()
                    break  # 退出循环            




            time.sleep(0.5)  # 降低CPU使用率
    
    def send_input_and_terminate(self):
        if not self.target_window:
            return
        
        try:
            hwnd = self.target_window._hWnd
            print("识别到目标，开始输入...")

            # 确保窗口处于可接收输入状态
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.2)

            # 发送"哈哈哈"和回车
            pyautogui.typewrite("HAHAHA", interval=0.1)
            time.sleep(0.1)
            pyautogui.press('enter')
            pyautogui.press('enter')
            pyautogui.press('enter')
            print("已输入'哈哈哈'并回车")

            # 标记为已完成，让循环自然退出（而非强制join）
            self.is_running = False
            self.stop()
        except Exception as e:
            print(f"输入错误: {e}")


    def start(self):
        """启动自动化"""
        time.sleep(3)
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
        """停止自动化并退出程序（修复线程join错误）"""
        self.is_running = False
        self.target_found = True
        
        # 关键修复：只在非当前线程中执行join
        if hasattr(self, 'automation_thread') and threading.current_thread() != self.automation_thread:
            self.automation_thread.join(timeout=1)
# 使用示例
if __name__ == "__main__":
    # 创建自动化实例（替换为您的目标程序名）
    automator = BackgroundAutomation("QQ","皇")

    try:
        automator.start()
        
        # 主线程循环：只要自动化在运行就继续等待，否则退出
        while automator.is_running:
            time.sleep(1)
            
        # 当automator.is_running变为False时，程序会执行到这里然后自然退出
        print("自动化任务已完成，程序退出")
        
    except KeyboardInterrupt:
        automator.stop()
        print("用户中断，程序退出")