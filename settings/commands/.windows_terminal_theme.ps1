# 
# Set Color Theme
# 
$file = "https://github.com/microsoft/terminal/releases/download/1708.14008/colortool.zip"
$zip_destination = "$Home/colortool.zip"
$folder_desitnation = "$Home/colortool"
(New-Object Net.WebClient).DownloadFile($file, $zip_destination)
Expand-Archive $zip_destination -DestinationPath $folder_desitnation -Force
# change the theme to OneHalfDark
& "$folder_desitnation/colortool" -b OneHalfDark
