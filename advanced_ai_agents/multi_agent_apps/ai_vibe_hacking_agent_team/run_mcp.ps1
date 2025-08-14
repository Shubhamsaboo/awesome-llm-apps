$files = Get-ChildItem -Path "src\tools\mcp" -Filter "*.py"
foreach ($file in $files) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "python $($file.FullName)" 
}
