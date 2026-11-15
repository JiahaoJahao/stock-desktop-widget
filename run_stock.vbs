Set ws = CreateObject("Wscript.Shell")
ws.CurrentDirectory = "F:\stock"
ws.Run "pythonw ""F:\stock\stock_widget.py""", 0, False
