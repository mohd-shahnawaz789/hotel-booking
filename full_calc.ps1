$csvPath = 'C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\13_hotel_bookings.csv'
$data = Import-Csv $csvPath

# 2. De-duplicate by Booking_ID
$uniqueMap = @{}
$deduped = @()
foreach ($row in $data) {
    if (-not $uniqueMap.ContainsKey($row.Booking_ID)) {
        $uniqueMap[$row.Booking_ID] = $true
        $deduped += $row
    }
}
Write-Host "Deduped count: $($deduped.Count)"

# Check missing values in deduped
Write-Host "`n--- Missing in Deduped ---"
foreach ($col in $deduped[0].PSObject.Properties.Name) {
    $nullCount = ($deduped | Where-Object { [string]::IsNullOrWhiteSpace($_.$col) }).Count
    Write-Host "$col : $nullCount"
}

# 3. Medians by Room_Type for Room_Rate and Lead_Time_Days
function Get-Median($values) {
    $sorted = $values | Sort-Object
    $count = $sorted.Count
    if ($count -eq 0) { return 0 }
    if ($count % 2 -eq 1) {
        return $sorted[[math]::Floor($count / 2)]
    } else {
        return ($sorted[$count / 2 - 1] + $sorted[$count / 2]) / 2.0
    }
}

$roomTypes = $deduped | Select-Object -ExpandProperty Room_Type -Unique
Write-Host "`n--- Medians by Room_Type ---"
$rateMedians = @{}
$leadMedians = @{}
foreach ($rt in $roomTypes) {
    $rates = $deduped | Where-Object { $_.Room_Type -eq $rt -and -not [string]::IsNullOrWhiteSpace($_.Room_Rate) } | ForEach-Object { [double]$_.Room_Rate }
    $leads = $deduped | Where-Object { $_.Room_Type -eq $rt -and -not [string]::IsNullOrWhiteSpace($_.Lead_Time_Days) } | ForEach-Object { [double]$_.Lead_Time_Days }
    $medRate = Get-Median $rates
    $medLead = Get-Median $leads
    $rateMedians[$rt] = $medRate
    $leadMedians[$rt] = $medLead
    Write-Host "$rt -> Median Room_Rate: $medRate | Median Lead_Time: $medLead"
}

# Clean and enrich
$cleaned = [System.Collections.Generic.List[PSCustomObject]]::new()
foreach ($r in $deduped) {
    $nights = [int]$r.Nights
    $isCanc = if ($r.Canceled -eq 'Yes') { 1 } else { 0 }
    $rate = if ([string]::IsNullOrWhiteSpace($r.Room_Rate)) { $rateMedians[$r.Room_Type] } else { [double]$r.Room_Rate }
    $lead = if ([string]::IsNullOrWhiteSpace($r.Lead_Time_Days)) { $leadMedians[$r.Room_Type] } else { [double]$r.Lead_Time_Days }
    $chan = if ([string]::IsNullOrWhiteSpace($r.Booking_Channel)) { "Unknown" } else { $r.Booking_Channel }
    $dt = [datetime]::Parse($r.Checkin_Date)
    $rev = if ($isCanc -eq 0) { $nights * $rate } else { 0.0 }
    
    $band = if ($lead -le 7) { "Last-Minute (0-7d)" } elseif ($lead -le 30) { "Short-Term (8-30d)" } else { "Advance (31+d)" }

    $obj = [PSCustomObject]@{
        Booking_ID        = $r.Booking_ID
        Checkin_Date      = $dt
        Nights            = $nights
        Room_Type         = $r.Room_Type
        Booking_Channel   = $chan
        Traveler_Type     = $r.Traveler_Type
        Lead_Time_Days    = $lead
        Room_Rate         = $rate
        Canceled          = $r.Canceled
        Is_Canceled       = $isCanc
        Revenue           = $rev
        Lead_Band         = $band
        Arrival_Month     = $dt.ToString("yyyy-MM")
        Arrival_Month_Name= $dt.ToString("MMMM")
        Arrival_Weekday   = $dt.ToString("dddd")
    }
    $cleaned.Add($obj)
}

# 5. Overall metrics
$totalBookings = $cleaned.Count
$totalNights = ($cleaned | Measure-Object -Property Nights -Sum).Sum
$totalCanceled = ($cleaned | Where-Object { $_.Is_Canceled -eq 1 }).Count
$cancelPct = ($totalCanceled / $totalBookings) * 100

