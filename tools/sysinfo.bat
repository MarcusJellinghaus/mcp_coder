@echo off
REM Print date/time, CPU load, and system handle count (plus top handle holders).
REM Usage: tools\sysinfo.bat
powershell -NoProfile -Command ^
  "$cpu = (Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average;" ^
  "$procs = Get-Process;" ^
  "$handles = ($procs | Measure-Object HandleCount -Sum).Sum;" ^
  "$threads = ($procs | ForEach-Object { $_.Threads.Count } | Measure-Object -Sum).Sum;" ^
  "Write-Output ('DateTime:  ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff zzz'));" ^
  "Write-Output ('CPU load:  ' + $cpu + ' percent');" ^
  "Write-Output ('Handles:   ' + $handles);" ^
  "Write-Output ('Processes: ' + $procs.Count + '   Threads: ' + $threads);" ^
  "Write-Output 'Top 5 processes by handle count:';" ^
  "$procs | Sort-Object HandleCount -Descending | Select-Object -First 5 Id, ProcessName, HandleCount | Format-Table -AutoSize | Out-String -Width 120 | Write-Output"
