# Python脚本

## 目录

* [Python脚本](#python脚本)
  * [目录](#目录)
  * [FxxkChromiumSecurity.py](#fxxkchromiumsecuritypy)
  * [SortShellHistory.py](#sortshellhistorypy)
  * [YNU\_TimetableConvert](#ynu_timetableconvert)
  * [VideoSubtitleExtractor](#videosubtitleextractor)

## [FxxkChromiumSecurity.py](./FxxkChromiumSecurity.py)

> * 一个用于显示Chromium浏览器中，账号密码数据库的工具（仅限于Windows端Chrome和Edge，但相信大多数人的主要浏览器都是这两者之一）
>
> * （Chromium在账号安全性的保护上有够偷懒，用数据库存账号密码没问题，虽然密码也加密了，但架不住密钥也直接放在本地）
>
> * 好在经过测试，这段代码要跑起来的要求还是挺高的：必须使用Python执行源码，并且需要以下全部库的支持。

    ⚠⚠注意：本文件仅用于学习交流，请勿用作非法用途，所造成的一切后果不承担相关责任。

* 环境要求
  * Python 3
    * win32crypt
    * cryptography
    * base64
    * sqlite3
    * json

* 用法
  * 在Python环境中运行即可

* ChangeLog
  * 2023-01-09
    * 完成代码编写
  * 2023-10-07
    * 修复了一点点bug
    * 2023-10-07测试，Edge和Chrome仍然在摆烂

## [SortShellHistory.py](./SortShellHistory.py)

> 整理`PowerShell`/`Bash`/`Zsh`的历史命令记录的脚本，主要功能为去重、排序，以及删去包含屏蔽词的命令

* 环境要求
  * Python 3
  * PowerShell / Bash / Zsh

* 用法
  * 在Shell中调用Python执行即可，可通过`-h`或`--help`查看帮助

* ChangeLog
  * 2024-06-06
    * 完成初版编写
  * 2025-02-03
    * 支持Bash和Zsh，改用命令行参数的方式执行

## [YNU_TimetableConvert](./YNU_TimetableConvert)

> 将YNU教务系统中的课程表进行格式转换的脚本，使之适应各种第三方日程类应用

* 环境要求
  * Python 3
    * openpyxl
    * csv

* 用法
  * 详见该脚本的[README.md](./YNU_TimetableConvert/README.md)

* ChangeLog
  * 2022-12-26
    * 完成代码编写
  * 2023-02-20
    * 修复了2个bug

## [VideoSubtitleExtractor](./VideoSubtitleExtractor.py)

> 利用PaddleOCR进行视频硬字幕（内嵌字幕）提取的脚本，推理后端使用Transformers+PyTorch，自动检测并使用GPU（CUDA）或CPU
>
> * 通过`ffmpeg`每秒抽取一帧，裁切底部30%作为字幕区域送入OCR识别
> * 相邻帧文本基于编辑距离判断是否为同一条字幕，合并连续相同的字幕条目，最终导出为SRT文件

* 环境要求
  * Python 3
    * paddleocr
    * paddlex[ocr]
    * torch（按需使用CPU版或CUDA版）
    * transformers
    * torchvision
    * opencv-python
    * pillow
    * pysrt
    * tqdm
  * 系统依赖
    * FFmpeg
    * FFprobe

* 用法
  * 修改脚本末尾`main(Path("input.mp4"))`中的视频路径后在Python环境中运行，字幕将导出为同名`.srt`文件

* ChangeLog
  * 2026-07-12
    * 完成代码编写
