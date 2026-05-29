param(
    [string]$HomeAssistantUrl = "http://192.168.1.153:8123",
    [string]$Username = $env:HA_USERNAME,
    [securestring]$Password,
    [pscredential]$Credential,
    [int]$DurationMinutes = 30,
    [int]$IntervalSeconds = 60,
    [string]$EntityPattern = "air_purifier",
    [string]$PowerPlugEntity = "switch.electric_blanket",
    [string]$SambaShare = "\\192.168.1.153\config",
    [switch]$SkipLogs
)

$ErrorActionPreference = "Stop"

function ConvertTo-PlainText {
    param([securestring]$Secure)
    if ($null -eq $Secure) {
        return $null
    }
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Get-HomeAssistantToken {
    param(
        [string]$BaseUrl,
        [pscredential]$Credential
    )

    $clientId = "http://localhost/"
    $flowBody = @{
        client_id = $clientId
        handler = @("homeassistant", $null)
        redirect_uri = "http://localhost/"
    } | ConvertTo-Json

    $flow = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/login_flow" -ContentType "application/json" -Body $flowBody

    $plainPassword = ConvertTo-PlainText $Credential.Password
    try {
        $loginBody = @{
            username = $Credential.UserName
            password = $plainPassword
            client_id = $clientId
        } | ConvertTo-Json

        $login = Invoke-RestMethod `
            -Method Post `
            -Uri "$BaseUrl/auth/login_flow/$($flow.flow_id)" `
            -ContentType "application/json" `
            -Body $loginBody
    }
    finally {
        $plainPassword = $null
    }

    Invoke-RestMethod `
        -Method Post `
        -Uri "$BaseUrl/auth/token" `
        -ContentType "application/x-www-form-urlencoded" `
        -Body @{
            grant_type = "authorization_code"
            code = $login.result
            client_id = $clientId
        }
}

function Get-PhilipsLogLines {
    param(
        [string]$Share,
        [pscredential]$Credential
    )

    if ($SkipLogs -or -not $Share) {
        return @()
    }

    $driveName = "HAMonitor"
    if (Get-PSDrive -Name $driveName -ErrorAction SilentlyContinue) {
        Remove-PSDrive -Name $driveName -Force
    }

    New-PSDrive -Name $driveName -PSProvider FileSystem -Root $Share -Credential $Credential -Scope Script | Out-Null

    try {
        $paths = @(
            "$($driveName):\home-assistant.log",
            "$($driveName):\home-assistant.log.fault",
            "$($driveName):\philips_airpurifier_debug.jsonl"
        )
        $lines = @()
        foreach ($path in $paths) {
            if (Test-Path $path) {
                $matches = Get-Content -Tail 1000 $path |
                    Select-String -Pattern "philips|airpurifier|aiocoap|coap|unavailable|reconnect|failed|exception|traceback|observe|watchdog|status|setup" -CaseSensitive:$false |
                    ForEach-Object { $_.Line }
                $lines += $matches
            }
        }
        return $lines
    }
    finally {
        Remove-PSDrive -Name $driveName -Force -ErrorAction SilentlyContinue
    }
}

if ($null -eq $Credential) {
    if (-not $Username) {
        throw "Provide -Username, -Credential, or set HA_USERNAME."
    }
    if ($null -eq $Password) {
        if ($env:HA_PASSWORD) {
            $Password = ConvertTo-SecureString $env:HA_PASSWORD -AsPlainText -Force
        }
        else {
            $Password = Read-Host "Home Assistant password" -AsSecureString
        }
    }
    $Credential = [pscredential]::new($Username, $Password)
}

$baseUrl = $HomeAssistantUrl.TrimEnd("/")
$token = Get-HomeAssistantToken -BaseUrl $baseUrl -Credential $Credential
$headers = @{ Authorization = "Bearer $($token.access_token)" }
$endAt = (Get-Date).AddMinutes($DurationMinutes)
$samples = @()
$unavailableSamples = 0

while ((Get-Date) -lt $endAt) {
    $states = Invoke-RestMethod -Method Get -Uri "$baseUrl/api/states" -Headers $headers
    $entities = @(
        $states | Where-Object {
            $_.entity_id -match $EntityPattern -and $_.entity_id -notmatch "^update\."
        }
    )
    $unavailable = @($entities | Where-Object { $_.state -eq "unavailable" })
    $unknown = @($entities | Where-Object { $_.state -eq "unknown" })
    $pm25 = $states | Where-Object { $_.entity_id -eq "sensor.air_purifier_pm2_5" } | Select-Object -First 1
    $rssi = $states | Where-Object { $_.entity_id -eq "sensor.air_purifier_rssi" } | Select-Object -First 1
    $powerPlug = $states | Where-Object { $_.entity_id -eq $PowerPlugEntity } | Select-Object -First 1

    if ($unavailable.Count -gt 0) {
        $unavailableSamples++
    }

    $sample = [pscustomobject]@{
        timestamp = (Get-Date).ToString("s")
        entity_count = $entities.Count
        unavailable = $unavailable.Count
        unknown = $unknown.Count
        fan = ($states | Where-Object { $_.entity_id -eq "fan.air_purifier" } | Select-Object -First 1).state
        pm25 = $pm25.state
        rssi = $rssi.state
        power_plug = $powerPlug.state
    }
    $samples += $sample
    $sample | ConvertTo-Json -Compress

    Start-Sleep -Seconds $IntervalSeconds
}

$logLines = Get-PhilipsLogLines -Share $SambaShare -Credential $Credential
$errorLogLines = @(
    $logLines | Select-String -Pattern "failed|exception|traceback|unavailable|error|watchdog|reconnect" -CaseSensitive:$false |
        ForEach-Object { $_.Line }
)

[pscustomobject]@{
    result = if ($unavailableSamples -eq 0 -and $errorLogLines.Count -eq 0) { "pass" } else { "review" }
    samples = $samples.Count
    unavailable_samples = $unavailableSamples
    matching_log_lines = $logLines.Count
    error_log_lines = $errorLogLines.Count
    final_sample = $samples[-1]
} | ConvertTo-Json -Depth 5

if ($unavailableSamples -gt 0 -or $errorLogLines.Count -gt 0) {
    exit 1
}
