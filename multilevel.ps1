$csvPath = 'C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\13_hotel_bookings.csv'
$data = Import-Csv $csvPath

# deduplicate
$uniqueMap = @{}
$deduped = @()
foreach ($row in $data) {
    if (-not $uniqueMap.ContainsKey($row.Booking_ID)) {
        $uniqueMap[$row.Booking_ID] = $true
        $deduped += $row
    }
}

# medians for imputation
$roomTypes = $deduped | Select-Object -ExpandProperty Room_Type -Unique
$rateMedians = @{}
$leadMedians = @{}
foreach ($rt in $roomTypes) {
    $rates = $deduped | Where-Object { $_.Room_Type -eq $rt -and -not [string]::IsNullOrWhiteSpace($_.Room_Rate) } | ForEach-Object { [double]$_.Room_Rate } | Sort-Object
    $leads = $deduped | Where-Object { $_.Room_Type -eq $rt -and -not [string]::IsNullOrWhiteSpace($_.Lead_Time_Days) } | ForEach-Object { [double]$_.Lead_Time_Days } | Sort-Object
    $rateMedians[$rt] = $rates[[math]::Floor($rates.Count / 2)]
    $leadMedians[$rt] = $leads[[math]::Floor($leads.Count / 2)]
}

$cleaned = @()
foreach ($r in $deduped) {
    $nights = [int]$r.Nights
    $isCanc = if ($r.Canceled -eq 'Yes') { 1 } else { 0 }
    $rate = if ([string]::IsNullOrWhiteSpace($r.Room_Rate)) { $rateMedians[$r.Room_Type] } else { [double]$r.Room_Rate }
    $chan = if ([string]::IsNullOrWhiteSpace($r.Booking_Channel)) { "Unknown" } else { $r.Booking_Channel }
    $rev = if ($isCanc -eq 0) { $nights * $rate } else { 0.0 }
    $cleaned += [PSCustomObject]@{
        Room_Type       = $r.Room_Type
        Booking_Channel = $chan
        Revenue         = $rev
        Nights          = $nights
        Is_Canceled     = $isCanc
    }
}

Write-Host "--- Groupby Room_Type and Booking_Channel ---"
$multi = $cleaned | Group-Object { "$($_.Room_Type)|$($_.Booking_Channel)" } | ForEach-Object {
    $parts = $_.Name -split '\|'
    $grp = $_.Group
    $nonCanc = $grp | Where-Object { $_.Is_Canceled -eq 0 }
    [PSCustomObject]@{
        Room_Type       = $parts[0]
        Booking_Channel = $parts[1]
        Total_Bookings  = $grp.Count
        Canceled        = ($grp | Where-Object { $_.Is_Canceled -eq 1 }).Count
        Cancel_Pct      = [math]::Round((($grp | Where-Object { $_.Is_Canceled -eq 1 }).Count / $grp.Count) * 100, 1)
        Realized_Nights = ($nonCanc | Measure-Object -Property Nights -Sum).Sum
        Realized_Revenue= [math]::Round(($nonCanc | Measure-Object -Property Revenue -Sum).Sum, 2)
    }
} | Sort-Object -Property Room_Type, Realized_Revenue -Descending
$multi | Format-Table -AutoSize
