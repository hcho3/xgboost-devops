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

# Reload path
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") +
    ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install OpenSSH and set up public-key auth
Write-Host '>>> Installing OpenSSH for Windows...'
choco install openssh
New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH SSH Server' -Enabled True -Direction Inbound `
    -Protocol TCP -Action Allow -LocalPort 22 -Program "C:\Program Files\OpenSSH-Win64\sshd.exe"
. "C:\Program Files\OpenSSH-Win64\install-sshd.ps1"
mkdir $Env:UserProfile\.ssh
$PublicKey =
    "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDlEj0qPxTBHPxc9EB96jhdUb8z/oylNkItHpn1d87acm4E8E52DbI/" +
    "P24kUm02ZE4pNjF5GAU5wyL2/AU86NjvvQ47xTMJ0rFF+0yZuVbHqMgu/YbUlnMVxikynAyA1XAmGgssDkPUYN6jNbZ1" +
    "ug8Y+CblurWBZ4yQjHaoClOvUzwdw9RuB3A8umdRJyT7jKSq+wV05xo6BX0BDCoAedBBH9wF6FDNRWNUfzGK0FxiDtVp" +
    "55vfxFUPFcGB+lbualdiqgHvo+BBAAssgEExW7pG/2Kurp8xL+cha8ksEeZu79PqGvqz5Qbx4WHuVchdBTF6N7erV1My" +
    "3KMUmG1YzykB"
$AuthorizedKeysFile = "$Env:UserProfile\.ssh\authorized_keys"
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
Set-Service SSHD -StartupType Automatic
Set-Service SSH-Agent -StartupType Automatic
Restart-Service SSHD
Restart-Service SSH-Agent

# CMake 3.18
Write-Host '>>> Installing CMake 3.18...'
choco install cmake --version 3.18.0 --installargs "ADD_CMAKE_TO_PATH=System"

# Notepad++
Write-Host '>>> Installing Notepad++...'
choco install notepadplusplus

# Miniconda
Write-Host '>>> Installing Miniconda...'
choco install miniconda3 /RegisterPython:1 /D=C:\tools\miniconda3
C:\tools\miniconda3\Scripts\conda.exe init
. C:\Users\Administrator\Documents\WindowsPowerShell\profile.ps1
conda config --set auto_activate_base false
conda config --prepend channels conda-forge

# Install Java SE Runtime 8
Write-Host '>>> Installing Java 8...'
choco install jre8 -PackageParameters "/exclude:32"

# Install GraphViz
Write-Host '>>> Installing GraphViz...'
choco install graphviz

# Install Visual Studio Community 2017 (15.9)
Write-Host '>>> Installing Visual Studio 2017 Community (15.9)...'
choco install visualstudio2017community --version 15.9.23.0 --params "--wait --passive --norestart"
choco install visualstudio2017-workload-nativedesktop --params `
    "--wait --passive --norestart --includeOptional"

# Install CUDA 10.1
Write-Host '>>> Installing CUDA 10.1...'
choco install cuda --version 10.1.243

# Install Python packages
Write-Host '>>> Installing Python packages...'
conda activate
conda install -y numpy scipy matplotlib scikit-learn pandas pytest python-graphviz boto3