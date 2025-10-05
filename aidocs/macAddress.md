# 网络接口信息获取工具技术文档

## 概述

该 Python 脚本用于获取当前系统中处于活动状态的网络接口的 IP 地址和 MAC 地址。它利用 `psutil` 和 `socket` 库来收集网络接口的状态与配置信息，仅返回正在发送和接收数据的活跃网络接口的相关地址。

---

## 依赖库

- `psutil`：跨平台系统资源监控库，用于获取网络接口统计、状态和地址信息。
- `socket`：标准库，用于处理网络协议常量（如 `AF_INET` 和 `AF_PACKET`）。
- `locale`：标准库，用于获取系统默认编码（在获取 MAC 地址时使用，但实际未直接涉及编码转换）。

> ⚠️ **注意**：运行此脚本前需安装 `psutil`：
```bash
pip install psutil
```

---

## 函数说明

### `getAllAddress()`

#### 功能
获取所有**活跃网络接口的 IPv4 地址**。

#### 返回值
一个生成器（generator），每次迭代返回一个元组 `(interface_name, ip_address)`，其中：
- `interface_name`：网络接口名称（如 `eth0`, `wlan0` 等）
- `ip_address`：该接口的 IPv4 地址字符串

#### 实现逻辑
1. 使用 `psutil.net_io_counters(pernic=True)` 获取每个网络接口的数据收发统计。
2. 筛选出 **发送和接收字节数均大于 0** 的接口（即活跃接口）。
3. 使用 `psutil.net_if_stats()` 获取接口状态（如是否启用、速度等），进一步确认其可用性。
4. 遍历 `psutil.net_if_addrs()` 中的接口地址信息，查找具有 `socket.AF_INET` 家族的地址（即 IPv4 地址）。
5. 对符合条件的接口，逐个通过 `yield` 返回其名称和 IP 地址。

#### 示例输出
```python
('eth0', '192.168.1.100')
('wlan0', '192.168.0.105')
```

---

### `getAllMacAddress()`

#### 功能
获取所有**活跃网络接口的 MAC 地址**。

#### 返回值
一个生成器，每次迭代返回一个元组 `(interface_name, mac_address)`，其中：
- `interface_name`：网络接口名称
- `mac_address`：该接口的 MAC 地址字符串（格式如 `aa:bb:cc:dd:ee:ff`）

#### 实现逻辑
1. 获取系统默认编码（`locale.getdefaultlocale()[1]`），虽然当前代码中并未实际使用该编码进行解码操作，可能是冗余或预留扩展。
2. 与 `getAllAddress()` 类似，筛选出活跃且启用的网络接口。
3. 遍历接口地址信息，查找具有 `socket.AF_PACKET` 家族的地址（Linux 上表示链路层协议，包含 MAC 地址）。
4. 通过 `yield` 返回接口名和对应的 MAC 地址。

> 📌 注意：`AF_PACKET` 是 Linux 特有的；在非 Linux 平台（如 Windows）上可能不支持或行为不同。

#### 示例输出
```python
('eth0', '00:1A:2B:3C:4D:5E')
('wlan0', '02:2A:3B:4C:5D:6E')
```

---

## 主程序入口（`if __name__ == '__main__':`）

### 功能
提供简单的测试功能，调用 `getAllAddress()` 并打印结果。

#### 当前行为
- 执行 `test()` 函数，遍历 `getAllAddress()` 的结果。
- 输出格式为：`mac= (interface_name, ip_address)`
  > ❗ 注意：尽管变量名为 `mac=`，实际输出的是 IP 地址信息，属于命名错误。

#### 示例输出
```text
mac= ('eth0', '192.168.1.100')
mac= ('wlan0', '192.168.0.105')
```

> 🔴 建议修复：应将 `print("mac=",i)` 改为 `print("ip=", i)` 以避免误导。

---

## 使用示例

```python
# 获取所有活跃接口的 IPv4 地址
for iface, ip in getAllAddress():
    print(f"Interface: {iface}, IP: {ip}")

# 获取所有活跃接口的 MAC 地址
for iface, mac in getAllMacAddress():
    print(f"Interface: {iface}, MAC: {mac}")
```

---

## 注意事项与限制

| 项目 | 说明 |
|------|------|
| ✅ **跨平台兼容性** | `psutil` 支持多平台，但 `AF_PACKET` 仅适用于 Linux，因此 `getAllMacAddress()` 在 Windows/macOS 上可能无法正确获取 MAC 地址。 |
| ⚠️ **MAC 地址获取方式** | 推荐使用 `psutil.net_if_addrs()` 中 `family == -1` 或其他平台无关字段提取 MAC 地址，而非依赖 `AF_PACKET`。更健壮的方法是检查 `address` 字段并识别是否为 MAC 格式。 |
| ⚠️ **locale 编码未使用** | `locale.getdefaultlocale()[1]` 在函数中被赋值但未使用，建议移除以提高可读性。 |
| ✅ **性能表现** | 使用生成器设计，内存友好，适合大规模接口场景。 |
| ✅ **活跃判断标准** | 通过 `bytes_sent > 0 and bytes_recv > 0` 判断接口活跃，合理排除未使用的虚拟或关闭接口。 |

---

## 改进建议

1. **修复打印语句中的标签错误**：
   ```python
   print("ip=", i)  # 替代 "mac="
   ```

2. **优化 MAC 地址获取逻辑（增强跨平台支持）**：
   ```python
   if i.family == socket.AF_LINK or i.family == -1:  # BSD/macOS 使用 AF_LINK
       yield n, i.address
   ```
   或者统一使用 `psutil` 提供的更高层接口。

3. **移除无用的 locale 调用**：
   ```python
   # 删除这一行
   # coding = locale.getdefaultlocale()[1]
   ```

4. **增加异常处理和日志支持**（生产环境建议）

---

## 总结

本脚本是一个轻量级的网络接口信息探测工具，适用于需要自动发现本地活跃网络接口及其 IP/MAC 地址的场景（如设备识别、网络诊断等）。虽然存在少量命名和平台兼容性问题，但整体结构清晰、逻辑合理，易于维护和扩展。

--- 

📌 **版本要求**：Python 3.6+  
📦 **推荐用途**：自动化运维、网络配置检测、主机信息采集