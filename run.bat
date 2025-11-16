@echo off
chcp 65001 >nul
echo ========================================
echo Python程序启动脚本
echo ========================================
echo.

REM 自动检测Python命令
set PYTHON_CMD=
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
    )
)

REM 检查是否找到Python
if "%PYTHON_CMD%"=="" (
    echo [错误] 未检测到Python或Python3，请确保Python已安装并添加到环境变量
    echo.
    pause
    exit /b 1
)

echo [信息] 使用命令: %PYTHON_CMD%
echo [信息] Python版本:
%PYTHON_CMD% --version
echo.

REM 检查Python版本是否大于等于3.13
echo [信息] 正在检查Python版本要求...
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i

REM 提取主版本号和次版本号
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR_VERSION=%%a
    set MINOR_VERSION=%%b
)

REM 版本检查
set VERSION_OK=0
if %MAJOR_VERSION% gtr 3 set VERSION_OK=1
if %MAJOR_VERSION% equ 3 if %MINOR_VERSION% geq 13 set VERSION_OK=1

if %VERSION_OK% equ 0 (
    echo [错误] Python版本不满足要求！
    echo [要求] Python 3.13 或更高版本
    echo [当前] Python %PYTHON_VERSION%
    echo.
    echo 请升级Python版本后再运行此程序
    echo.
    pause
    exit /b 1
)

echo [成功] Python版本检查通过 ^(需要: ^>= 3.13, 当前: %PYTHON_VERSION%^)
echo.

REM 检查main.py是否存在
if not exist "main.py" (
    echo [错误] 找不到main.py文件，请确保脚本在正确的目录下运行
    echo 当前目录: %CD%
    echo.
    pause
    exit /b 1
)

REM 检查config.ini是否存在
if not exist "config.ini" (
    echo [警告] 找不到config.ini文件，程序可能无法正常运行
    echo.
)

echo [信息] 开始运行Python程序...
echo [信息] 命令: %PYTHON_CMD% main.py -c config.ini
echo ========================================
echo.

REM 运行Python程序，无论成功或失败都不退出
%PYTHON_CMD% main.py -c config.ini

REM 捕获退出码
set EXIT_CODE=%errorlevel%

echo.
echo ========================================
if %EXIT_CODE% equ 0 (
    echo [成功] 程序正常结束，退出码: %EXIT_CODE%
) else (
    echo [错误] 程序异常退出，退出码: %EXIT_CODE%
)
echo ========================================
echo.
echo 按任意键关闭窗口...
pause >nul