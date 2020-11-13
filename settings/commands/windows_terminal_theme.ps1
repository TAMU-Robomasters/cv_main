# TODO:
    # - check if ruby is already installed, and what version
    # - use scoop reset instead of uninstalling things

# change the powershell theme to use a black background instead of dark magenta
if (-not $host.ui.rawui.backgroundcolor.equals([System.ConsoleColor]::Black)) {
    Clear-Host
$atk_command = @"
powershell -command "Set-ExecutionPolicy RemoteSigned -scope CurrentUser; iex (new-object net.webclient).downloadstring('https://git.io/fj7gT')" & ___AtkPrintDone.bat & exit
"@
    start cmd.exe "/k $atk_command"
    exit
}

# while (-not $host.ui.rawui.backgroundcolor.equals([System.ConsoleColor]::Black)) {
    
#     Clear-Host
#     read-host "
    
#     Hello!
    
#     There's a bit of a problem, but there's an easy fix!
    
#     Powershell has an issue with colors
#     The issue has been posted here for several years
#     https://github.com/microsoft/Terminal/issues/23
#     (Please go complain so they will finally fix it)
#     As far as I know, there's still no way to fix it from a program
    
#     If you could
#     1. Go to the top bar of this powershell
#     2. Right click and then select 'Properties'
#     3. Go to the 'colors' tab
#     4. Select 'Screen Background'
#     5. Select the black color (far left)
#     6. Then click 'OK'
    
#     That will prevent the screen from turning purple later on
#     [press enter to continue]"
    
#     if (-not $host.ui.rawui.backgroundcolor.equals([System.ConsoleColor]::Black)) {
#         Clear-Host
#         read-host "it appears the setting as still not changed
#         [press enter to continue]"
#     }
# }
# Clear-Host

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
