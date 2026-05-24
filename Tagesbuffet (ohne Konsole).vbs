' Startet den Tagesbuffet-Generator ohne sichtbares Konsolen-Fenster.
' Bei einem Crash schreibt die GUI selbst eine Datei "tagesbuffet_crash.log"
' und zeigt eine Fehler-Messagebox.

Set objShell = CreateObject("WScript.Shell")
Set objFSO   = CreateObject("Scripting.FileSystemObject")

' In das Verzeichnis dieses Skripts wechseln
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = strPath

' pythonw.exe = Python ohne Konsolen-Fenster
' 0 = unsichtbar starten, False = nicht warten
objShell.Run "pythonw.exe """ & strPath & "\tagesbuffet_gui.py""", 0, False
