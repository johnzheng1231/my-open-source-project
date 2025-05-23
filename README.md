# Python读码器GUI程序说明文档

## 一、程序概述
这是一个基于PyQt6开发的TCP客户端GUI应用程序，主要用于条码/二维码数据的采集和传输。

## 二、核心功能模块

### 1. 网络通信模块
- 实现了基于TCP Socket的客户端通信
- 使用独立的`TCPClientThread`线程类处理网络通信
- 支持自动重连和异常处理机制
- 采用信号槽机制实现线程间通信

### 2. 界面布局设计
- 采用PyQt6构建现代化GUI界面
- 主要分为三大功能区：
  * 服务器连接配置区
  * 数据发送区（支持文本和图片）
  * 通信日志显示区

### 3. 数据发送功能
- 支持JSON格式的文本数据发送
- 支持图片数据的发送（自动Base64编码）
- 提供单次发送和自动定时发送功能
- 自动添加时间戳等元数据

### 4. 图片处理功能
- 支持选择本地图片文件
- 提供图片预览功能
- 自动进行图片格式转换和压缩
- 支持添加图片附加信息

### 5. HTTP协议支持
- 自动构建HTTP POST请求
- 支持Content-Type和其他请求头配置
- 适配服务端接口规范
- 处理HTTP响应数据

### 6. 日志系统
- 实时显示操作日志
- 包含时间戳和详细信息
- 自动滚动显示最新日志

## 三、应用场景
- 条码扫描器数据采集
- 工业自动化数据上报
- 图像采集设备集成
- 测试和调试工具

## 四、技术特点
- 采用面向对象编程思想
- 代码结构清晰，模块化设计
- 异常处理完善
- 界面交互友好

## 五、总结
这是一个功能完整的工业级应用程序，适合在条码识别、工业自动化等场景中使用。程序设计合理，功能丰富，具有良好的可扩展性和维护性。
