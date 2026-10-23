# Week 3 - Safe API Gateway -> Producer Lambda smoke test wrapper
# Delegates to the canonical bounded Python tool (scripts/load_test_orders.py) so all
# URL validation, finite timeouts, rate bounds, and dry-run/execute safeguards are shared
# in one place (ONE RULE -> ONE OWNER).

param(
    [string]$EndpointUrl = $env:ORDER_API_URL,
    [string]$CustomerPrefix = "CUS001",
    [string]$ProductId = "P001",
    [int]$Count = 1,
    [double]$Rate = 1.0,
    [double]$TimeoutSec = 5.0,
    [switch]$DryRun,
    [switch]$Execute
)

if ($DryRun -and $Execute) {
    Write-Error "Conflicting switches: -DryRun and -Execute cannot be used together."
    exit 2
}

if ([string]::IsNullOrWhiteSpace($EndpointUrl)) {
    Write-Error "EndpointUrl is required. Pass -EndpointUrl https://<api-id>.execute-api.us-east-1.amazonaws.com/orders or set ORDER_API_URL."
    exit 2
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$loadScript = Join-Path $scriptDir "load_test_orders.py"

$cliArgs = @(
    $loadScript,
    "--endpoint", $EndpointUrl.Trim(),
    "--count", "$Count",
    "--rate", "$Rate",
    "--timeout", "$TimeoutSec",
    "--customer-prefix", $CustomerPrefix,
    "--product-id", $ProductId,
    "--no-reconcile"
)

if ($Execute) {
    $parsedUri = $null
    if (-not [System.Uri]::TryCreate($EndpointUrl.Trim(), [System.UriKind]::Absolute, [ref]$parsedUri) -or $parsedUri.Scheme -ne "https") {
        Write-Error "EndpointUrl must be a valid https:// URL."
        exit 2
    }
    $cliArgs += @("--execute", "--confirm-target", $parsedUri.Host)
} else {
    $cliArgs += "--dry-run"
}

& python @cliArgs
exit $LASTEXITCODE
