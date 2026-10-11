# Week 1 - API Gateway -> Producer Lambda smoke test
# Run in Windows PowerShell.

$body = @{
    customerId = "CUS001"
    productId  = "P001"
    quantity   = 2
} | ConvertTo-Json

# Replace this with the current Invoke URL if the Learner Lab is rebuilt.
$uri = "https://a3tbe1kpq0.execute-api.us-east-1.amazonaws.com/orders"

$response = Invoke-WebRequest `
  -Uri $uri `
  -Method POST `
  -ContentType "application/json" `
  -Body $body

Write-Host "HTTP Status:" $response.StatusCode
Write-Host "Response:"
$response.Content
