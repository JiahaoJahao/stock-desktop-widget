# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import webbrowser
import requests
import time
import json
import re
import ctypes

try:
    import datetime
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint, QEvent
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizeGrip, QDialog, QLineEdit, QScrollArea, QMessageBox, QCompleter, QMenu,
    QAction, QSlider, QCheckBox, QDoubleSpinBox, QFrame, QSizePolicy, QComboBox,
)
from PyQt5.QtGui import QGuiApplication, QCursor, QFont

def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = _app_dir()
PID_FILE = os.path.join(APP_DIR, "widget.pid")
CONFIG_FILE = os.path.join(APP_DIR, "stocks_config.json")
UI_FILE = os.path.join(APP_DIR, "widget_ui.json")
RUN_VBS = os.path.join(APP_DIR, "run_stock.vbs")
AUTOSTART_NAME = "StockDesktopWidget"
APP_VERSION = "1.2.0"
MIN_W = 280
MIN_H = 120
RESIZE_MARGIN = 8
# edge flags for frameless resize
EDGE_LEFT = 1
EDGE_RIGHT = 2
EDGE_TOP = 4
EDGE_BOTTOM = 8

DEFAULT_UI = {
    "x": 1560,
    "y": -1075,
    "width": 480,
    "height": 360,
    "screen_name": r"\\.\DISPLAY1",
    "rel_x": 1433,
    "rel_y": 5,
    "always_on_top": True,
    "position_locked": False,
    "opacity": 0.7,
    "alert_pct": 4.0,
    "local_tz": "auto",
}

LOCAL_TZ_CHOICES = [
    ("auto", "自动（系统时区）"),
    ("Australia/Sydney", "悉尼"),
    ("Australia/Melbourne", "墨尔本"),
    ("Asia/Shanghai", "北京 / 上海"),
    ("Asia/Hong_Kong", "香港"),
    ("Asia/Tokyo", "东京"),
    ("Asia/Singapore", "新加坡"),
    ("Europe/London", "伦敦"),
    ("America/Los_Angeles", "洛杉矶"),
    ("America/New_York", "纽约"),
]

POPULAR_STOCKS_DB = {
    "AAPL": "苹果", "MSFT": "微软", "GOOGL": "谷歌", "AMZN": "亚马逊",
    "NVDA": "英伟达", "TSLA": "特斯拉", "META": "Meta", "TSM": "台积电",
    "SPCX": "SpaceX", "BABA": "阿里巴巴", "JD": "京东", "PDD": "拼多多",
    "NIO": "蔚来", "LI": "理想汽车", "XPEV": "小鹏汽车", "AMD": "AMD",
    "INTC": "英特尔", "QCOM": "高通", "NFLX": "奈飞", "DIS": "迪士尼",
    "BA": "波音", "KO": "可口可乐", "PEP": "百事可乐", "WMT": "沃尔玛",
    "COST": "开市客", "MCD": "麦当劳", "SBUX": "星巴克", "NKE": "耐克",
    "V": "Visa", "MA": "万事达", "JPM": "摩根大通", "BAC": "美国银行",
    "GS": "高盛", "BRK-B": "伯克希尔", "JNJ": "强生", "UNH": "联合健康",
    "PFE": "辉瑞", "MRNA": "Moderna", "UBER": "优步", "ABNB": "爱彼迎",
    "COIN": "Coinbase", "PLTR": "Palantir", "SQ": "Block", "PYPL": "PayPal",
    "CRM": "赛富时", "SNOW": "Snowflake", "ZM": "Zoom", "ARM": "ARM",
    "ASML": "阿斯麦", "AVGO": "博通", "LRCX": "泛林集团", "AMAT": "应用材料",
    "MU": "美光科技", "TXN": "德州仪器", "CSCO": "思科", "IBM": "IBM",
    "ORCL": "甲骨文", "ADBE": "Adobe", "NOW": "ServiceNow", "INTU": "Intuit",
    "QQQ": "纳指ETF", "SPY": "标普ETF", "DIA": "道指ETF", "TQQQ": "纳指三倍做多",
    "SOXL": "半导体三倍", "SMH": "半导体ETF", "IWM": "罗素2000",
    "BTC-USD": "比特币", "ETH-USD": "以太坊", "SOL-USD": "Solana",
}

CRYPTO_ALIASES = {
    "BTC": "BTC-USD", "BTCUSD": "BTC-USD", "XBT": "BTC-USD", "BITCOIN": "BTC-USD",
    "ETH": "ETH-USD", "ETHUSD": "ETH-USD", "ETHEREUM": "ETH-USD",
    "SOL": "SOL-USD", "SOLUSD": "SOL-USD",
}

CRYPTO_NAMES = {
    "BTC-USD": "比特币",
    "ETH-USD": "以太坊",
    "SOL-USD": "Solana",
}

DEFAULT_STOCKS = [
    {"name": "SpaceX", "ticker": "SPCX"},
    {"name": "Apple", "ticker": "AAPL"},
    {"name": "Microsoft", "ticker": "MSFT"},
    {"name": "Google", "ticker": "GOOGL"},
    {"name": "NVIDIA", "ticker": "NVDA"},
]

US_MARKET_HOLIDAYS = {
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
    "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24",
}

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
UP = "#FF5C5C"
DOWN = "#3DFF7A"
MUTED = "#C8C8D0"
UI_FONT = "Microsoft YaHei UI"
NUM_FONT = "Consolas, Cascadia Mono, Microsoft YaHei UI"
TEXT = "#FFFFFF"
TEXT_DIM = "#D8D8E0"


def load_json(path, fallback):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                merged = fallback.copy()
                merged.update(data)
                return merged
            return data
        except Exception:
            return fallback.copy() if isinstance(fallback, dict) else fallback
    return fallback.copy() if isinstance(fallback, dict) else fallback


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


def normalize_ticker(ticker):
    raw = (ticker or "").strip().upper().replace(" ", "")
    return CRYPTO_ALIASES.get(raw, raw)


def display_ticker(ticker):
    if ticker.endswith("-USD"):
        return ticker[:-4]
    return ticker


def is_crypto(ticker):
    return ticker.endswith("-USD") or ticker in CRYPTO_ALIASES


