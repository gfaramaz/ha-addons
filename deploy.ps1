<#
.SYNOPSIS
  Deploy a Home Assistant add-on from your local Windows machine to HassOS over Samba + SSH.

.DESCRIPTION
  1. Loads local settings (deploy.settings.ps1) or uses fallback defaults.
  2. Optionally lints your code.
  3. Copies add-on files to HassOS, excluding config.json.
  4. Rebuilds & restarts the add-on.
  5. Streams logs indefinitely until user presses Ctrl+C.

.PARAMETER ConfigFile
  Path to your settings file. Default: ./deploy.settings.ps1

.EXAMPLE
  .\deploy.ps1

.EXAMPLE
  .\deploy.ps1 -ConfigFile ".\my_other_settings.ps1"
#>

Param(
    [string]$ConfigFile = ".\deploy.settings.ps1"
)

# --- 1) Load Settings ---
if (Test-Path $ConfigFile) {
    Write-Host "Loading settings from $ConfigFile"
    . $ConfigFile
} else {
    Write-Host "No $ConfigFile found. Using fallback defaults..."
    # Provide fallback defaults if needed:
    $LocalPath      = "C:\source\ha-addons\maestro_gateway"
    $SambaSharePath = "\\homeassistant\addons\local\maestro_gateway_test"
    $SSHKey         = "$env:USERPROFILE\.ssh\id_rsa"
    $SSHHost        = "root@homeassistant"
    $AddonSlug      = "local_maestro_gateway_test"
}

Write-Host "`n=== 2) (Optional) Local linting ==="
# Uncomment or adapt to your environment:
# & pylint "$LocalPath\rootfs"
# & flake8 "$LocalPath\rootfs"
# & black "$LocalPath\rootfs" --check

Write-Host "`n=== 3) Copy files to HassOS Samba share (excluding config.json) ==="
# /E  => Copy subdirectories, including empty ones
# /PURGE => Delete files in destination that no longer exist in source
# /XF config.json => Exclude config.json
# /XD __pycache__ => Exclude Python cache directories

robocopy `
    "$LocalPath" `
    "$SambaSharePath" `
    /E /PURGE /XF config.json /XD __pycache__

if ($LASTEXITCODE -gt 8) {
    Write-Error "robocopy encountered a serious error (exit code $LASTEXITCODE). Exiting."
    exit $LASTEXITCODE
}

Write-Host "`n=== 4) SSH to rebuild & restart $AddonSlug ==="
$rebuildCmd = "ha addons rebuild $AddonSlug"
$restartCmd = "ha addons restart $AddonSlug"

Write-Host " -> Rebuild: $rebuildCmd"
ssh -i $SSHKey $SSHHost $rebuildCmd

Write-Host " -> Restart: $restartCmd"
ssh -i $SSHKey $SSHHost $restartCmd

Write-Host "`n=== 5) Stream logs indefinitely. Press Ctrl+C to stop. ==="
ssh -i $SSHKey $SSHHost "ha addons logs $AddonSlug --follow"
# Once you press Ctrl+C, the script stops and the connection closes.

Write-Host "`n=== Deployment completed ==="
