@echo off
set MSG=%*
if "%MSG%"=="" set MSG=quick update

git add .
git commit -m "%MSG%"
git push origin main
