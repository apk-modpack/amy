' Lanzador silencioso de la Sala de Chat (sin ventana de consola)
' Usar este archivo .vbs como alternativa al .bat para un arranque completamente limpio.
Set oShell = CreateObject("WScript.Shell")
oShell.CurrentDirectory = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\") - 1)
oShell.Run "venv\Scripts\pythonw.exe -m wiki_agent.cli chat-room", 0, False

