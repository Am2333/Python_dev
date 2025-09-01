import cv2
import numpy as np
import pytesseract
from PIL import Image
import re

class OCROptimizer:
    def __init__(self, threshold=0.6):
        self.threshold = threshold
        # 针对不同场景的预处理参数（可根据实际图像调整）
        self.preprocess_params = {
            "low_contrast": {"clipLimit": 2.0, "tileGridSize": (8, 8)},
            "high_noise": {"kernel_size": (3, 3), "sigmaX": 1.0},
            "blurry": {"ksize": (-1, -1), "sigma": 1.5}
        }

    def analyze_image(self, img):
        """分析图像特征，判断适用的预处理策略"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # 计算对比度（标准差越小对比度越低）
        contrast = np.std(gray)
        # 计算噪声水平（通过拉普拉斯算子）
        noise = cv2.Laplacian(gray, cv2.CV_64F).var()
        # 计算清晰度（边缘检测响应）
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        strategies = []
        if contrast < 30:
            strategies.append("low_contrast")
        if noise > 100:
            strategies.append("high_noise")
        if sharpness < 50:
            strategies.append("blurry")
            
        return strategies

    def preprocess_image(self, img):
        """自适应预处理：根据图像特征组合优化策略"""
        # 1. 转为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # 2. 分析图像特征，获取优化策略
        strategies = self.analyze_image(img)
        
        # 3. 针对性优化
        if "high_noise" in strategies:
            # 高斯模糊去噪
            params = self.preprocess_params["high_noise"]
            gray = cv2.GaussianBlur(gray, 
                                   (params["kernel_size"][0], params["kernel_size"][1]), 
                                   params["sigmaX"])
        
        if "low_contrast" in strategies:
            # 对比度受限自适应直方图均衡化（增强文字与背景差异）
            params = self.preprocess_params["low_contrast"]
            clahe = cv2.createCLAHE(clipLimit=params["clipLimit"], 
                                   tileGridSize=(params["tileGridSize"][0], params["tileGridSize"][1]))
            gray = clahe.apply(gray)
        
        if "blurry" in strategies:
            # 锐化处理（增强文字边缘）
            params = self.preprocess_params["blurry"]
            gray = cv2.GaussianBlur(gray, params["ksize"], params["sigma"])
            gray = cv2.addWeighted(gray, 1.5, gray, -0.5, 0)
        
        # 4. 二值化（根据图像亮度自动选择阈值方向）
        mean_brightness = np.mean(gray)
        if mean_brightness > 127:  # 偏亮图像用普通二值化
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        else:  # 偏暗图像用自适应二值化
            thresh = cv2.adaptiveThreshold(gray, 255,
                                          cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY_INV,
                                          15, 4)
        
        # 5. 形态学优化（修复文字断裂）
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        return thresh

    def recognize(self, img, target_text):
        """优化的OCR识别流程"""
        try:
            # 1. 高级预处理
            processed_img = self.preprocess_image(img)
            
            # 2. 保存预处理后的图像（用于调试分析）
            cv2.imwrite("processed_ocr_image.jpg", processed_img)
            
            # 3. 优化的Tesseract配置
            # 中文+英文混合识别，按段落布局解析
            custom_config = r'''
                --tessdata-dir "C:\Program Files\Tesseract-OCR\tessdata"
                -l chi_sim
                --psm 3  # 自动分页布局分析（适合复杂排版）
                --oem 3  # 使用LSTM+传统引擎混合模式
                -c preserve_interword_spaces=1  # 保留词间空格
                -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789一二三四五六七八九十大中小年月日时分秒发送确定取消
            '''
            
            # 4. 执行识别
            pil_img = Image.fromarray(processed_img)
            data = pytesseract.image_to_data(
                pil_img,
                output_type=pytesseract.Output.DICT,
                config=custom_config
            )
            
            # 5. 后处理：过滤无效字符并合并结果
            results = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if not text:
                    continue
                # 过滤乱码（保留常见中文字符和基本符号）
                cleaned_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。,.;;：:？?！!]', '', text)
                if cleaned_text:
                    results.append({
                        "text": cleaned_text,
                        "confidence": float(data['conf'][i])/100,
                        "left": data['left'][i],
                        "top": data['top'][i],
                        "width": data['width'][i],
                        "height": data['height'][i]
                    })
            
            # 6. 查找目标文字（支持模糊匹配）
            target_lower = target_text.lower()
            best_match = None
            for res in results:
                if res["confidence"] < self.threshold:
                    continue
                if target_lower in res["text"].lower():
                    # 计算中心坐标
                    center_x = res["left"] + res["width"]//2
                    center_y = res["top"] + res["height"]//2
                    if not best_match or res["confidence"] > best_match["confidence"]:
                        best_match = {
                            "found": True,
                            "pos": (center_x, center_y),
                            "confidence": res["confidence"],
                            "text": res["text"]
                        }
            
            if best_match:
                print(f"识别成功：'{best_match['text']}'（置信度：{best_match['confidence']:.2f}）")
                return (True, best_match["pos"], best_match["confidence"])
            
            # 未找到目标时返回最高置信度结果
            if results:
                top_result = max(results, key=lambda x: x["confidence"])
                print(f"未找到目标，但识别到：'{top_result['text']}'（最高置信度：{top_result['confidence']:.2f}）")
            return (False, None, 0.0)
            
        except Exception as e:
            print(f"OCR优化识别错误：{e}")
            return (False, None, 0.0)

# 使用示例
# optimizer = OCROptimizer(threshold=0.5)
# found, pos, conf = optimizer.recognize(cv_img, "发送")