def load_stocks():
    stocks = load_json(CONFIG_FILE, DEFAULT_STOCKS)
    if not isinstance(stocks, list) or not stocks:
        return DEFAULT_STOCKS.copy()
    changed = False
    cleaned = []
    seen = set()
    for stock in stocks:
        ticker = normalize_ticker(stock.get("ticker", ""))
        if not ticker or ticker in seen:
            changed = True
            continue
        name = stock.get("name") or ticker
        if ticker in CRYPTO_NAMES and name in (ticker, display_ticker(ticker), "BTC", "ETH", "SOL"):
            name = CRYPTO_NAMES[ticker]
            changed = True
        if ticker != stock.get("ticker"):
            changed = True
        cleaned.append({"name": name, "ticker": ticker})
        seen.add(ticker)
    if changed:
        save_stocks(cleaned)
    return cleaned


def save_stocks(stocks):
    save_json(CONFIG_FILE, stocks)


def load_ui():
    return load_json(UI_FILE, DEFAULT_UI)


def save_ui(ui):
    save_json(UI_FILE, ui)


def autostart_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'wscript.exe "{RUN_VBS}"'


def is_autostart_enabled():
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        ) as key:
            value, _ = winreg.QueryValueEx(key, AUTOSTART_NAME)
            return bool(value)
    except Exception:
        return False


