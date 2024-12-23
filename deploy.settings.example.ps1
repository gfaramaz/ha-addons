# deploy.settings.example.ps1
# ---------------------------------------------------------------------------
# EXAMPLE settings file. Copy or rename to 'deploy.settings.ps1' and adjust.
# Then add 'deploy.settings.ps1' to .gitignore so it never goes to GitHub.
# ---------------------------------------------------------------------------

# Local path to your add-on code on Windows:
$LocalPath = "C:\source\ha-addons\maestro_gateway"

# Samba share path to the corresponding folder on HassOS:
$SambaSharePath = "\\homeassistant\addons\local\maestro_gateway_test"

# SSH key & host info:
$SSHKey = "$env:USERPROFILE\.ssh\id_rsa"
$SSHHost = "root@homeassistant"

# Add-on slug:
$AddonSlug = "local_maestro_gateway_test"

return
