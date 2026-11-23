$rawPath = 'C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\data\raw\13_hotel_bookings.csv'
$outPath = 'C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\data\processed\hotel_bookings_cleaned.csv'

$data = Import-Csv $rawPath

# Deduplicate
$uniqueMap = @{}
$deduped = @()
foreach ($row in $data) {
    if (-not $uniqueMap.ContainsKey($row.Booking_ID)) {
        $uniqueMap[$row.Booking_ID] = $true
        $deduped += $row
    }
}

# Group medians
$roomTypes = $deduped | Select-Object -ExpandProperty Room_Type -Unique
$rateMedians = @{}
$leadMedians = @{}
foreach ($rt in $roomTypes) {
    $rates = $deduped | Where-Object { $_.Room_Type -eq $rt -and -not [string]::IsNullOrWhiteSpace($_.Room_Rate) } | ForEach-Object { [double]$_.Room_Rate } | Sort-Object
    $leads = $deduped | Where-Object { $_.Room_Type -eq $rt -and -not [string]::IsNullOrWhiteSpace($_.Lead_Time_Days) } | ForEach-Object { [double]$_.Lead_Time_Days } | Sort-Object
    $rateMedians[$rt] = $rates[[math]::Floor($rates.Count / 2)]
    $leadMedians[$rt] = $leads[[math]::Floor($leads.Count / 2)]
}

# Clean and transform
$cleanedList = @()
foreach ($r in $deduped) {
    $nights = [int]$r.Nights
    $isCanc = if ($r.Canceled -eq 'Yes') { 1 } else { 0 }
    $rate = if ([string]::IsNullOrWhiteSpace($r.Room_Rate)) { $rateMedians[$r.Room_Type] } else { [double]$r.Room_Rate }
    $lead = if ([string]::IsNullOrWhiteSpace($r.Lead_Time_Days)) { $leadMedians[$r.Room_Type] } else { [double]$r.Lead_Time_Days }
    $chan = if ([string]::IsNullOrWhiteSpace($r.Booking_Channel)) { "Unknown" } else { $r.Booking_Channel }
    $dt = [datetime]::Parse($r.Checkin_Date)
    $rev = if ($isCanc -eq 0) { $nights * $rate } else { 0.0 }
    $potRev = $nights * $rate
    $band = if ($lead -le 7) { "Last-Minute (0-7d)" } elseif ($lead -le 30) { "Short-Term (8-30d)" } else { "Advance (31+d)" }
    $isWeekend = if ($dt.DayOfWeek -in @([DayOfWeek]::Friday, [DayOfWeek]::Saturday, [DayOfWeek]::Sunday)) { 1 } else { 0 }

    $obj = [PSCustomObject]@{
        Booking_ID        = $r.Booking_ID
        Checkin_Date      = $dt.ToString("yyyy-MM-dd")
        Nights            = $nights
        Room_Type         = $r.Room_Type
        Booking_Channel   = $chan
        Traveler_Type     = $r.Traveler_Type
        Lead_Time_Days    = $lead
        Room_Rate         = $rate
        Canceled          = $r.Canceled
        Arrival_Year_Month= $dt.ToString("yyyy-MM")
        Arrival_Month_Name= $dt.ToString("MMMM")
        Arrival_Weekday   = $dt.ToString("dddd")
        Is_Weekend_Arrival= $isWeekend
        Lead_Time_Band    = $band
        Potential_Revenue = $potRev
        Revenue           = $rev
    }
    $cleanedList += $obj
}

$cleanedList | Export-Csv -Path $outPath -NoTypeInformation
Write-Host "Processed data written successfully to $outPath. Rows: $($cleanedList.Count)"
