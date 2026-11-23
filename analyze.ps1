$csvPath = 'C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis\13_hotel_bookings.csv'
$data = Import-Csv $csvPath

Write-Host "Total rows:" $data.Count
$cols = $data[0].PSObject.Properties.Name
Write-Host "Columns: $($cols -join ', ')"

Write-Host "`n--- Missing Values ---"
foreach ($col in $cols) {
    $nullCount = ($data | Where-Object { [string]::IsNullOrWhiteSpace($_.$col) }).Count
    Write-Host "$col : $nullCount"
}

Write-Host "`n--- Duplicate Booking_ID ---"
$dupGroups = $data | Group-Object Booking_ID | Where-Object { $_.Count -gt 1 }
Write-Host "Duplicate Booking_ID count: $($dupGroups.Count)"
if ($dupGroups.Count -gt 0) {
    foreach ($d in $dupGroups) {
        Write-Host "Duplicate ID: $($d.Name) appears $($d.Count) times"
    }
}

Write-Host "`n--- Unique Values ---"
Write-Host "Room_Types: $(($data | Select-Object -ExpandProperty Room_Type -Unique) -join ', ')"
Write-Host "Booking_Channels: $(($data | Select-Object -ExpandProperty Booking_Channel -Unique) -join ', ')"
Write-Host "Traveler_Types: $(($data | Select-Object -ExpandProperty Traveler_Type -Unique) -join ', ')"
Write-Host "Canceled values: $(($data | Select-Object -ExpandProperty Canceled -Unique) -join ', ')"