Write-Host "`n--- 5. Overall Metrics ---"
Write-Host "Total Bookings: $totalBookings"
Write-Host "Total Room Nights (All): $totalNights"
$realizedNights = ($cleaned | Where-Object { $_.Is_Canceled -eq 0 } | Measure-Object -Property Nights -Sum).Sum
Write-Host "Realized Room Nights (Non-Canceled): $realizedNights"
Write-Host "Canceled Bookings: $totalCanceled"
Write-Host "Cancellation Percentage: $([math]::Round($cancelPct, 2))%"

# 6. Total booking revenue for non-canceled bookings
$totalRevenue = ($cleaned | Measure-Object -Property Revenue -Sum).Sum
Write-Host "`n--- 6. Revenue ---"
Write-Host "Total Realized Revenue: $($totalRevenue.ToString('N2'))"

# 7. Compare average room rates and occupancy across room types
Write-Host "`n--- 7. Room Type Comparison ---"
$rtSummary = $cleaned | Group-Object Room_Type | ForEach-Object {
    $group = $_.Group
    $nonCancel = $group | Where-Object { $_.Is_Canceled -eq 0 }
    [PSCustomObject]@{
        Room_Type        = $_.Name
        Total_Bookings   = $group.Count
        Booking_Share_Pct= [math]::Round(($group.Count / $totalBookings) * 100, 2)
        Avg_Room_Rate    = [math]::Round(($group | Measure-Object -Property Room_Rate -Average).Average, 2)
        Median_Room_Rate = Get-Median ($group | ForEach-Object { $_.Room_Rate })
        Total_Nights     = ($group | Measure-Object -Property Nights -Sum).Sum
        Realized_Nights  = ($nonCancel | Measure-Object -Property Nights -Sum).Sum
        Realized_Revenue = [math]::Round(($nonCancel | Measure-Object -Property Revenue -Sum).Sum, 2)
        Revenue_Share_Pct= [math]::Round((($nonCancel | Measure-Object -Property Revenue -Sum).Sum / $totalRevenue) * 100, 2)
        Cancellation_Pct = [math]::Round((($group | Where-Object { $_.Is_Canceled -eq 1 }).Count / $group.Count) * 100, 2)
    }
}
$rtSummary | Format-Table -AutoSize

# 8. Rank booking channels by booking volume and revenue
Write-Host "`n--- 8. Booking Channels Ranked ---"
$channelSummary = $cleaned | Group-Object Booking_Channel | ForEach-Object {
    $group = $_.Group
    $nonCancel = $group | Where-Object { $_.Is_Canceled -eq 0 }
    [PSCustomObject]@{
        Channel          = $_.Name
        Total_Bookings   = $group.Count
        Booking_Share_Pct= [math]::Round(($group.Count / $totalBookings) * 100, 2)
        Realized_Revenue = [math]::Round(($nonCancel | Measure-Object -Property Revenue -Sum).Sum, 2)
        Revenue_Share_Pct= [math]::Round((($nonCancel | Measure-Object -Property Revenue -Sum).Sum / $totalRevenue) * 100, 2)
        Canceled_Count   = ($group | Where-Object { $_.Is_Canceled -eq 1 }).Count
        Cancellation_Pct = [math]::Round((($group | Where-Object { $_.Is_Canceled -eq 1 }).Count / $group.Count) * 100, 2)
    }
} | Sort-Object -Property Realized_Revenue -Descending
$channelSummary | Format-Table -AutoSize

# 9. Cancellation rates by booking channel and lead-time bands
Write-Host "`n--- 9. Lead-Time Bands & Cancellation ---"
$bandSummary = $cleaned | Group-Object Lead_Band | ForEach-Object {
    $group = $_.Group
    [PSCustomObject]@{
        Lead_Band        = $_.Name
        Bookings         = $group.Count
        Canceled         = ($group | Where-Object { $_.Is_Canceled -eq 1 }).Count
        Cancellation_Pct = [math]::Round((($group | Where-Object { $_.Is_Canceled -eq 1 }).Count / $group.Count) * 100, 2)
    }
} | Sort-Object -Property Bookings -Descending
$bandSummary | Format-Table -AutoSize

Write-Host "`n--- 9b. Channel x Lead Band Cancellation Pivot ---"
$piv = @()
foreach ($ch in ($channelSummary.Channel)) {
    foreach ($lb in @("Last-Minute (0-7d)", "Short-Term (8-30d)", "Advance (31+d)")) {
        $sub = $cleaned | Where-Object { $_.Booking_Channel -eq $ch -and $_.Lead_Band -eq $lb }
        if ($sub.Count -gt 0) {
            $canc = ($sub | Where-Object { $_.Is_Canceled -eq 1 }).Count
            $piv += [PSCustomObject]@{
                Channel = $ch
                Band    = $lb
                Total   = $sub.Count
                Canceled= $canc
                Rate_Pct= [math]::Round(($canc / $sub.Count) * 100, 1)
            }
        }
    }
}
$piv | Format-Table -AutoSize

