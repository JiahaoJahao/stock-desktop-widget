# 美股桌面挂件

Windows 桌面悬浮看盘工具：美股 / 加密货币自选、盘前盘中盘后、置顶、透明度、开机自启。

## 下载

到 [Releases](https://github.com/JiahaoJahao/stock-desktop-widget/releases) 下载 `StockWidget.exe`，双击即可运行（无需安装 Python）。

> Windows 可能对**未签名**的 exe 弹出 SmartScreen 提示（常见于 PyInstaller 打包），点「仍要运行」即可。源码开源可审计，不含恶意行为。

## 功能

- 自选美股 / ETF / 加密货币（Yahoo Finance），行内显示公司 logo
- 盘前 / 开盘 / 盘后状态与倒计时
- 拖拽股票行调整顺序；拖边角缩放，位置与大小自动记住
- 本地时间：默认跟随系统时区，也可在设置里指定
- 默认透明度 95%；开机自启、始终置顶、锁定位置
- 桌面快捷方式 + 应用图标

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
