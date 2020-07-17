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

# Install Visual Studio Community 2017 (15.6)
Write-Host '>>> Installing Visual Studio 2017 Community (15.6)...'
$LocalTempDir = $env:TEMP
$VSInstaller = 'VSInstaller.exe'
$webclient.DownloadFile('https://aka.ms/eac464', "$LocalTempDir\$VSInstaller")
Start-Process -FilePath "$LocalTempDir\$VSInstaller" -Wait -PassThru -ArgumentList `
    "--add Microsoft.VisualStudio.Workload.ManagedDesktop",
    "--add Microsoft.VisualStudio.Workload.NetCoreTools",
    "--add Microsoft.VisualStudio.Workload.NetWeb",
    "--add Microsoft.VisualStudio.Workload.Node",
    "--add Microsoft.VisualStudio.Workload.Office",
    "--add Microsoft.VisualStudio.Component.TypeScript.2.0",
    "--add Microsoft.VisualStudio.Component.TestTools.WebLoadTest",
    "--add Component.GitHub.VisualStudio",
    "--add Microsoft.VisualStudio.ComponentGroup.NativeDesktop.Core",
    "--add Microsoft.VisualStudio.Component.Static.Analysis.Tools",
    "--add Microsoft.VisualStudio.Component.VC.CMake.Project",
    "--add Microsoft.VisualStudio.Component.VC.140",
    "--add Microsoft.VisualStudio.Component.Windows10SDK.15063.Desktop",
    "--add Microsoft.VisualStudio.Component.Windows10SDK.15063.UWP",
    "--add Microsoft.VisualStudio.Component.Windows10SDK.15063.UWP.Native",
    "--add Microsoft.VisualStudio.ComponentGroup.Windows10SDK.15063",
    "--wait",
    "--passive",
    "--norestart" 

# Install CUDA 10.0
Write-Host '>>> Installing CUDA 10.0...'
$CUDAInstaller = 'CUDAInstaller.exe'
$webclient.DownloadFile(
    'https://developer.nvidia.com/compute/cuda/10.0/Prod/network_installers/cuda_10.0.130_windows_network',
    "$LocalTempDir\$CUDAInstaller")
Start-Process -FilePath "$LocalTempDir\$CUDAInstaller" -Wait -PassThru -ArgumentList `
    "-s",
    "nvcc_10.0",
    "cuobjdump_10.0",
    'nvprune_10.0',
    'cupti_10.0',
    'gpu_library_advisor_10.0',
    'memcheck_10.0',
    'nvdisasm_10.0',
    'nvprof_10.0',
    'visual_profiler_10.0',
    'visual_studio_integration_10.0',
    'demo_suite_10.0',
    'documentation_10.0',
    'cublas_10.0',
    'cublas_dev_10.0',
    'cudart_10.0',
    'cufft_10.0',
    'cufft_dev_10.0',
    'curand_10.0',
    'curand_dev_10.0',
    'cusolver_10.0',
    'cusolver_dev_10.0',
    'cusparse_10.0',
    'cusparse_dev_10.0',
    'nvgraph_10.0',
    'nvgraph_dev_10.0',
    'npp_10.0',
    'npp_dev_10.0',
    'nvrtc_10.0',
    'nvrtc_dev_10.0',
    'nvml_dev_10.0'

# Install Python packages
Write-Host '>>> Installing Python packages...'
conda activate
conda install -y numpy scipy matplotlib scikit-learn pandas pytest python-graphviz boto3