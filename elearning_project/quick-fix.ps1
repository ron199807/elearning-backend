Write-Host "=== Quick Fix ===" -ForegroundColor Cyan

# 1. Fix settings.py
Write-Host "1. Fixing settings.py..." -ForegroundColor Yellow
$settings = Get-Content "elearning_project/settings.py" -Raw

# Fix ALLOWED_HOSTS
$settings = $settings -replace "ALLOWED_HOSTS = os\.getenv\('localhost,127\.0\.0\.1,\.elasticbeanstalk\.com,\.amazonaws\.com,elearning-api-env\.eba-gjr4ta8a\.us-east-1\.elasticbeanstalk\.com'\)\.split\('\,'\)", "ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')"

# Fix CORS
$settings = $settings -replace "CORS_ALLOWED_ORIGINS = os\.getenv\(\`"https://btee-lms\.vercel\.app\`", ''\)\.split\('\,'\)", "CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')"

Set-Content -Path "elearning_project/settings.py" -Value $settings -Encoding utf8

# 2. Set environment
Write-Host "2. Setting environment variables..." -ForegroundColor Yellow
eb setenv ALLOWED_HOSTS="localhost,127.0.0.1,.elasticbeanstalk.com,.amazonaws.com,elearning-api-env.eba-gjr4ta8a.us-east-1.elasticbeanstalk.com"
eb setenv DJANGO_DEBUG="False"

# 3. Deploy
Write-Host "3. Deploying..." -ForegroundColor Green
eb deploy

# 4. Test
Write-Host "4. Testing in 30 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
eb open