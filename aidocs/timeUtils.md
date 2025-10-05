# 日期与时间处理工具库技术文档

本模块提供了一系列用于日期、时间处理和格式转换的实用函数，支持日期计算、字符串与时间对象互转、模式匹配等功能，适用于数据分析、任务调度、日志处理等场景。

---

## 目录

- [1. 导入依赖](#1-导入依赖)
- [2. 全局变量](#2-全局变量)
- [3. 核心功能函数](#3-核心功能函数)
  - [3.1 时间差计算](#31-days_betweendate_str1-date_str2)
  - [3.2 当前时间相关](#32-monthfirstday--curdatetime--curdatestring--curtimestring--timestampstr)
  - [3.3 判断类函数](#33-ismonthlastday--isleapyear--is_monthend)
  - [3.4 时间戳操作](#34-timestamp--timestampsecond--timestampadd--timestampsub--timestamp2dt)
  - [3.5 日期加减运算](#35-addseconds--addmonths--addyears--dateadd--strdate_add)
  - [3.6 日期格式化与解析](#36-date2str--time2str--str2date--str2datetime--str2date)
  - [3.7 特殊日期计算](#37-firstsunday)
  - [3.8 时间对齐（StepedTimestamp）](#38-steppedtimestamp)
  - [3.9 周/季度辅助函数](#39-date_weekinyear--date_season)
  - [3.10 模式匹配](#310-is_match_pattern)

---

## 1. 导入依赖

```python
import os, sys
import time
from datetime import date, timedelta, datetime
```

> **说明**：
> - `os`, `sys`：保留接口扩展性。
> - `time`：用于时间戳和结构化时间处理。
> - `datetime`：核心日期时间处理模块。

---

## 2. 全局变量

### `leapMonthDays`, `unleapMonthDays`
```python
leapMonthDays = [0,31,29,31,30,31,30,31,31,30,31,30,31]   # 闰年各月天数（索引从1开始）
unleapMonthDays = [0,31,28,31,30,31,30,31,31,30,31,30,31] # 平年各月天数
```

> **用途**：快速查询某月最大天数，结合 `isLeapYear()` 使用。

---

## 3. 核心功能函数

### 3.1 `days_between(date_str1, date_str2)`

计算两个日期字符串之间的天数差（绝对值）。

#### 参数
| 参数        | 类型   | 描述                     |
|-------------|--------|--------------------------|
| `date_str1` | str    | 起始日期，格式 `'YYYY-MM-DD'` |
| `date_str2` | str    | 结束日期，格式 `'YYYY-MM-DD'` |

#### 返回值
- `int`：相差的天数（非负整数）

#### 示例
```python
days_between("2023-01-01", "2023-01-10")  # 返回 9
```

---

### 3.2 `monthfirstday()`

获取当前月份的第一天。

#### 返回值
- `str`：格式为 `'YYYY-MM-01'`

#### 示例
```python
monthfirstday()  # 如 '2025-04-01'
```

---

### 3.3 `curDatetime()`

获取当前精确时间的 `datetime` 对象。

#### 返回值
- `datetime.datetime`：当前系统时间

---

### 3.4 `curDateString()`

获取当前日期字符串。

#### 返回值
- `str`：格式 `'YYYY-MM-DD'`

---

### 3.5 `curTimeString()`

获取当前时间字符串（时分秒）。

#### 返回值
- `str`：格式 `'HH:MM:SS'`

---

### 3.6 `timestampstr()`

生成带毫秒的完整时间戳字符串。

#### 返回值
- `str`：格式 `'YYYY-MM-DD HH:MM:SS.fff'`

#### 示例
```python
timestampstr()  # 如 '2025-04-05 14:30:22.123'
```

---

### 3.7 `isMonthLastDay(d)`

判断给定 `datetime` 是否是当月最后一天。

#### 参数
| 参数 | 类型           | 描述             |
|------|----------------|------------------|
| `d`  | `datetime`     | 待判断的时间对象 |

#### 返回值
- `bool`：若是月末返回 `True`

#### 原理
通过加一天后判断月份是否变化。

---

### 3.8 `isLeapYear(year)`

判断是否为闰年。

> ⚠️ **注意**：原代码逻辑有误！

#### 错误分析
```python
if year % 4 == 0 and year % 100 == 0 and not (year % 400 == 0):
```
此条件仅在“能被100整除但不能被400整除”时返回 `True`，即把**平年**判为闰年。

#### 正确应为：
```python
def isLeapYear(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
```

> ✅ 建议修复该函数！

---

### 3.9 `timestamp(dt)` 和 `timeStampSecond(dt)`

将 `datetime` 转换为 Unix 时间戳。

| 函数名            | 精度       | 说明                         |
|-------------------|------------|------------------------------|
| `timestamp(dt)`   | 微秒级     | 包含 `.microsecond`          |
| `timeStampSecond(dt)` | 秒级   | 忽略微秒部分                 |

#### 参数
- `dt`: `datetime` 对象

#### 返回值
- `int`：自 1970-01-01 UTC 起的秒数

---

### 3.10 `addSeconds(dt, s)`

给时间对象增加若干秒。

#### 参数
| 参数 | 类型         | 说明               |
|------|--------------|--------------------|
| `dt` | `datetime`   | 原始时间           |
| `s`  | `int`        | 要增加的秒数       |

#### 返回值
- `datetime`：新的时间对象

---

### 3.11 `monthMaxDay(y, m)`

获取指定年份某月的最大天数（考虑闰年）。

#### 参数
| 参数 | 类型  | 说明       |
|------|-------|------------|
| `y`  | int   | 年份       |
| `m`  | int   | 月份（1~12）|

#### 返回值
- `int`：该月最多多少天

---

### 3.12 `date2str(dt=None)`

将 `datetime` 转为 `'YYYY-MM-DD'` 字符串。

#### 参数
- `dt`: 可选 `datetime` 对象；若未传则使用当前时间

#### 返回值
- `str`：格式化日期字符串

---

### 3.13 `time2str(dt)`

⚠️ **存在 Bug**

```python
return '%02d:%02d:%02d' % (dt.hour, dt, minute, dt.second)
```
错误使用了 `dt,minute`（语法错误），应为 `dt.minute`。

#### 修正版本
```python
def time2str(dt):
    return '%02d:%02d:%02d' % (dt.hour, dt.minute, dt.second)
```

---

### 3.14 `str2Date(dstr)` 和 `str2Datetime(dstr)`

#### `str2Date(dstr)`
尝试解析形如 `'YYYY-MM-DD [HH:MM:SS]'` 的字符串为 `datetime` 对象。

> **警告**：内部调用了不存在的 `ymdDate(...)` 函数前就执行拆分，且异常处理打印但不中断。

##### 改进建议：
- 统一使用标准库 `datetime.strptime`
- 移除冗余中间步骤

#### `str2Datetime(dstr)`
更稳健的实现，推荐使用。

##### 支持格式
- `'YYYY-MM-DD'`
- `'YYYY-MM-DD HH:MM:SS'`

##### 返回值
- `datetime` 对象

---

### 3.15 `ymdDate(y, m, d, H=0, M=0, S=0)`

构造 `datetime` 实例的快捷方式。

#### 参数
年、月、日、时、分、秒均可指定，默认为0。

#### 示例
```python
ymdDate(2025, 4, 5, 10, 30)  # 2025-04-05 10:30:00
```

---

### 3.16 `strdate_add(date_str, days=0, months=0, years=0)`

对日期字符串进行加减操作并返回新字符串。

#### 参数
支持同时添加天、月、年。

#### 执行顺序
1. 加 `days`
2. 加 `months`
3. 加 `years`

> 自动处理跨月/跨年边界，并确保不会出现非法日期（如 2月30日）

#### 示例
```python
strdate_add("2024-01-31", months=1)  # 返回 "2024-02-29"（自动调整到月底）
```

---

### 3.17 `addMonths(dt, months)` 和 `addYears(dt, years)`

#### `addMonths(dt, months)`
安全地增加月份，自动修正超出范围的日期（如 1月31日 +1月 → 2月29日或28日）

#### `addYears(dt, years)`
同理，考虑闰年导致2月可能只有28天。

---

### 3.18 `dateAdd(dt, days=0, months=0, years=0)`

综合日期加法入口函数，按顺序应用增量。

---

### 3.19 `firstSunday(dt)`

返回大于等于输入日期的第一个周日。

> 注意：Python 中 `weekday()` 返回 0~6 表示周一至周日。  
> 因此 `(7 - weekday()) % 7` 更准确。

当前实现假设 `weekday()==6` 是周六？实际应为周日。

#### 存疑逻辑
```python
f = dt.weekday()
if f < 6:
    return dt + timedelta(7 - f)
else:
    return dt
```
这表示：
- 若不是周日（即 0~5），则加 `(7-f)` 天
- 若是周日（6），直接返回

✅ 实际上这是正确的：`weekday()` 返回 0=周一 ... 6=周日

所以当 `f=6`（周日）时无需移动。

✔️ 此函数逻辑正确。

---

### 3.20 时间格式常量与函数

```python
DTFORMAT = '%Y%m%d %H%M%S'
```

#### `getCurrentTimeStamp()`
获取当前时间按 `DTFORMAT` 格式的字符串。

#### `TimeStamp(t)`
将 `struct_time` 格式化为上述格式。

#### `timestampAdd(ts1, ts2)`
将两个时间字符串相加（`ts2` 可为秒数或时间字符串）

> ❌ 存在类型判断错误：
```python
if type(ts2)=='' :
```
应改为：
```python
if isinstance(ts2, str):
```

否则会出错。

#### `timestampSub(ts1, ts2)`
计算两个 `DTFORMAT` 时间之间的秒数差。

---

### 3.21 `StepedTimestamp(baseTs, ts, step)`

将时间 `ts` 对齐到以 `baseTs` 为起点、步长为 `step` 秒的时间网格。

#### 应用场景
- 数据采样对齐
- 定时任务触发点归一化

#### 参数
| 参数     | 类型   | 说明                   |
|----------|--------|------------------------|
| `baseTs` | str    | 基准时间（DTFORMAT）   |
| `ts`     | str    | 当前时间               |
| `step`   | int    | 步长（秒）             |

#### 返回值
- 最近的对齐时间点（向上或向下取整）

---

### 3.22 `timestamp2dt(t)`

将 Unix 时间戳（秒）转为 `datetime` 对象。

---

### 3.23 `date_weekinyear(date_str)`

获取日期所在年的第几周（ISO 周编号）。

#### 返回值
- `str`：`'YYYY-W'` 形式，其中 `W` 为两位周数

> 使用 `%W`（基于周一开始的周），而非 ISO 标准 `%U` 或 `isocalendar()`

---

### 3.24 `date_season(date_str)`

根据月份划分季节：

| 月份     | 季度 |
|----------|------|
| 1–3      | 1    |
| 4–6      | 2    |
| 7–9      | 3    |
| 10–12    | 4    |

#### 返回值
- `str`：`'YYYYQ'`，如 `'20251'` 表示2025年第1季度

---

### 3.25 `str2date(sd)`

将 `'YYYY-MM-DD'` 字符串转为 `date` 对象。

#### 示例
```python
str2date("2025-04-05")  # 返回 date(2025, 4, 5)
```

---

### 3.26 `is_monthend(dt)`

判断日期是否为月末。

#### 参数
- `dt`: `str` 或 `date` 对象

#### 方法
+1天后看月份是否改变。

---

### 3.27 `is_match_pattern(pattern, strdate)`

判断某日期是否符合特定调度模式。

#### 支持的模式

| 模式         | 含义                             | 示例                    |
|--------------|----------------------------------|-------------------------|
| `'D'`        | 每日触发                         | `'D'`                   |
| `'W[0-6]'`   | 每周星期X（0=周一...6=周日）     | `'W0'`=每周一            |
| `'M0'`       | 每月最后一天                     | `'M0'`                  |
| `'Mdd'`      | 每月第dd天                       | `'M15'`=每月15日         |
| `'Sx-dd'`    | 每季度第x月第dd天                | `'S1-01'`=季初第一天     |
| `'Ym-dd'`    | 每年m月dd日                      | `'Y12-25'`=每年12月25日  |

#### 返回值
- `bool`：是否匹配

#### 注意事项
- `Sx-dd` 中 `x %= 4`，即循环每4个月视为一个季度
- 调试信息 `print(f'{m=}-{d=}, ...')` 建议移除生产环境

---

## 4. 已知问题汇总（建议修复）

| 函数名         | 问题描述                                       | 建议修改 |
|----------------|------------------------------------------------|----------|
| `isLeapYear`   | 条件反向，导致逻辑错误                         | ✅ 重写   |
| `time2str`     | 引用 `dt,minute` 报语法错误                    | ✅ 修复拼写 |
| `timestampAdd` | `type(ts2)==''` 永远为假                        | ✅ 改为 `isinstance(ts2, str)` |
| `str2Date`     | 使用未定义函数 `ymdDate` 在 try 外部可能发生错误 | ✅ 重构或删除冗余逻辑 |
| `str2Datetime` | 不支持毫秒                                     | ✅ 可拓展支持 |

---

## 5. 使用示例

```python
# 计算间隔
print(days_between("2023-01-01", "2023-12-31"))  # 364

# 获取今天
print(curDateString())  # 2025-04-05

# 加一个月
print(strdate_add("2024-01-31", months=1))  # 2024-02-29

# 判断是否为月末
print(is_monthend("2025-04-30"))  # True

# 匹配每周五
print(is_match_pattern("W4", "2025-04-11"))  # True（假设是周五）
```

---

## 6. 总结

本工具包提供了丰富的日期时间操作能力，适合嵌入数据处理流水线或定时任务系统中。尽管存在少量 bug 和可优化空间，整体设计清晰、功能完整。

> 📌 推荐在正式使用前进行单元测试，并优先修复已知缺陷。

--- 

**版本**: v1.0  
**作者**: Auto-generated Documentation  
**更新时间**: 2025-04-05