def set_autostart(enabled):
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, autostart_command())
            else:
                try:
                    winreg.DeleteValue(key, AUTOSTART_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def now_local(tz_name="auto"):
    if HAS_PYTZ and tz_name and tz_name != "auto":
        try:
            return datetime.datetime.now(pytz.timezone(tz_name))
        except Exception:
            pass
    try:
        return datetime.datetime.now().astimezone()
    except Exception:
        return datetime.datetime.now()


def kill_previous_instances():
    my_pid = os.getpid()
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = f.read().strip()
            if old_pid.isdigit() and int(old_pid) != my_pid:
                subprocess.call(
                    ["taskkill", "/F", "/PID", old_pid],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(my_pid))
    except Exception:
        pass


def now_new_york():
    if HAS_PYTZ:
        try:
            return datetime.datetime.now(pytz.timezone("America/New_York"))
        except Exception:
            pass
    return None


def market_session():
    ny = now_new_york()
    if ny is None:
        return "行情", 8000, "#E6E6EE"
    if ny.weekday() >= 5 or ny.strftime("%Y-%m-%d") in US_MARKET_HOLIDAYS:
        return "休市", 60000, "#D0D0D8"
    minutes = ny.hour * 60 + ny.minute
    pre, open_, close, after = 4 * 60, 9 * 60 + 30, 16 * 60, 20 * 60
    if pre <= minutes < open_:
        return "盘前", 8000, "#FFD166"
    if open_ <= minutes < close:
        return "开盘", 5000, "#3DFF7A"
    if close <= minutes < after:
        return "盘后", 8000, "#7ADCFF"
    return "休市", 60000, "#D0D0D8"


def _fmt_hms(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def next_open_datetime(ny):
    candidate = ny.replace(hour=9, minute=30, second=0, microsecond=0)
    if ny >= candidate:
        candidate += datetime.timedelta(days=1)
    for _ in range(10):
        if candidate.weekday() < 5 and candidate.strftime("%Y-%m-%d") not in US_MARKET_HOLIDAYS:
            return candidate
        candidate += datetime.timedelta(days=1)
        candidate = candidate.replace(hour=9, minute=30, second=0, microsecond=0)
    return candidate


def session_countdown_text(local_tz="auto"):
    local_dt = now_local(local_tz)
    local = local_dt.strftime("%H:%M:%S")
    ny = now_new_york()
    session, interval, color = market_session()
    if ny is None:
        return session, f"本地 {local}", interval, color
    now_s = ny.hour * 3600 + ny.minute * 60 + ny.second
    if session == "盘前":
        remain = "开盘 " + _fmt_hms((9 * 3600 + 30 * 60) - now_s)
    elif session == "开盘":
        remain = "收盘 " + _fmt_hms((16 * 3600) - now_s)
    elif session == "盘后":
        remain = "剩余 " + _fmt_hms((20 * 3600) - now_s)
    else:
        nxt = next_open_datetime(ny)
        remain = "开盘 " + _fmt_hms((nxt - ny).total_seconds())
    hint = f"本地 {local} | 美东 {ny.strftime('%H:%M:%S')} | {remain}"
    return session, hint, interval, color


def fmt_price(value):
    if value is None:
        return "--"
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "--"


def fmt_pct(value):
    if value is None:
        return "--"
    try:
        return f"{float(value):+.2f}%"
    except Exception:
        return "--"


def native_set_pos(hwnd, x, y, w, h, always_on_top):
    if sys.platform != "win32" or not hwnd:
        return
    try:
        insert_after = HWND_TOPMOST if always_on_top else HWND_NOTOPMOST
        ctypes.windll.user32.SetWindowPos(
            int(hwnd), insert_after, int(x), int(y), int(w), int(h),
            SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
    except Exception:
        pass


class StockFetchThread(QThread):
    data_fetched = pyqtSignal(list, bool)

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.crumb = None
        self.stocks_to_fetch = []

    def set_stocks(self, stocks):
        self.stocks_to_fetch = list(stocks)

    def _init_yahoo_auth(self):
        for home in ("https://fc.yahoo.com", "https://finance.yahoo.com"):
            try:
                self.session.get(home, timeout=8)
                res = self.session.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=8)
                if res.status_code == 200 and "<html>" not in res.text.lower():
                    self.crumb = res.text.strip()
                    return
            except Exception:
                continue
        self.crumb = None

    def _quote_url(self, host, tickers):
        url = f"https://{host}/v7/finance/quote?symbols={tickers}&_nocache={int(time.time() * 1000)}"
        if self.crumb:
            url += f"&crumb={self.crumb}"
        return url

    def _fetch_map(self, tickers):
        for host in ("query2.finance.yahoo.com", "query1.finance.yahoo.com"):
            try:
                response = self.session.get(self._quote_url(host, tickers), timeout=8)
                if response.status_code == 200:
                    results = response.json().get("quoteResponse", {}).get("result", [])
                    return {item["symbol"]: item for item in results}, True
                self.crumb = None
            except Exception:
                self.crumb = None
        return {}, False

    def _parse_item(self, stock, data):
        ticker = stock["ticker"]
        empty = {
            "ticker": ticker, "name": stock["name"],
            "pre_price": "--", "pre_change": "--", "pre_up": True,
            "reg_price": "未上市" if ticker == "SPCX" else "N/A",
            "reg_change": "--", "reg_up": True, "reg_pct": 0.0,
            "post_price": "--", "post_change": "--", "post_up": True,
            "raw_price": None,
        }
        if ticker == "SPCX" and not data:
            return empty
        if not data:
            raise ValueError("missing")

        pre_price = data.get("preMarketPrice")
        pre_change_pct = data.get("preMarketChangePercent")
        reg_price = data.get("regularMarketPrice")
        reg_change_pct = data.get("regularMarketChangePercent")
        post_price = data.get("postMarketPrice")
        post_change_pct = data.get("postMarketChangePercent")
        return {
            "ticker": ticker, "name": stock["name"],
            "pre_price": fmt_price(pre_price) if pre_price else "--",
            "pre_change": fmt_pct(pre_change_pct) if pre_price else "--",
            "pre_up": (pre_change_pct or 0) >= 0,
            "reg_price": fmt_price(reg_price),
            "reg_change": fmt_pct(reg_change_pct),
            "reg_up": (reg_change_pct or 0) >= 0,
            "reg_pct": float(reg_change_pct or 0),
            "post_price": fmt_price(post_price) if post_price else "--",
            "post_change": fmt_pct(post_change_pct) if post_price else "--",
            "post_up": (post_change_pct or 0) >= 0,
            "raw_price": reg_price,
        }

    def _run(self):
        stocks = list(self.stocks_to_fetch)
        if not stocks:
            self.data_fetched.emit([], True)
            return
        if not self.crumb:
            self._init_yahoo_auth()

        tickers_str = ",".join(stock["ticker"] for stock in stocks)
        result_map, ok = self._fetch_map(tickers_str)
        if not ok and not self.crumb:
            self._init_yahoo_auth()
            result_map, ok = self._fetch_map(tickers_str)

        watch = []
        for stock in stocks:
            try:
                data = result_map.get(stock["ticker"]) or result_map.get(display_ticker(stock["ticker"]))
                watch.append(self._parse_item(stock, data))
            except Exception:
                watch.append(self._parse_item(stock, None) if stock["ticker"] == "SPCX" else {
                    "ticker": stock["ticker"], "name": stock["name"],
                    "pre_price": "--", "pre_change": "--", "pre_up": True,
                    "reg_price": "N/A", "reg_change": "--", "reg_up": True, "reg_pct": 0.0,
                    "post_price": "--", "post_change": "--", "post_up": True,
                    "raw_price": None,
                })

        all_na = bool(watch) and all(item["reg_price"] in ("N/A", "未上市") for item in watch)
        self.data_fetched.emit(watch, ok and not all_na)

    def run(self):
        try:
            self._run()
        except Exception:
            import traceback
            traceback.print_exc()
            self.data_fetched.emit([], False)


class IconButton(QPushButton):
    def __init__(self, text, tooltip, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setFixedSize(28, 24)
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.12);
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI';
            }
            QPushButton:hover { background: rgba(255,255,255,0.22); color: white; }
            QPushButton:checked { background: rgba(61,255,122,0.28); color: #3DFF7A; }
        """)


def _price_column():
    box = QVBoxLayout()
    box.setSpacing(0)
    box.setContentsMargins(0, 0, 0, 0)
    price = QLabel("--")
    chg = QLabel("--")
    price.setAlignment(Qt.AlignCenter)
    chg.setAlignment(Qt.AlignCenter)
    box.addWidget(price)
    box.addWidget(chg)
    return box, price, chg


class StockRow(QFrame):
    remove_requested = pyqtSignal(str)

    def __init__(self, stock_info, parent=None):
        super().__init__(parent)
        self.ticker = stock_info["ticker"]
        self.display_name = stock_info["name"]
        self._last_price = None
        self.setObjectName("StockRow")
        self.setFixedHeight(58)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame#StockRow {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 10px;
            }
            QFrame#StockRow:hover {
                background: rgba(255,255,255,0.13);
                border: 1px solid rgba(255,255,255,0.22);
            }
        """)
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 6, 8, 6)
        root.setSpacing(4)

        name_box = QVBoxLayout()
        name_box.setSpacing(0)
        self.name_label = QLabel(self.display_name)
        self.name_label.setStyleSheet(f"font-size:15px; font-weight:700; color:{TEXT}; font-family:'{UI_FONT}';")
        self.meta_label = QLabel(display_ticker(self.ticker))
        self.meta_label.setStyleSheet(f"font-size:12px; color:{TEXT_DIM}; font-family:'{UI_FONT}';")
        name_box.addWidget(self.name_label)
        name_box.addWidget(self.meta_label)

        pre_box, self.pre_price, self.pre_chg = _price_column()
        mid_box, self.reg_price, self.reg_chg = _price_column()
        post_box, self.post_price, self.post_chg = _price_column()
        self.reg_price.setText("加载中")

        root.addLayout(name_box, 3)
        root.addLayout(pre_box, 3)
        root.addLayout(mid_box, 3)
        root.addLayout(post_box, 3)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

    def _menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu{background:#1F1F24;color:#EEE;border:1px solid #333;} QMenu::item:selected{background:#333;}")
        open_act = menu.addAction("打开 Yahoo 行情")
        copy_act = menu.addAction("复制代码")
        remove_act = menu.addAction("从自选移除")
        chosen = menu.exec_(self.mapToGlobal(pos))
        if chosen == open_act:
            webbrowser.open(f"https://finance.yahoo.com/quote/{self.ticker}")
        elif chosen == copy_act:
            QApplication.clipboard().setText(self.ticker)
        elif chosen == remove_act:
            self.remove_requested.emit(self.ticker)

    def flash(self, up):
        color = "255,90,95" if up else "34,197,94"
        self.setStyleSheet(f"""
            QFrame#StockRow {{
                background: rgba({color},0.20);
                border: 1px solid rgba({color},0.45);
                border-radius: 10px;
            }}
        """)
        QTimer.singleShot(520, self._reset_style)

    def _reset_style(self):
        self.setStyleSheet("""
            QFrame#StockRow {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 10px;
            }
            QFrame#StockRow:hover {
                background: rgba(255,255,255,0.13);
                border: 1px solid rgba(255,255,255,0.22);
            }
        """)

    def _paint_pair(self, price_label, chg_label, price, change, up, active):
        empty = price in ("--", "N/A", "未上市", None)
        color = MUTED if empty else (UP if up else DOWN)
        size = 17 if active and not empty else 15
        weight = 800 if active else 700
        price_label.setText(price)
        price_label.setStyleSheet(
            f"font-size:{size}px; font-weight:{weight}; color:{color}; font-family:Consolas;"
        )
        chg_label.setText(change)
        chg_label.setStyleSheet(
            f"font-size:13px; font-weight:700; color:{color}; font-family:Consolas;"
        )

    def update_data(self, item, session="行情"):
        self.meta_label.setText(display_ticker(self.ticker))
        live_mid = is_crypto(self.ticker) or session == "开盘"
        self._paint_pair(self.pre_price, self.pre_chg, item["pre_price"], item["pre_change"], item["pre_up"], session == "盘前" and not is_crypto(self.ticker))
        self._paint_pair(self.reg_price, self.reg_chg, item["reg_price"], item["reg_change"], item["reg_up"], live_mid)
        self._paint_pair(self.post_price, self.post_chg, item["post_price"], item["post_change"], item["post_up"], session == "盘后" and not is_crypto(self.ticker))
        self.setToolTip(
            f"{self.display_name} ({self.ticker})\n"
            f"盘前 {item['pre_price']}  {item['pre_change']}\n"
            f"盘中 {item['reg_price']}  {item['reg_change']}\n"
            f"盘后 {item['post_price']}  {item['post_change']}"
        )
        raw = item.get("raw_price")
        if raw is not None and self._last_price is not None and abs(raw - self._last_price) > 1e-9:
            self.flash(raw >= self._last_price)
        self._last_price = raw


class SettingsDialog(QDialog):
    def __init__(self, current_stocks, ui, parent=None):
        super().__init__(parent)
        self.stocks = [dict(s) for s in current_stocks]
        self.ui = ui.copy()
        self.setWindowTitle("挂件设置")
        self.setFixedSize(400, 580)
        self.setStyleSheet("""
            QDialog { background-color: #141418; color: #E8E8ED; }
            QLabel { color: #E8E8ED; font-size: 13px; }
            QLineEdit, QDoubleSpinBox {
                background:#23232A; color:#FFF; border:1px solid #3A3A44;
                border-radius:6px; padding:6px; font-size:13px;
            }
            QPushButton { background:#2C2C34; color:#FFF; border:none; border-radius:6px; padding:6px 12px; font-weight:bold; }
            QPushButton:hover { background:#3A3A44; }
            QPushButton#DeleteBtn { background:transparent; color:#FF5A5F; }
            QPushButton#SaveBtn { background:#16A34A; }
            QPushButton#SaveBtn:hover { background:#22C55E; }
            QScrollArea { border:1px solid #2A2A32; background:#101014; border-radius:8px; }
            QWidget#ScrollWidget { background:#101014; }
            QCheckBox { color:#D0D0D6; spacing:8px; }
            QSlider::groove:horizontal { height:4px; background:#333; border-radius:2px; }
            QSlider::handle:horizontal { background:#EEE; width:12px; margin:-5px 0; border-radius:6px; }
        """)
        layout = QVBoxLayout(self)
        add_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索 特斯拉 / TSLA，或直接输入代码")
        completer_list = [f"{name} ({ticker})" for ticker, name in POPULAR_STOCKS_DB.items()]
        completer = QCompleter(completer_list)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setMaxVisibleItems(8)
        completer.popup().setStyleSheet("QListView{background:#23232A;color:#FFF;border:1px solid #444;}")
        self.search_input.setCompleter(completer)
        self.search_input.returnPressed.connect(self.add_stock)
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_stock)
        add_layout.addWidget(self.search_input, 4)
        add_layout.addWidget(add_btn, 1)
        layout.addLayout(add_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("ScrollWidget")
        self.list_layout = QVBoxLayout(self.scroll_widget)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area, 1)
        self.refresh_list()

        self.autostart = QCheckBox("开机自动启动")
        self.autostart.setChecked(is_autostart_enabled())
        layout.addWidget(self.autostart)

        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("透明度"))
        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(40, 100)
        self.opacity.setValue(int(round(float(ui.get("opacity", 0.7)) * 100)))
        self.op_val = QLabel(f"{self.opacity.value()}%")
        self.opacity.valueChanged.connect(lambda v: self.op_val.setText(f"{v}%"))
        op_row.addWidget(self.opacity, 1)
        op_row.addWidget(self.op_val)
        layout.addLayout(op_row)

        tz_row = QHBoxLayout()
        tz_row.addWidget(QLabel("本地时区"))
        self.local_tz = QComboBox()
        self.local_tz.setStyleSheet(
            "QComboBox{background:#23232A;color:#FFF;border:1px solid #3A3A44;border-radius:6px;padding:4px 8px;}"
            "QComboBox QAbstractItemView{background:#23232A;color:#FFF;selection-background-color:#3A3A44;}"
        )
        current_tz = ui.get("local_tz", "auto") or "auto"
        for key, label in LOCAL_TZ_CHOICES:
            self.local_tz.addItem(label, key)
        idx = next((i for i, (key, _) in enumerate(LOCAL_TZ_CHOICES) if key == current_tz), 0)
        self.local_tz.setCurrentIndex(idx)
        tz_row.addWidget(self.local_tz, 1)
        layout.addLayout(tz_row)

        al_row = QHBoxLayout()
        al_row.addWidget(QLabel("异动提醒"))
        self.alert = QDoubleSpinBox()
        self.alert.setRange(0.5, 30.0)
        self.alert.setSingleStep(0.5)
        self.alert.setSuffix(" %")
        self.alert.setValue(float(ui.get("alert_pct", 4.0)))
        al_row.addWidget(self.alert)
        al_row.addStretch()
        layout.addLayout(al_row)

        hint = QLabel("本地时间默认跟系统；也可在上方指定时区。滚轮调透明度 · 位置与宽度会自动记住")
        hint.setStyleSheet("color:#7C7C86; font-size:11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        bottom = QHBoxLayout()
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        save = QPushButton("保存")
        save.setObjectName("SaveBtn")
        save.clicked.connect(self.accept)
        bottom.addStretch()
        bottom.addWidget(cancel)
        bottom.addWidget(save)
        layout.addLayout(bottom)

    def add_stock(self):
        text = self.search_input.text().strip()
        if not text:
            return
        match = re.match(r"^(.*?)\s*\((.*?)\)$", text)
        if match:
            name, ticker = match.group(1).strip(), match.group(2).strip().upper()
        else:
            ticker = text.upper()
            name = POPULAR_STOCKS_DB.get(ticker, ticker)
        ticker = normalize_ticker(ticker)
        name = CRYPTO_NAMES.get(ticker, POPULAR_STOCKS_DB.get(ticker, name))
        if any(s["ticker"] == ticker for s in self.stocks):
            QMessageBox.warning(self, "重复", "该股票已在自选中")
            return
        self.stocks.append({"name": name, "ticker": ticker})
        self.search_input.clear()
        self.refresh_list()

    def remove_stock(self, ticker):
        self.stocks = [s for s in self.stocks if s["ticker"] != ticker]
        self.refresh_list()

    def move_stock(self, ticker, delta):
        idx = next((i for i, s in enumerate(self.stocks) if s["ticker"] == ticker), -1)
        if idx < 0:
            return
        new_idx = max(0, min(len(self.stocks) - 1, idx + delta))
        self.stocks[idx], self.stocks[new_idx] = self.stocks[new_idx], self.stocks[idx]
        self.refresh_list()

    def refresh_list(self):
        for i in reversed(range(self.list_layout.count())):
            widget = self.list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        for stock in self.stocks:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(6, 4, 6, 4)
            lbl = QLabel(f"{stock['name']}  ({stock['ticker']})")
            up = QPushButton("上")
            down = QPushButton("下")
            delete = QPushButton("移除")
            delete.setObjectName("DeleteBtn")
            up.setFixedWidth(32)
            down.setFixedWidth(32)
            delete.setFixedWidth(48)
            up.clicked.connect(lambda _, t=stock["ticker"]: self.move_stock(t, -1))
            down.clicked.connect(lambda _, t=stock["ticker"]: self.move_stock(t, 1))
            delete.clicked.connect(lambda _, t=stock["ticker"]: self.remove_stock(t))
            row_layout.addWidget(lbl, 1)
            row_layout.addWidget(up)
            row_layout.addWidget(down)
            row_layout.addWidget(delete)
            self.list_layout.addWidget(row)

    def result_ui(self):
        data = self.ui.copy()
        data["opacity"] = self.opacity.value() / 100.0
        data["alert_pct"] = float(self.alert.value())
        data["local_tz"] = self.local_tz.currentData() or "auto"
        return data

    def apply_autostart(self):
        wanted = self.autostart.isChecked()
        if wanted == is_autostart_enabled():
            return True
        ok = set_autostart(wanted)
        if not ok:
            QMessageBox.warning(self, "开机自启", "写入开机启动项失败，请检查权限后重试。")
            self.autostart.setChecked(is_autostart_enabled())
        return ok


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_stocks = load_stocks()
        self.ui = load_ui()
        self.last_data = []
        self._ready_to_save = False
        self._dragging = False
        self._resizing = False
        self._resize_edges = 0
        self._resize_start_geo = None
        self._resize_start_global = QPoint()
        self._press_global = QPoint()
        self._press_offset = QPoint()
        self._press_row = None
        self._alerted = set()
        self._target = None
        self.initUI()
        self._target = self._resolve_geometry()
        self.apply_window_flags()
        self.setWindowOpacity(float(self.ui.get("opacity", 1.0)))

        self.thread = StockFetchThread()
        self.thread.set_stocks(self.current_stocks)
        self.thread.data_fetched.connect(self.on_data_fetched)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fetch_data)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._tick_header)
        self.clock_timer.start(1000)
        self._tick_header()

        self.guard_timer = QTimer(self)
        self.guard_timer.timeout.connect(self._startup_guard)
        self._guard_until = time.monotonic() + 2.0
        self.guard_timer.start(80)
        self.fetch_data()

    def initUI(self):
        self.setWindowTitle("美股挂件")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(MIN_W, MIN_H)
        init_w = max(MIN_W, int(self.ui.get("width", 480)))
        init_h = max(MIN_H, int(self.ui.get("height") or self._content_height()))
        self.resize(init_w, init_h)
        self.setStyleSheet("""
            QWidget { font-family: 'Microsoft YaHei UI'; color: #FFFFFF; }
            QWidget#MainContainer {
                background-color: rgb(18, 18, 22);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.20);
            }
            QLabel { color: #FFFFFF; }
            QLabel#HintLabel { font-size:13px; color:#FFFFFF; font-weight:700; }
            QMenu { background:#1C1C22; color:#FFFFFF; border:1px solid #444; }
            QMenu::item:selected { background:#3A3A44; }
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: transparent; width: 8px; margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.25); border-radius: 4px; min-height: 24px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        container.setObjectName("MainContainer")
        container.setMouseTracking(True)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QHBoxLayout()
        self.session_pill = QLabel("行情")
        self.session_pill.setAlignment(Qt.AlignCenter)
        self.session_pill.setFixedHeight(26)
        self.header_hint = QLabel("初始化...")
        self.header_hint.setObjectName("HintLabel")
        self.header_hint.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.header_hint.setMinimumWidth(70)
        self.alert_label = QLabel("")
        self.alert_label.setStyleSheet("color:#FFD166; font-size:13px; font-weight:bold;")

        settings_btn = IconButton("设", "设置自选、透明度和开机自启")
        settings_btn.clicked.connect(self.open_settings)
        close_btn = IconButton("×", "关闭")
        close_btn.setStyleSheet(close_btn.styleSheet() + "QPushButton:hover{color:#FF5A5F;}")
        close_btn.clicked.connect(self.close)

        title.addWidget(self.session_pill)
        title.addSpacing(8)
        title.addWidget(self.header_hint, 1)
        title.addWidget(self.alert_label)
        title.addWidget(settings_btn)
        title.addWidget(close_btn)
        layout.addLayout(title)

        cols = QHBoxLayout()
        cols.setContentsMargins(10, 0, 8, 0)
        self.col_headers = {}
        for key, text, stretch in (
            ("name", "自选", 3),
            ("pre", "盘前", 3),
            ("mid", "盘中", 3),
            ("post", "盘后", 3),
        ):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter if key != "name" else Qt.AlignLeft | Qt.AlignVCenter)
            lbl.setStyleSheet(f"color:{TEXT_DIM}; font-size:12px; font-weight:700;")
            self.col_headers[key] = lbl
            cols.addWidget(lbl, stretch)
        layout.addLayout(cols)

        self.rows_widget = QWidget()
        self.rows_widget.setMouseTracking(True)
        self.rows_layout = QVBoxLayout(self.rows_widget)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(6)
        self.rows_layout.addStretch(1)
        self.rows_scroll = QScrollArea()
        self.rows_scroll.setWidgetResizable(True)
        self.rows_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rows_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.rows_scroll.setFrameShape(QFrame.NoFrame)
        self.rows_scroll.setWidget(self.rows_widget)
        self.rows_scroll.setMouseTracking(True)
        layout.addWidget(self.rows_scroll, 1)
        self.rows = {}
        self.render_rows()

        footer = QHBoxLayout()
        self.footer_label = QLabel("拖边角缩放 · 滚轮调透明度")
        self.footer_label.setStyleSheet("color:#C8C8D0; font-size:11px;")
        footer.addWidget(self.footer_label)
        footer.addStretch()
        grip = QSizeGrip(self)
        grip.setToolTip("拖动调整大小")
        footer.addWidget(grip, 0, Qt.AlignRight | Qt.AlignBottom)
        layout.addLayout(footer)
        outer.addWidget(container)
        self._chrome = container
        container.installEventFilter(self)
        self.rows_scroll.viewport().installEventFilter(self)
        self.rows_widget.installEventFilter(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def apply_window_flags(self):
        flags = Qt.FramelessWindowHint | Qt.Tool
        if self.ui.get("always_on_top", True):
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _tick_header(self):
        session, hint, interval, color = session_countdown_text(self.ui.get("local_tz", "auto"))
        self.session_pill.setText(f"  {session}  ")
        self.session_pill.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background: rgba(255,255,255,0.05);
                border: 1px solid {color}55;
                border-radius: 9px;
                font-size: 13px;
                font-weight: 800;
                padding: 0 6px;
            }}
        """)
        self.header_hint.setText(hint)
        self._paint_col_headers(session)
        if self.timer.interval() != interval or not self.timer.isActive():
            self.timer.start(interval)

    def _paint_col_headers(self, session):
        mapping = {"盘前": "pre", "开盘": "mid", "盘后": "post"}
        active = mapping.get(session)
        for key, lbl in self.col_headers.items():
            if key == "name":
                lbl.setStyleSheet(f"color:{TEXT_DIM}; font-size:12px; font-weight:700;")
            elif key == active:
                lbl.setStyleSheet(f"color:{TEXT}; font-size:13px; font-weight:800;")
            else:
                lbl.setStyleSheet(f"color:{TEXT_DIM}; font-size:12px; font-weight:700;")

    def _content_height(self):
        n = max(1, len(self.current_stocks))
        header = 68
        rows = n * 58 + max(0, n - 1) * 6
        footer = 22
        padding = 28
        return header + rows + footer + padding

    def _pick_screen(self):
        screens = QGuiApplication.screens()
        wanted = self.ui.get("screen_name")
        for screen in screens:
            if screen.name() == wanted:
                return screen
        for screen in screens:
            if screen.geometry().y() < 0:
                return screen
        for screen in screens:
            if screen != QGuiApplication.primaryScreen():
                return screen
        return QGuiApplication.primaryScreen()

    def _resolve_geometry(self):
        width = max(MIN_W, int(self.ui.get("width", 480)))
        saved_h = self.ui.get("height")
        height = max(MIN_H, int(saved_h) if saved_h else self._content_height())
        screen = self._pick_screen()
        geo = screen.geometry() if screen else QGuiApplication.primaryScreen().geometry()
        rel_x, rel_y = self.ui.get("rel_x"), self.ui.get("rel_y")
        if rel_x is None or rel_y is None:
            x = int(self.ui.get("x", geo.x() + geo.width() - width - 20))
            y = int(self.ui.get("y", geo.y() + 20))
        else:
            x = geo.x() + int(rel_x)
            y = geo.y() + int(rel_y)
        x = min(max(x, geo.x() - 40), geo.x() + geo.width() - 80)
        y = min(max(y, geo.y() - 40), geo.y() + geo.height() - 80)
        max_w = max(MIN_W, geo.x() + geo.width() - x - 8)
        max_h = max(MIN_H, geo.y() + geo.height() - y - 8)
        width = min(width, max_w)
        height = min(height, max_h)
        return {"x": int(x), "y": int(y), "w": width, "h": height}

    def apply_saved_geometry(self):
        target = self._target or self._resolve_geometry()
        screen = self._pick_screen()
        geo = screen.geometry() if screen else QGuiApplication.primaryScreen().geometry()
        max_w = max(MIN_W, geo.x() + geo.width() - target["x"] - 8)
        max_h = max(MIN_H, geo.y() + geo.height() - target["y"] - 8)
        target["w"] = min(max(MIN_W, target["w"]), max_w)
        target["h"] = min(max(MIN_H, target["h"]), max_h)
        self.setMinimumSize(MIN_W, MIN_H)
        self.resize(target["w"], target["h"])
        self.move(target["x"], target["y"])
        native_set_pos(
            int(self.winId()) if self.winId() else 0,
            target["x"], target["y"], target["w"], target["h"],
            self.ui.get("always_on_top", True),
        )

    def _is_near_target(self):
        target = self._target
        if not target:
            return True
        return abs(self.x() - target["x"]) < 40 and abs(self.y() - target["y"]) < 40

    def _startup_guard(self):
        if not self._is_near_target():
            self.apply_saved_geometry()
        if time.monotonic() >= self._guard_until:
            self.guard_timer.stop()
            self._ready_to_save = True
            self.persist_geometry()

    def persist_geometry(self, force=False):
        if not self._ready_to_save and not force:
            return
        screen = QGuiApplication.screenAt(self.frameGeometry().center()) or self._pick_screen()
        geo = screen.geometry()
        self.ui["x"] = int(self.x())
        self.ui["y"] = int(self.y())
        self.ui["screen_name"] = screen.name()
        self.ui["rel_x"] = int(self.x() - geo.x())
        self.ui["rel_y"] = int(self.y() - geo.y())
        max_w = max(MIN_W, geo.width() - self.ui["rel_x"] - 8)
        max_h = max(MIN_H, geo.height() - self.ui["rel_y"] - 8)
        self.ui["width"] = min(max(MIN_W, int(self.width())), max_w)
        self.ui["height"] = min(max(MIN_H, int(self.height())), max_h)
        save_ui(self.ui)
        self._target = {
            "x": self.ui["x"], "y": self.ui["y"],
            "w": self.ui["width"], "h": self.ui["height"],
        }

    def render_rows(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        self.rows.clear()
        for stock in self.current_stocks:
            row = StockRow(stock)
            row.setMouseTracking(True)
            row.installEventFilter(self)
            row.remove_requested.connect(self.remove_ticker)
            self.rows[stock["ticker"]] = row
            self.rows_layout.addWidget(row)
        self.rows_layout.addStretch(1)
        # Keep user-chosen size; only seed height if never saved
        width = max(MIN_W, int(self.ui.get("width", self.width() or 480)))
        if self.ui.get("height"):
            height = max(MIN_H, int(self.ui["height"]))
        else:
            height = max(MIN_H, self._content_height())
        if self.width() < MIN_W or self.height() < MIN_H:
            self.resize(width, height)
        if self._target:
            self._target["w"] = max(MIN_W, int(self.width() or width))
            self._target["h"] = max(MIN_H, int(self.height() or height))

    def remove_ticker(self, ticker):
        self.current_stocks = [s for s in self.current_stocks if s["ticker"] != ticker]
        save_stocks(self.current_stocks)
        self.render_rows()
        self.thread.set_stocks(self.current_stocks)
        self.apply_saved_geometry()
        self.fetch_data()

    def open_settings(self):
        dialog = SettingsDialog(self.current_stocks, self.ui, self)
        if dialog.exec_() == QDialog.Accepted:
            dialog.apply_autostart()
            save_stocks(dialog.stocks)
            self.current_stocks = dialog.stocks
            self.ui.update(dialog.result_ui())
            self.ui.pop("compact", None)
            save_ui(self.ui)
            self.setWindowOpacity(float(self.ui.get("opacity", 1.0)))
            self.render_rows()
            self.thread.set_stocks(self.current_stocks)
            self.apply_saved_geometry()
            self.fetch_data()

    def open_context_menu(self, pos):
        menu = QMenu(self)
        pin = QAction("始终置顶", self, checkable=True)
        pin.setChecked(bool(self.ui.get("always_on_top", True)))
        pin.triggered.connect(self.toggle_always_on_top)
        lock = QAction("锁定位置", self, checkable=True)
        lock.setChecked(bool(self.ui.get("position_locked", False)))
        lock.triggered.connect(self.toggle_lock)
        auto = QAction("开机自启", self, checkable=True)
        auto.setChecked(is_autostart_enabled())
        auto.triggered.connect(self.toggle_autostart)
        snap = QAction("钉到当前屏右上角", self)
        snap.triggered.connect(self.snap_top_right)
        settings = QAction("设置", self)
        settings.triggered.connect(self.open_settings)
        quit_act = QAction("退出", self)
        quit_act.triggered.connect(self.close)
        menu.addAction(pin)
        menu.addAction(lock)
        menu.addAction(auto)
        menu.addAction(snap)
        menu.addSeparator()
        menu.addAction(settings)
        menu.addAction(quit_act)
        menu.exec_(self.mapToGlobal(pos))

    def toggle_always_on_top(self, checked):
        self.ui["always_on_top"] = bool(checked)
        save_ui(self.ui)
        self.apply_window_flags()
        self.show()
        self.apply_saved_geometry()

    def toggle_lock(self, checked):
        self.ui["position_locked"] = bool(checked)
        save_ui(self.ui)

    def toggle_autostart(self, checked):
        if not set_autostart(bool(checked)):
            QMessageBox.warning(self, "开机自启", "写入开机启动项失败，请检查权限后重试。")

    def snap_top_right(self):
        screen = QGuiApplication.screenAt(QCursor.pos()) or self._pick_screen()
        geo = screen.availableGeometry()
        width, height = max(MIN_W, self.width()), max(MIN_H, self.height())
        x = geo.x() + geo.width() - width - 12
        y = geo.y() + 8
        self._target = {"x": x, "y": y, "w": width, "h": height}
        self.apply_saved_geometry()
        self._ready_to_save = True
        self.persist_geometry(force=True)

    def _hit_resize_edges(self, pos):
        edges = 0
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        if x <= RESIZE_MARGIN:
            edges |= EDGE_LEFT
        elif x >= w - RESIZE_MARGIN:
            edges |= EDGE_RIGHT
        if y <= RESIZE_MARGIN:
            edges |= EDGE_TOP
        elif y >= h - RESIZE_MARGIN:
            edges |= EDGE_BOTTOM
        return edges

    def _cursor_for_edges(self, edges):
        if edges in (EDGE_LEFT | EDGE_TOP, EDGE_RIGHT | EDGE_BOTTOM):
            return Qt.SizeFDiagCursor
        if edges in (EDGE_RIGHT | EDGE_TOP, EDGE_LEFT | EDGE_BOTTOM):
            return Qt.SizeBDiagCursor
        if edges in (EDGE_LEFT, EDGE_RIGHT):
            return Qt.SizeHorCursor
        if edges in (EDGE_TOP, EDGE_BOTTOM):
            return Qt.SizeVerCursor
        return Qt.ArrowCursor

    def _apply_resize(self, global_pos):
        if not self._resize_start_geo or not self._resize_edges:
            return
        dx = global_pos.x() - self._resize_start_global.x()
        dy = global_pos.y() - self._resize_start_global.y()
        geo = self._resize_start_geo
        x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
        if self._resize_edges & EDGE_LEFT:
            new_w = max(MIN_W, w - dx)
            x = x + (w - new_w)
            w = new_w
        if self._resize_edges & EDGE_RIGHT:
            w = max(MIN_W, w + dx)
        if self._resize_edges & EDGE_TOP:
            new_h = max(MIN_H, h - dy)
            y = y + (h - new_h)
            h = new_h
        if self._resize_edges & EDGE_BOTTOM:
            h = max(MIN_H, h + dy)
        self.setGeometry(x, y, w, h)

    def fetch_data(self):
        self._tick_header()
        if not self.thread.isRunning():
            self.thread.start()

    def on_data_fetched(self, data_list, ok):
        try:
            self._apply_quotes(data_list, ok)
        except Exception:
            import traceback
            traceback.print_exc()

    def _apply_quotes(self, data_list, ok):
        if not data_list:
            self.header_hint.setText("暂无自选，点右上角「设」添加")
            return
        if ok:
            self.last_data = data_list
            self.footer_label.setText("拖边角缩放 · 滚轮调透明度")
        else:
            self.footer_label.setText("刷新失败，仍显示上次价格")
            data_list = self.last_data or data_list

        session, _, _ = market_session()
        alerts = []
        thresh = float(self.ui.get("alert_pct", 4.0))
        for item in data_list:
            row = self.rows.get(item["ticker"])
            if not row:
                continue
            row.update_data(item, session)
            pct = abs(item.get("reg_pct", 0))
            if pct >= thresh:
                if item["ticker"] not in self._alerted:
                    self._alerted.add(item["ticker"])
                    alerts.append(f"{item['name']} {item['reg_change']}")
                    row.flash(item["reg_up"])
            else:
                self._alerted.discard(item["ticker"])
        self.alert_label.setText("  ·  ".join(alerts[:2]))

    def _row_at(self, widget_pos):
        child = self.childAt(widget_pos)
        while child is not None and child is not self:
            if isinstance(child, StockRow):
                return child
            child = child.parentWidget()
        return None

    def _pos_in_self(self, event):
        return self.mapFromGlobal(event.globalPos())

    def eventFilter(self, obj, event):
        et = event.type()
        if et in (QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            if not hasattr(event, "globalPos"):
                return super().eventFilter(obj, event)
            local = self._pos_in_self(event)
            if et == QEvent.MouseMove:
                if self._resizing and (event.buttons() & Qt.LeftButton):
                    self._apply_resize(event.globalPos())
                    return True
                if (event.buttons() & Qt.LeftButton) and (self._dragging or self._press_global is not None):
                    # Let normal handlers on self manage drag if started there;
                    # still update cursor when idle over edges through children.
                    pass
                if not (event.buttons() & Qt.LeftButton):
                    edges = self._hit_resize_edges(local)
                    self.setCursor(self._cursor_for_edges(edges))
                    if edges:
                        return False
            elif et == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                edges = self._hit_resize_edges(local)
                if edges:
                    self._resizing = True
                    self._dragging = False
                    self._press_row = None
                    self._resize_edges = edges
                    self._resize_start_geo = self.geometry()
                    self._resize_start_global = event.globalPos()
                    self._press_global = event.globalPos()
                    return True
            elif et == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                if self._resizing:
                    self._resizing = False
                    self._resize_edges = 0
                    self.persist_geometry(force=True)
                    self.setCursor(self._cursor_for_edges(self._hit_resize_edges(local)))
                    return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edges = self._hit_resize_edges(event.pos())
            self._dragging = False
            self._resizing = False
            self._press_global = event.globalPos()
            self._press_offset = event.globalPos() - self.frameGeometry().topLeft()
            self._press_row = None
            if edges:
                self._resizing = True
                self._resize_edges = edges
                self._resize_start_geo = self.geometry()
                self._resize_start_global = event.globalPos()
            else:
                self._press_row = self._row_at(event.pos())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and (event.buttons() & Qt.LeftButton):
            self._apply_resize(event.globalPos())
            event.accept()
            return
        if event.buttons() & Qt.LeftButton:
            moved = (event.globalPos() - self._press_global).manhattanLength()
            if moved >= 6:
                self._dragging = True
                self._press_row = None
                if not self.ui.get("position_locked", False):
                    self.move(event.globalPos() - self._press_offset)
            event.accept()
            return
        edges = self._hit_resize_edges(event.pos())
        self.setCursor(self._cursor_for_edges(edges))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._resizing:
                self._resizing = False
                self._resize_edges = 0
                self.persist_geometry(force=True)
            elif self._dragging:
                if not self.ui.get("position_locked", False):
                    self.persist_geometry(force=True)
            elif self._press_row:
                webbrowser.open(f"https://finance.yahoo.com/quote/{self._press_row.ticker}")
            self._dragging = False
            self._press_row = None
            self.setCursor(self._cursor_for_edges(self._hit_resize_edges(event.pos())))
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        step = 0.04 if event.angleDelta().y() > 0 else -0.04
        opacity = min(1.0, max(0.40, self.windowOpacity() + step))
        self.setWindowOpacity(opacity)
        self.ui["opacity"] = round(opacity, 2)
        save_ui(self.ui)
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._ready_to_save:
            self.persist_geometry()

    def closeEvent(self, event):
        self.persist_geometry(force=True)
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except Exception:
                pass
        event.accept()


if __name__ == "__main__":
    try:
        os.chdir(APP_DIR)
        if sys.platform == "win32":
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("stock.desktop.widget")
            except Exception:
                pass
        kill_previous_instances()
        app = QApplication(sys.argv)
        app.setApplicationName("美股挂件")
        app.setFont(QFont("Microsoft YaHei UI", 11))
        widget = MainWidget()
        widget.show()
        widget.apply_saved_geometry()
        QTimer.singleShot(120, widget.apply_saved_geometry)
        sys.exit(app.exec_())
    except Exception:
        import traceback
        try:
            with open(os.path.join(APP_DIR, "widget_error.log"), "w", encoding="utf-8") as err:
                traceback.print_exc(file=err)
        except Exception:
            pass
        raise
