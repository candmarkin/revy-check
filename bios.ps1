function Set-DellLogo {
    Write-Host "Detectado Dell. Verificando suporte a FullScreenLogo..."
    $Bios = Get-WmiObject -Namespace root\dcim\sysman -Class DCIM_BIOSEnumeration | Where-Object { $_.AttributeName -match "Logo|FullScreenLogo" }
    if ($Bios) {
        Write-Host "Suporte detectado. Aplicando logo..."
        $Bios.CurrentValue = $LogoPath
        $Bios.Put()
        Write-Host "Logo do POST Dell configurada com sucesso!"
    } else {
        Write-Host "Modelo Dell não suporta logo personalizada via WMI."
    }
}

Set-DellLogo