# 10. Top 3 peak revenue months
Write-Host "`n--- 10. Monthly Realized Revenue ---"
$monthlyRevenue = $cleaned | Where-Object { $_.Is_Canceled -eq 0 } | Group-Object Arrival_Month | ForEach-Object {
    [PSCustomObject]@{
        Month            = $_.Name
        Realized_Revenue = [math]::Round(($_.Group | Measure-Object -Property Revenue -Sum).Sum, 2)
        Realized_Nights  = ($_.Group | Measure-Object -Property Nights -Sum).Sum
        Bookings         = $_.Group.Count
    }
} | Sort-Object -Property Realized_Revenue -Descending
$monthlyRevenue | Format-Table -AutoSize

# 11. Average stay duration for leisure vs business
Write-Host "`n--- 11. Stay Duration by Traveler Type ---"
$travelerSummary = $cleaned | Group-Object Traveler_Type | ForEach-Object {
    $group = $_.Group
    [PSCustomObject]@{
        Traveler_Type    = $_.Name
        Bookings         = $group.Count
        Avg_Stay_Nights  = [math]::Round(($group | Measure-Object -Property Nights -Average).Average, 2)
        Median_Stay      = Get-Median ($group | ForEach-Object { [double]$_.Nights })
        Realized_Revenue = [math]::Round(($group | Where-Object { $_.Is_Canceled -eq 0 } | Measure-Object -Property Revenue -Sum).Sum, 2)
        Cancellation_Pct = [math]::Round((($group | Where-Object { $_.Is_Canceled -eq 1 }).Count / $group.Count) * 100, 2)
    }
}
$travelerSummary | Format-Table -AutoSize

# 12. Room rate statistics (mean, median, std)
Write-Host "`n--- 12. Room Rate Stats ---"
$ratesAll = $cleaned | ForEach-Object { [double]$_.Room_Rate }
$meanRate = ($ratesAll | Measure-Object -Average).Average
$medianRate = Get-Median $ratesAll
$variance = ($ratesAll | ForEach-Object { [math]::Pow($_ - $meanRate, 2) } | Measure-Object -Sum).Sum / ($ratesAll.Count - 1)
$stdRate = [math]::Sqrt($variance)
Write-Host "Mean Room Rate: $([math]::Round($meanRate, 2))"
Write-Host "Median Room Rate: $([math]::Round($medianRate, 2))"
Write-Host "Std Dev Room Rate: $([math]::Round($stdRate, 2))"

# 13. IQR method for unusually high booking values (non-canceled revenue)
Write-Host "`n--- 13. Outlier Analysis (Revenue) ---"
$nonCancelRev = $cleaned | Where-Object { $_.Is_Canceled -eq 0 } | ForEach-Object { [double]$_.Revenue } | Sort-Object
$nRev = $nonCancelRev.Count
$q1Idx = [int][math]::Floor($nRev * 0.25)
$q3Idx = [int][math]::Floor($nRev * 0.75)
$q1 = $nonCancelRev[$q1Idx]
$q3 = $nonCancelRev[$q3Idx]
$iqr = $q3 - $q1
$upperBound = $q3 + 1.5 * $iqr
$lowerBound = [math]::Max(0, ($q1 - 1.5 * $iqr))
$outliers = $cleaned | Where-Object { $_.Is_Canceled -eq 0 -and $_.Revenue -gt $upperBound }
Write-Host "Non-canceled bookings count: $nRev"
Write-Host "Q1: $q1 | Q3: $q3 | IQR: $iqr"
Write-Host "Upper Fence: $upperBound | Lower Fence: $lowerBound"
Write-Host "Outliers Count: $($outliers.Count)"
if ($outliers.Count -gt 0) {
    Write-Host "Top 5 outlier bookings by revenue:"
    $outliers | Sort-Object -Property Revenue -Descending | Select-Object -First 5 -Property Booking_ID, Room_Type, Nights, Room_Rate, Revenue | Format-Table -AutoSize
}

# Day of week breakdown (for staffing recommendations)
Write-Host "`n--- Weekday Arrivals ---"
$cleaned | Group-Object Arrival_Weekday | ForEach-Object {
    [PSCustomObject]@{
        Weekday = $_.Name
        Bookings = $_.Group.Count
        Cancellation_Pct = [math]::Round((($_.Group | Where-Object { $_.Is_Canceled -eq 1 }).Count / $_.Group.Count) * 100, 2)
    }
} | Format-Table -AutoSize
