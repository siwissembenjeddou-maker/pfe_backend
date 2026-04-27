# AutiSense API Authentication Test Script
# This script demonstrates the correct way to authenticate and make API requests

# Step 1: Create login data with ALL required fields
$loginData = @{
    email    = "demo.admin@autisense.app"
    password = "demo1234"
    role     = "admin"
} | ConvertTo-Json

Write-Host "Step 1: Logging in..." -ForegroundColor Green
Write-Host "Login data: $loginData"

# Step 2: Send login request
try {
    $tokenResponse = Invoke-RestMethod `
        -Uri "http://127.0.0.1:8000/auth/login" `
        -Method Post `
        -Body $loginData `
        -ContentType "application/json" `
        -ErrorAction Stop
    
    Write-Host "Login successful!" -ForegroundColor Green
    Write-Host "Response: $($tokenResponse | ConvertTo-Json -Depth 5)"
    
    # Step 3: Extract the token from the nested response
    $accessToken = $tokenResponse.user.token
    
    if (-not $accessToken) {
        Write-Host "ERROR: No token received in response!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Access token obtained: $($accessToken.Substring(0, [Math]::Min(50, $accessToken.Length)))..."
    
} catch {
    Write-Host "Login failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

# Step 4: Create headers with proper formatting
$headers = @{
    "Authorization" = "Bearer $accessToken"
    "Content-Type" = "application/json"
}

Write-Host "`nStep 2: Testing authenticated endpoint..." -ForegroundColor Green

# Step 5: Make authenticated request
try {
    $result = Invoke-RestMethod `
        -Uri "http://127.0.0.1:8000/children/" `
        -Method Get `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Host "Success! Children endpoint accessed." -ForegroundColor Green
    Write-Host "Result: $($result | ConvertTo-Json -Depth 5)"
    
} catch {
    Write-Host "API request failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host "`nAll tests passed!" -ForegroundColor Green