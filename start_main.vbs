Dim ws, fso, logFile, logContent, mainDir, mainPath
Set ws = WScript.CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

mainDir = "\dist\main"

mainPath = mainDir & "\main.exe"
logFile = mainDir & "\mainLog.txt"


ws.Run "cmd /c """ & mainPath & " > """ & logFile & """ 2>&1""", 0, True