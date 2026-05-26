$target = "cnpj.db"
Get-Process | ForEach-Object {
    $proc = $_
    try {
        $proc.Modules | Where-Object { $_.FileName -like "*$target*" } | ForEach-Object {
            Write-Host "PID=$($proc.Id) Name=$($proc.Name) File=$($_.FileName)"
        }
    } catch {}
}
