@echo off
echo ==========================================
echo  GITHUBGA YUKLASH TAYYORLOVI
echo ==========================================
echo.
set /p repo_url="GitHub repozitoriy manzilini kiriting (masalan: https://github.com/username/repo.git): "
echo.
git remote add origin %repo_url%
echo.
echo Yuklash boshlandi...
git push -u origin master
echo.
echo ==========================================
echo  TUGADI.
echo ==========================================
pause
