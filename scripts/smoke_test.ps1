<#
.SYNOPSIS
    Exam System smoke test - verifies core API endpoints respond as expected.
    Run from project root while backend is running on http://127.0.0.1:8000
.NOTES
    Usage: powershell -ExecutionPolicy Bypass .\scripts\smoke_test.ps1
#>

$BASE = "http://127.0.0.1:8000"
$PASS = 0; $FAIL = 0
$RND = Get-Random -Minimum 1000 -Maximum 99999
$USER = "smoke_$RND"; $PWD = "smoke123"
$TOKEN = ""; $CID = $null; $QID = $null

function Check($n, $label, $method, $path, $body, $exp, $token) {
    $url = "${BASE}${path}"
    $params = @{Uri=$url;Method=$method;ContentType="application/json";UseBasicParsing=$true;TimeoutSec=10}
    if ($body) { $params.Body = $body }
    if ($token) { $params.Headers = @{Authorization = "Bearer $token"} }
    try {
        $r = Invoke-WebRequest @params
        $code = [int]$r.StatusCode
        $ok = $code -eq $exp
        if ($ok) { Write-Host "  OK  $n $label" -ForegroundColor Green; $script:PASS++ }
        else { Write-Host "  FAIL $n $label (exp=$exp got=$code)" -ForegroundColor Red; $script:FAIL++ }
        return @($ok, $r.Content)
    } catch {
        $code = if ($_.Exception.Response.StatusCode.value__) { $_.Exception.Response.StatusCode.value__ } else { 0 }
        Write-Host "  FAIL $n $label (exp=$exp got=$code)" -ForegroundColor Red
        $script:FAIL++; return @($false, "")
    }
}

Write-Host "=== Exam System Smoke Test ===" -ForegroundColor Cyan
Write-Host "Backend: $BASE`n"

# 1. Health
Write-Host "-- [1] Health --" -ForegroundColor Yellow
Check 1.1 "health" "GET" "/health" $null 200 $null

# 2. Auth
Write-Host "`n-- [2] Auth --" -ForegroundColor Yellow
Check 2.1 "register ok" "POST" "/auth/register" "{`"username`":`"$USER`",`"password`":`"$PWD`",`"invite_code`":`"dev-invite`"}" 201 $null
Check 2.2 "register empty code" "POST" "/auth/register" "{`"username`":`"e$RND`",`"password`":`"1`",`"invite_code`":`"`"}" 400 $null
Check 2.3 "register bad code" "POST" "/auth/register" "{`"username`":`"b$RND`",`"password`":`"1`",`"invite_code`":`"bad`"}" 400 $null

$r = Check 2.4 "login" "POST" "/auth/login" "{`"username`":`"$USER`",`"password`":`"$PWD`"}" 200 $null
try { $TOKEN = ($r[1] | ConvertFrom-Json).access_token } catch {}
if ($TOKEN) { Write-Host "  INFO  Token=$($TOKEN.Substring(0, [Math]::Min(20,$TOKEN.Length)))..." -ForegroundColor DarkYellow }

if ($TOKEN) {
    Check 2.5 "auth/me" "GET" "/auth/me" $null 200 $TOKEN
    Check 2.6 "unauthorized" "GET" "/auth/me" $null 401 $null
}

# 3. Courses
Write-Host "`n-- [3] Courses --" -ForegroundColor Yellow
if ($TOKEN) {
    $r = Check 3.1 "create course" "POST" "/courses/" "{`"name`":`"Smoke Course`",`"subject`":`"test`"}" 201 $TOKEN
    try { $CID = ($r[1] | ConvertFrom-Json).id } catch {}
    if ($CID) { Write-Host "  INFO  Course id=$CID" -ForegroundColor DarkYellow }
    Check 3.2 "list mine" "GET" "/courses/mine" $null 200 $TOKEN
}

# 4. Questions & Practice
Write-Host "`n-- [4] Questions & Practice --" -ForegroundColor Yellow
if ($TOKEN -and $CID) {
    Check 4.1 "batch import" "POST" "/questions/batch" `
        "[{`"type`":`"single_choice`",`"question`":`"Q?`",`"options`":{`"A`":`"1`",`"B`":`"2`"},`"answer`":`"A`",`"course_id`":$CID}]" 200 $TOKEN

    $r = Check 4.2 "random" "GET" "/practice/random?course_id=$CID" $null 200 $TOKEN
    try { $QID = ($r[1] | ConvertFrom-Json).id } catch {}

    if ($QID) { Check 4.3 "submit" "POST" "/practice/submit" "{`"question_id`":$QID,`"user_answer`":`"A`"}" 200 $TOKEN }
    Check 4.4 "submit nonexistent" "POST" "/practice/submit" "{`"question_id`":9999999,`"user_answer`":`"A`"}" 404 $TOKEN
    Check 4.5 "wrongbook" "GET" "/wrongbook/" $null 200 $TOKEN
    Check 4.6 "publish course" "POST" "/courses/$CID/publish" $null 200 $TOKEN
    Check 4.7 "library" "GET" "/library/public" $null 200 $TOKEN
    Check 4.8 "unpublish" "POST" "/courses/$CID/unpublish" $null 200 $TOKEN
}

# 5. Review
Write-Host "`n-- [5] Review --" -ForegroundColor Yellow
if ($TOKEN) {
    Check 5.1 "review/due" "GET" "/practice/review/due" $null 200 $TOKEN
    Check 5.2 "review/today" "GET" "/practice/review/today" $null 200 $TOKEN
    Check 5.3 "weak-types" "GET" "/practice/insights/weak-types" $null 200 $TOKEN
    Check 5.4 "stats" "GET" "/practice/stats" $null 200 $TOKEN
    Check 5.5 "history" "GET" "/practice/history?page=1" $null 200 $TOKEN
}

Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $PASS" -ForegroundColor Green
Write-Host "Failed: $FAIL" -ForegroundColor Red
if ($FAIL -gt 0) { exit 1 }
exit 0
