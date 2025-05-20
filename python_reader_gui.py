import sys
import os
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'.\venv\Lib\site-packages\PyQt6\Qt6\plugins'
import socket
import json
import time
import base64
import threading
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QTextEdit, QFileDialog, 
                             QGroupBox, QGridLayout, QCheckBox, QSpinBox)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize

class TCPClientThread(QThread):
    """TCP客户端线程，处理与服务器的通信"""
    
    # 信号定义
    connected = pyqtSignal(bool, str)
    message_received = pyqtSignal(str)
    log_message = pyqtSignal(str)
    connection_error = pyqtSignal(str)
    
    def __init__(self, server, port):
        super().__init__()
        self.server = server
        self.port = port
        self.client = None
        self.is_running = False
        self.is_connected = False
    
    def run(self):
        """线程主函数"""
        self.is_running = True
        self.connect_to_server()
        
        while self.is_running:
            if self.is_connected:
                time.sleep(0.1)  # 避免CPU占用过高
            else:
                time.sleep(1)
                if self.is_running:
                    self.connect_to_server()
    
    def connect_to_server(self):
        """连接到服务器"""
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(5)  # 设置超时
            self.client.connect((self.server, self.port))
            self.is_connected = True
            self.connected.emit(True, f"已连接到 {self.server}:{self.port}")
            self.log_message.emit(f"TCP连接成功: {self.server}:{self.port}")
        except Exception as e:
            self.is_connected = False
            self.connected.emit(False, f"连接失败: {str(e)}")
            self.log_message.emit(f"TCP连接失败: {str(e)}")
    
    def send_data(self, data):
        """发送数据到服务器"""
        if not self.is_connected:
            self.log_message.emit("未连接到服务器，无法发送数据")
            return False, "未连接到服务器"
        
        try:
            self.client.sendall(data.encode('utf-8'))
            # 接收响应
            response = self.client.recv(4096).decode('utf-8')
            self.message_received.emit(response)
            return True, response
        except Exception as e:
            self.is_connected = False
            self.connection_error.emit(str(e))
            self.log_message.emit(f"发送数据出错: {str(e)}")
            return False, str(e)
    
    def send_binary_data(self, data):
        """发送二进制数据到服务器"""
        if not self.is_connected:
            self.log_message.emit("未连接到服务器，无法发送数据")
            return False, "未连接到服务器"
        
        try:
            # 直接发送二进制数据
            if isinstance(data, bytearray) or isinstance(data, bytes):
                self.client.sendall(data)
            else:
                self.client.sendall(data)
            
            # 接收响应
            response = self.client.recv(4096).decode('utf-8')
            self.message_received.emit(response)
            return True, response
        except Exception as e:
            self.is_connected = False
            self.connection_error.emit(str(e))
            self.log_message.emit(f"发送二进制数据出错: {str(e)}")
            return False, str(e)
    
    def stop(self):
        """停止线程"""
        self.is_running = False
        if self.client:
            try:
                self.client.close()
            except:
                pass

