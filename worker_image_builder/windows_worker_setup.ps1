$ErrorActionPreference = "Stop"

# Set *temporary* password for the Administrator user
$SecurePassword = ConvertTo-SecureString "WPUavEUmPhZpR4288GCQ7MeA" -AsPlainText -Force
Set-LocalUser -Name "Administrator" -AccountNeverExpires -Password $SecurePassword

# Configure EC2 launch setting. Ensure that password gets reset to random in next boot
$EC2LaunchSetting = "{`"adminPasswordType`": `"Random`"}"
$EC2LaunchConfigFile = "C:\ProgramData\Amazon\EC2-Windows\Launch\Config\LaunchConfig.json"
Set-Content -Path $EC2LaunchConfigFile -Value $EC2LaunchSetting
C:\ProgramData\Amazon\EC2-Windows\Launch\Scripts\InitializeInstance.ps1 -SchedulePerBoot

# Install Chocolatey
Write-Host '>>> Installing Chocolatey...'
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol =
    [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$webclient = New-Object System.Net.WebClient
Invoke-Expression ($webclient.DownloadString('https://chocolatey.org/install.ps1'))
choco --version
choco feature enable -n=allowGlobalConfirmation

# Git 2.27
Write-Host '>>> Installing Git 2.27...'
choco install git.install -params "'/GitAndUnixToolsOnPath'"
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }

# Reload path
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") +
    ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install OpenSSH and set up public-key auth
Write-Host '>>> Installing OpenSSH for Windows...'
choco install openssh
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH SSH Server' -Enabled True -Direction Inbound `
    -Protocol TCP -Action Allow -LocalPort 22 -Program "C:\Program Files\OpenSSH-Win64\sshd.exe"
. "C:\Program Files\OpenSSH-Win64\install-sshd.ps1"
mkdir C:\Users\Administrator\.ssh
$PublicKey =
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDlEj0qPxTBHPxc9EB96jhdUb8z/oylNkItHpn1d87acm4E8E52DbI/" +
    "P24kUm02ZE4pNjF5GAU5wyL2/AU86NjvvQ47xTMJ0rFF+0yZuVbHqMgu/YbUlnMVxikynAyA1XAmGgssDkPUYN6jNbZ1" +
    "ug8Y+CblurWBZ4yQjHaoClOvUzwdw9RuB3A8umdRJyT7jKSq+wV05xo6BX0BDCoAedBBH9wF6FDNRWNUfzGK0FxiDtVp" +
    "55vfxFUPFcGB+lbualdiqgHvo+BBAAssgEExW7pG/2Kurp8xL+cha8ksEeZu79PqGvqz5Qbx4WHuVchdBTF6N7erV1My" +
    "3KMUmG1YzykB"
$AuthorizedKeysFile = "C:\Users\Administrator\.ssh\authorized_keys"
Set-Content -Path $AuthorizedKeysFile -Value $PublicKey
Import-Module "$env:PROGRAMFILES\OpenSSH-Win64\OpenSSHUtils.psd1" -Force
Repair-AuthorizedKeyPermission -FilePath $AuthorizedKeysFile
Set-Service SSHD -StartupType Automatic
Set-Service SSH-Agent -StartupType Automatic
Restart-Service SSHD
Restart-Service SSH-Agent
sed -i -e 's/^Match Group administrators$//g' `
       -e 's/AuthorizedKeysFile __PROGRAMDATA__\/ssh\/administrators_authorized_keys$//g' `
          C:\ProgramData\ssh\sshd_config
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }
Set-Service SSHD -StartupType Automatic
Set-Service SSH-Agent -StartupType Automatic
Restart-Service SSHD
Restart-Service SSH-Agent

# CMake 3.18
Write-Host '>>> Installing CMake 3.18...'
choco install cmake --version 3.18.0 --installargs "ADD_CMAKE_TO_PATH=System"
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }

# Notepad++
Write-Host '>>> Installing Notepad++...'
choco install notepadplusplus
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }

# Miniconda
Write-Host '>>> Installing Miniconda...'
choco install miniconda3 /RegisterPython:1 /D:C:\tools\miniconda3
C:\tools\miniconda3\Scripts\conda.exe init --user --system
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }
. "C:\Program Files\PowerShell\7\profile.ps1"
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }
conda config --set auto_activate_base false
conda config --prepend channels conda-forge

# Install Java 11
Write-Host '>>> Installing Java 11...'
choco install openjdk11jre
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }

# Install GraphViz
Write-Host '>>> Installing GraphViz...'
choco install graphviz
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }

# Install Visual Studio Community 2017 (15.9)
Write-Host '>>> Installing Visual Studio 2017 Community (15.9)...'
choco install visualstudio2017community --version 15.9.23.0 --params "--wait --passive --norestart"
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }
choco install visualstudio2017-workload-nativedesktop --params `
    "--wait --passive --norestart --includeOptional"
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }

# Install CUDA 11.0
Write-Host '>>> Installing CUDA 11.0...'
choco install cuda --version 11.0.3
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }

# Install Python packages
Write-Host '>>> Installing Python packages...'
conda activate
conda install -y numpy scipy matplotlib scikit-learn pandas pytest python-graphviz boto3 awscli `
    hypothesis jsonschema mamba
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }

# Install R
Write-Host '>>> Installing R...'
choco install r.project --version=3.6.3
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }
choco install rtools --version=3.5.0.4
if ($LASTEXITCODE -ne 0) { throw "Last command failed" }
