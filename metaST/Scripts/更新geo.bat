@echo off

echo ����geoip.dat
curl -L -s -o geoip.dat  https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.dat
echo ����geosite.dat
curl -L -s -o geosite.dat  https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat
echo ����country.mmdb
curl -L -s -o country.mmdb https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country.mmdb

echo �ƶ��ļ�...
move /Y geoip.dat    ..\Resources\meta\geoip.dat >nul
move /Y geosite.dat  ..\Resources\meta\geosite.dat >nul
move /Y country.mmdb ..\Resources\meta\country.mmdb >nul

pause
