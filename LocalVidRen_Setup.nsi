; LocalVidRen NSIS 安装包脚本
; 使用 NSIS (Nullsoft Scriptable Install System) 编译

!include "MUI2.nsh"
!include "FileFunc.nsh"

; ==================== 基本配置 ====================
Name "LocalVidRen"
OutFile "LocalVidRen_Setup.exe"
InstallDir "$PROGRAMFILES64\LocalVidRen"
InstallDirRegKey HKLM "Software\LocalVidRen" "InstallDir"

; ==================== 版本信息 ====================
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "LocalVidRen"
VIAddVersionKey "FileDescription" "本地短视频智能重命名系统"
VIAddVersionKey "LegalCopyright" "Copyright © 2024"
VIAddVersionKey "FileVersion" "1.0.0"

; ==================== 界面配置 ====================
!define MUI_ABORTWARNING
!define MUI_ICON "installer.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"

; ==================== 页面配置 ====================
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; ==================== 语言配置 ====================
!insertmacro MUI_LANGUAGE "SimpChinese"

; ==================== 压缩配置 ====================
SetCompressor /SOLID lz4

; ==================== 安装过程 ====================
Section "MainProgram" SEC01
    SetOutPath "$INSTDIR"

    ; 复制主程序文件
    File /r "src\*"
    File "start.md"
    File "README.md"
    File "MODEL_INTERFACE.md"
    File "requirements.txt"
    File "LocalVidRen.bat"
    File "config\config.yaml"

    ; 创建配置目录
    CreateDirectory "$INSTDIR\models"
    CreateDirectory "$INSTDIR\logs"

    ; 创建桌面快捷方式
    CreateDesktopLink "$DESKTOP\LocalVidRen.lnk" "$INSTDIR\LocalVidRen.bat" "" ""
    CreateShortCut "$DESKTOP\LocalVidRen.lnk" "$INSTDIR\LocalVidRen.bat" "" ""

    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\LocalVidRen"
    CreateShortCut "$SMPROGRAMS\LocalVidRen\LocalVidRen.lnk" "$INSTDIR\LocalVidRen.bat" "" ""
    CreateShortCut "$SMPROGRAMS\LocalVidRen\卸载.lnk" "$INSTDIR\uninstall.exe" "" ""
    CreateShortCut "$SMPROGRAMS\LocalVidRen\README.lnk" "$INSTDIR\README.md" "" ""

    ; 写入注册表
    WriteRegStr HKLM "Software\LocalVidRen" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\LocalVidRen" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\LocalVidRen" "DisplayName" "LocalVidRen"
    WriteRegStr HKLM "Software\LocalVidRen" "DisplayIcon" "$INSTDIR\app.ico"
    WriteRegDWORD HKLM "Software\LocalVidRen" "Version" "100"
SectionEnd

Section "PythonRuntime" SEC02
    ; 检查是否已安装 Python
    ReadRegStr $0 HKLM "SOFTWARE\Python\PythonCore\InstalledVersions" ""
    IfErrors PythonNotFound

    ; Python 已安装，跳过
    Goto PythonSkip

PythonNotFound:
    ; 下载并安装 Python 3.11 嵌入式版本
    ; 注意：实际使用时需要下载 Python 嵌入式版本到临时目录

    ; 这里使用简化的方式，用户需要手动安装 Python
    MessageBox MB_OK "LocalVidRen 需要 Python 3.11+ 环境。\n\n" + `
        "请访问 https://www.python.org/downloads/ 下载安装。" + `
        "安装时请勾选 'Add Python to PATH'。"
SectionEnd

Section "FFmpeg" SEC03
    ; FFmpeg 可以预下载或使用系统已安装的版本
    ; 这里提供选项让用户选择

    MessageBox MB_YESNO "是否安装 FFmpeg？\n\n" + `
        "FFmpeg 用于视频处理。\n" + `
        "如果已安装，请选择否。" /SD IDNO
    ${If} $0 == IDYES
        ; 下载并解压 FFmpeg
        ; File "ffmpeg.exe"
        ; File "ffprobe.exe"
        ; File "libffmpeg.dll"
    ${EndIf}
SectionEnd

Section "Models" SEC04
    ; 可选：下载推荐模型文件
    ; 这些文件较大，建议用户手动下载

    MessageBox MB_YESNO "是否下载推荐模型？\n\n" + `
        "faster-whisper-base (约 150MB)\n" + `
        "Qwen2-VL-2B-Instruct (约 1.5GB)" + `
        "建议首次运行时下载。" /SD IDYES
    ${If} $0 == IDYES
        ; 显示进度条
        ; 下载模型文件
        ; File "models\faster-whisper-base.zip"
        ; File "models\Qwen2-VL-2B-Instruct-q4_k_m.gguf"
    ${EndIf}
SectionEnd

; ==================== 卸载过程 ====================
Section "Uninstall"
    ; 删除文件
    RMDir /r "$INSTDIR\src"
    RMDir /r "$INSTDIR\models"
    RMDir /r "$INSTDIR\logs"
    RMDir /r "$INSTDIR\config"

    ; 删除配置文件
    Delete "$INSTDIR\start.md"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\MODEL_INTERFACE.md"
    Delete "$INSTDIR\requirements.txt"
    Delete "$INSTDIR\LocalVidRen.bat"
    Delete "$INSTDIR\config.yaml"

    ; 删除快捷方式
    Delete "$DESKTOP\LocalVidRen.lnk"
    Delete "$SMPROGRAMS\LocalVidRen\LocalVidRen.lnk"
    Delete "$SMPROGRAMS\LocalVidRen\卸载.lnk"
    Delete "$SMPROGRAMS\LocalVidRen\README.lnk"
    RMDir "$SMPROGRAMS\LocalVidRen"

    ; 删除注册表项
    DeleteRegKey HKLM "Software\LocalVidRen"

    ; 删除安装目录
    RMDir "$INSTDIR"
SectionEnd

; ==================== 插件和依赖 ====================
; 需要 NSIS 插件：
; - MUI2.nsh (现代界面)
; - FileFunc.nsh (函数工具)
; - Inetc.nsh (HTTP 下载)
; - URLDownload.nsh (URL 下载)

; ==================== 编译说明 ====================
; 1. 安装 NSIS: https://nsis.sourceforge.io/Download
; 2. 将本文件保存为 LocalVidRen_Setup.nsi
; 3. 准备图标文件：installer.ico, header.bmp, app.ico
; 4. 编译：makensis LocalVidRen_Setup.nsi
; 5. 输出：LocalVidRen_Setup.exe
