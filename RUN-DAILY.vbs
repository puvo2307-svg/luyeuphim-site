Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\DAILYMONTION"
' Chạy Python với windowstyle ẩn (0 = hidden)
WshShell.Run "cmd /c python main.py", 0, False
Set WshShell = Nothing

