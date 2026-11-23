$base = 'C:\Users\mohds\.gemini\antigravity\scratch\hotel_booking_analysis'

# Create directories
$dirs = @(
    "$base\data\raw",
    "$base\data\processed",
    "$base\src",
    "$base\notebook",
    "$base\notebooks",
    "$base\outputs",
    "$base\srs"
)

foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Force -Path $d | Out-Null
    }
}

# Copy raw data
Copy-Item "$base\13_hotel_bookings.csv" "$base\data\raw\13_hotel_bookings.csv" -Force
Copy-Item "$base\13_hotel_bookings.csv" "$base\data\13_hotel_bookings.csv" -Force

# Copy notebook to notebook/ and notebooks/
Copy-Item "$base\Project_13_Hotel_Booking_Analysis.ipynb" "$base\notebook\Project_13_Hotel_Booking_Analysis.ipynb" -Force
Copy-Item "$base\Project_13_Hotel_Booking_Analysis.ipynb" "$base\notebooks\Project_13_Hotel_Booking_Analysis.ipynb" -Force

Write-Host "Directory structure created successfully!"
