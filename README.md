# 美股桌面挂件

Windows 桌面悬浮看盘工具：美股 / 加密货币自选、盘前盘中盘后、置顶、透明度、开机自启。

## 下载

到 [Releases](https://github.com/JiahaoJahao/stock-desktop-widget/releases) 下载 `StockWidget.exe`，双击即可运行（无需安装 Python）。

## 功能

- 自选美股 / ETF / 加密货币（Yahoo Finance）
- 盘前 / 开盘 / 盘后状态与倒计时
- 本地时间：默认跟随系统时区，也可在设置里指定
- 默认透明度 70%，滚轮可调；位置与宽度自动记住
- 开机自启、始终置顶、锁定位置

## 源码运行

```bat
pip install -r requirements.txt
pythonw stock_widget.py
```

或双击 `run_stock.vbs`。

## 打包 exe

```bat
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name StockWidget stock_widget.py
```

产物在 `dist\StockWidget.exe`。

## 声明

行情数据来自 Yahoo Finance，仅供参考，不构成投资建议。与 Elon Musk / X 官方无关。
