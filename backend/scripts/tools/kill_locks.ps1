Write-Host "Procurando processos Python/Jupyter..."
$procs = Get-WmiObject Win32_Process | Where-Object { $_.Name -like "*python*" }
if ($procs) {
    foreach ($p in $procs) {
        Write-Host "Encerrando PID=$($p.ProcessId) Name=$($p.Name) CMD=$($p.CommandLine)"
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Processos encerrados."
} else {
    Write-Host "Nenhum processo Python encontrado."
}
