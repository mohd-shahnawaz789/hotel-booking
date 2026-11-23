$csvPath = 'C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\13_hotel_bookings.csv'
$data = Import-Csv $csvPath

# Check if duplicate rows are identical
$exactDups = $data | Group-Object { $_.PSObject.Properties.Value -join '|' } | Where-Object { $_.Count -gt 1 }
Write-Host "Exact full-row duplicates count: $($exactDups.Count)"

# Let's inspect the 25 duplicate Booking_IDs
$dupIds = ($data | Group-Object Booking_ID | Where-Object { $_.Count -gt 1 }).Name
Write-Host "Are all 25 duplicates identical across all columns?"
$allIdentical = $true
foreach ($id in $dupIds) {
    $rows = $data | Where-Object { $_.Booking_ID -eq $id }
    $first = $rows[0].PSObject.Properties.Value -join '|'
    $second = $rows[1].PSObject.Properties.Value -join '|'
    if ($first -ne $second) {
        $allIdentical = $false
        Write-Host "Mismatch in ID $id : $first vs $second"
    }
}
Write-Host "All duplicate rows completely identical: $allIdentical"
