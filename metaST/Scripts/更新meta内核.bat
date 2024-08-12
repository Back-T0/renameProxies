@echo off
rem ��ȡ���°汾��
for /f "tokens=*" %%a in ('curl -L -s -o nul -w %%{url_effective} https://github.com/MetaCubeX/mihomo/releases/latest') do (
  echo %%a
  for %%i in ("%%a") do (set "latest=%%~nxi")
)

if "%latest%" neq "latest" (
  echo ���°汾�ţ�%latest%
  
  echo ����win_amd64.zip
  curl -L -s -o win_amd64.zip  https://github.com/MetaCubeX/mihomo/releases/download/%latest%/mihomo-windows-amd64-%latest%.zip
  echo ����win_arm64.zip
  curl -L -s -o win_arm64.zip  https://github.com/MetaCubeX/mihomo/releases/download/%latest%/mihomo-windows-arm64-%latest%.zip
  echo ����linux_amd64.gz
  curl -L -s -o linux_amd64.gz https://github.com/MetaCubeX/mihomo/releases/download/%latest%/mihomo-linux-amd64-%latest%.gz
  echo ����linux_arm64.gz
  curl -L -s -o linux_arm64.gz https://github.com/MetaCubeX/mihomo/releases/download/%latest%/mihomo-linux-arm64-%latest%.gz
  
  echo ��ѹ�ļ�
  7za -o.\ x win_amd64.zip
  7za -o.\ x win_arm64.zip
  7za -o.\ x linux_amd64.gz
  7za -o.\ x linux_arm64.gz

  echo �ƶ��ļ�...
  move /Y mihomo-windows-amd64.exe ..\Resources\meta\win_amd64\mihomo.exe >nul
  move /Y mihomo-windows-arm64.exe ..\Resources\meta\win_arm64\mihomo.exe >nul
  move /Y mihomo-linux-amd64       ..\Resources\meta\linux_amd64\mihomo   >nul
  move /Y mihomo-linux-arm64       ..\Resources\meta\linux_arm64\mihomo   >nul
  
  echo ɾ����ʱ�ļ�...
  del win_amd64.zip  >nul
  del win_arm64.zip  >nul
  del linux_amd64.gz >nul
  del linux_arm64.gz >nul
) else (
  echo ��ȡ���汾��ʧ��
)
pause