class ReaderGUI(QWidget):
    """读码器GUI主类"""
    
    def __init__(self):
        super().__init__()
        self.tcp_thread = None
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.send_auto_data)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 窗口设置
        self.setWindowTitle("发送Http数据脚本")
        self.setMinimumSize(800, 600)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 连接区域
        connection_group = QGroupBox("服务器连接")
        connection_layout = QGridLayout()
        
        self.server_label = QLabel("服务器地址:")
        self.server_input = QLineEdit("110.40.135.195")
        self.port_label = QLabel("端口:")
        self.port_input = QLineEdit("8081")
        self.connect_btn = QPushButton("连接")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connection_status = QLabel("未连接")
        self.connection_status.setStyleSheet("color: red")
        
        connection_layout.addWidget(self.server_label, 0, 0)
        connection_layout.addWidget(self.server_input, 0, 1)
        connection_layout.addWidget(self.port_label, 0, 2)
        connection_layout.addWidget(self.port_input, 0, 3)
        connection_layout.addWidget(self.connect_btn, 0, 4)
        connection_layout.addWidget(self.connection_status, 0, 5)
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # 数据发送区域
        data_group = QGroupBox("数据发送")
        data_layout = QVBoxLayout()
        
        # 文本数据区域
        text_box = QGroupBox("文本数据")
        text_layout = QVBoxLayout()
        
        self.text_data_input = QTextEdit()
        self.text_data_input.setPlaceholderText("在此输入要发送的JSON数据")
        self.text_data_input.setText('{\n    "device_id": "scanner-001",\n    "data": "6923450657713",\n    "codeType": "barcode",\n    "parseResult": "Success",\n    "result": "OK"\n   }')
        self.text_data_input.setMaximumHeight(150)
        
        send_layout = QHBoxLayout()
        self.send_once_btn = QPushButton("发送一次")
        self.send_once_btn.clicked.connect(self.send_text_once)
        
        self.auto_send_check = QCheckBox("自动发送")
        self.auto_send_check.toggled.connect(self.toggle_auto_send)
        
        self.interval_label = QLabel("间隔(秒):")
        self.interval_spinner = QSpinBox()
        self.interval_spinner.setRange(1, 60)
        self.interval_spinner.setValue(3)
        
        send_layout.addWidget(self.send_once_btn)
        send_layout.addWidget(self.auto_send_check)
        send_layout.addWidget(self.interval_label)
        send_layout.addWidget(self.interval_spinner)
        send_layout.addStretch()
        
        text_layout.addWidget(self.text_data_input)
        text_layout.addLayout(send_layout)
        text_box.setLayout(text_layout)
        data_layout.addWidget(text_box)
        
        # 图片数据区域
        image_box = QGroupBox("图片数据")
        image_layout = QGridLayout()
        
        self.image_path_label = QLabel("未选择图片")
        self.select_image_btn = QPushButton("选择图片")
        self.select_image_btn.clicked.connect(self.select_image)
        
        self.image_preview = QLabel("图片预览")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(150)
        self.image_preview.setStyleSheet("border: 1px solid #cccccc;")
        
        self.send_image_btn = QPushButton("发送图片")
        self.send_image_btn.clicked.connect(self.send_image)
        self.send_image_btn.setEnabled(False)
        
        self.image_message_input = QLineEdit("图片附加信息")
        
        image_layout.addWidget(self.select_image_btn, 0, 0)
        image_layout.addWidget(self.image_path_label, 0, 1, 1, 3)
        image_layout.addWidget(self.image_preview, 1, 0, 1, 4)
        image_layout.addWidget(QLabel("附加信息:"), 2, 0)
        image_layout.addWidget(self.image_message_input, 2, 1)
        image_layout.addWidget(self.send_image_btn, 2, 2, 1, 2)
        
        image_box.setLayout(image_layout)
        data_layout.addWidget(image_box)
        
        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group)
        
        # 日志区域
        log_group = QGroupBox("通信日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 设置主布局
        self.setLayout(main_layout)
        
        # 添加初始日志
        self.add_log("程序已启动，请连接到服务器")
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.tcp_thread and self.tcp_thread.is_running:
            # 断开连接
            self.tcp_thread.stop()
            self.tcp_thread.wait()
            self.tcp_thread = None
            self.connect_btn.setText("连接")
            self.connection_status.setText("已断开")
            self.connection_status.setStyleSheet("color: red")
            self.add_log("已断开连接")
        else:
            # 建立连接
            try:
                server = self.server_input.text()
                port = int(self.port_input.text())
                
                self.tcp_thread = TCPClientThread(server, port)
                self.tcp_thread.connected.connect(self.on_connection_status)
                self.tcp_thread.message_received.connect(self.on_message_received)
                self.tcp_thread.log_message.connect(self.add_log)
                self.tcp_thread.connection_error.connect(self.on_connection_error)
                self.tcp_thread.start()
                
                self.connect_btn.setText("断开")
                self.add_log(f"正在连接到 {server}:{port}...")
            except Exception as e:
                self.add_log(f"连接出错: {str(e)}")
    
    def on_connection_status(self, is_connected, message):
        """连接状态变化处理"""
        if is_connected:
            self.connection_status.setText("已连接")
            self.connection_status.setStyleSheet("color: green")
        else:
            self.connection_status.setText("未连接")
            self.connection_status.setStyleSheet("color: red")
            self.connect_btn.setText("连接")
            if self.tcp_thread:
                self.tcp_thread.stop()
                self.tcp_thread = None
        
        self.add_log(message)
    
    def on_connection_error(self, error_msg):
        """连接错误处理"""
        self.connection_status.setText("连接错误")
        self.connection_status.setStyleSheet("color: red")
        self.add_log(f"连接错误: {error_msg}")
    
    def on_message_received(self, message):
        """收到消息处理"""
        self.add_log(f"收到响应:\n{message}")
    
    def select_image(self):
        """选择图片"""
        try:
            # 在PyQt6中不需要使用QFileDialog.Options()
            filepath, _ = QFileDialog.getOpenFileName(
                self, "选择图片", "", 
                "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*)"
            )
            
            if filepath:
                self.image_path_label.setText(filepath)
                try:
                    # 显示预览
                    pixmap = QPixmap(filepath)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(QSize(300, 150), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.image_preview.setPixmap(pixmap)
                        self.send_image_btn.setEnabled(True)
                    else:
                        self.image_preview.setText("无法预览图片")
                        self.send_image_btn.setEnabled(False)
                except Exception as e:
                    self.add_log(f"图片预览失败: {str(e)}")
                    self.image_preview.setText("图片预览失败")
                    self.send_image_btn.setEnabled(False)
        except Exception as e:
            self.add_log(f"选择图片操作失败: {str(e)}")
            self.image_preview.setText("选择图片操作失败")
    
    def send_text_once(self):
        """发送一次文本数据"""
        if not self.tcp_thread or not self.tcp_thread.is_connected:
            self.add_log("未连接到服务器，无法发送数据")
            return
        
        try:
            # 获取用户输入的JSON数据
            text_data = self.text_data_input.toPlainText()
            data = json.loads(text_data)
            
            # 添加时间戳
            if "timestamp" not in data:
                data["timestamp"] = time.time()
            
            # 创建HTTP请求
            http_request = self.create_http_request(data)
            
            # 发送数据
            self.add_log(f"发送数据:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
            success, response = self.tcp_thread.send_data(http_request)
            
            if not success:
                self.add_log(f"发送失败: {response}")
        except json.JSONDecodeError:
            self.add_log("JSON格式错误，无法解析")
        except Exception as e:
            self.add_log(f"发送出错: {str(e)}")
    
    def toggle_auto_send(self, checked):
        """切换自动发送状态"""
        if checked:
            interval = self.interval_spinner.value() * 1000  # 转换为毫秒
            self.auto_timer.start(interval)
            self.add_log(f"已开启自动发送，间隔 {interval/1000} 秒")
        else:
            self.auto_timer.stop()
            self.add_log("已停止自动发送")
    
    def send_auto_data(self):
        """自动发送数据"""
        if not self.tcp_thread or not self.tcp_thread.is_connected:
            self.auto_send_check.setChecked(False)
            self.add_log("未连接到服务器，已停止自动发送")
            return
        
        try:
            # 获取基本数据模板
            text_data = self.text_data_input.toPlainText()
            data = json.loads(text_data)
            
            # 添加时间戳和自动标识
            data["timestamp"] = time.time()
            if "data" in data and isinstance(data["data"], str):
                data["data"] += f" (自动发送 {time.strftime('%H:%M:%S')})"
            
            # 创建HTTP请求
            http_request = self.create_http_request(data)
            
            # 发送数据
            self.add_log(f"自动发送数据:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
            success, response = self.tcp_thread.send_data(http_request)
            
            if not success:
                self.add_log(f"自动发送失败: {response}")
                self.auto_send_check.setChecked(False)
        except Exception as e:
            self.add_log(f"自动发送出错: {str(e)}")
            self.auto_send_check.setChecked(False)
    
    def send_image(self):
        """发送图片数据"""
        if not self.tcp_thread or not self.tcp_thread.is_connected:
            self.add_log("未连接到服务器，无法发送数据")
            return
        
        image_path = self.image_path_label.text()
        if image_path == "未选择图片":
            self.add_log("未选择图片，无法发送")
            return
        
        try:
            # 直接以JSON方式发送
            # 读取图片并转换为Base64
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
            
            base64_data = base64.b64encode(img_data).decode('utf-8')
            
            # 获取文件扩展名和MIME类型
            file_ext = os.path.splitext(image_path)[1][1:].lower()
            mime_type = f"image/{file_ext}"
            if file_ext == 'jpg':
                mime_type = "image/jpeg"
            
            # 创建图片数据 - 确保字段名与index.html兼容
            image_data = {
                "deviceName": "py-reader-gui-001",
                "receivedData": f"IMAGE-{os.path.basename(image_path)}",
                "codeType": "QR Code",
                "parseResult": "Success",
                "resultStatus": "OK",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),  # 更改为可读时间格式
                "message": self.image_message_input.text(),
                "imageData": base64_data,
                "imageMimeType": mime_type
            }
            
            # 创建HTTP请求
            json_data = json.dumps(image_data)
            http_request = (
                f"POST /image HTTP/1.1\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(json_data)}\r\n"
                f"Host: {self.server_input.text()}:{self.port_input.text()}\r\n"
                f"Connection: keep-alive\r\n"
                f"\r\n"
                f"{json_data}"
            )
            
            # 发送数据
            self.add_log(f"发送图片数据:\n路径: {image_path}\n大小: {len(base64_data)} 字符\n附加信息: {image_data['message']}")
            success, response = self.tcp_thread.send_data(http_request)
            
            if not success:
                self.add_log(f"发送图片失败: {response}")
        except Exception as e:
            self.add_log(f"发送图片出错: {str(e)}")
    
    def create_http_request(self, data):
        """创建HTTP请求"""
        # 确保有device_id字段，修改为与index.html中接收逻辑匹配的字段名
        if not "deviceName" in data and "device_id" in data:
            data["deviceName"] = data["device_id"]
        
        if not "timestamp" in data:
            data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            
        # 增加适配字段，确保与index.html的处理逻辑匹配
        if "data" in data and not "receivedData" in data:
            data["receivedData"] = data["data"]
            
        if not "codeType" in data and "code_type" in data:
            data["codeType"] = data["code_type"]
            
        if not "parseResult" in data:
            data["parseResult"] = "Success"
            
        if not "resultStatus" in data and "result" in data:
            data["resultStatus"] = data["result"]
        elif not "resultStatus" in data:
            data["resultStatus"] = "OK"
        
        json_data = json.dumps(data)
        http_request = (
            f"POST /data HTTP/1.1\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(json_data)}\r\n"
            f"Host: {self.server_input.text()}:{self.port_input.text()}\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n"
            f"{json_data}"
        )
        return http_request
    
    def add_log(self, message):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # 滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """关闭窗口事件处理"""
        if self.tcp_thread:
            self.tcp_thread.stop()
            self.tcp_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ReaderGUI()
    gui.show()
    sys.exit(app.exec()) 