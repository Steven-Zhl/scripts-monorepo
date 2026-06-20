"""
利用PaddleOCR进行视频硬字幕提取的脚本，推理后端使用Transformers+PyTorch
环境依赖：
- paddleocr
- paddlex[ocr]
- torch (按需使用CPU版或CUDA版)
- transformers
- torchvision
- opencv-python
- pillow
- pysrt
- tqdm
系统依赖：
- FFmpeg
- FFprobe
"""

import json
import subprocess
from typing import Generator, TypedDict

import cv2
import numpy as np
import pysrt
import torch
from paddleocr import PaddleOCR
from paddlex.inference.pipelines.ocr.result import OCRResult
from pathlib import Path
from tqdm import tqdm


class SubtitleItem(TypedDict):
    start_time: int  # 单位ms
    end_time: int  # 单位ms
    content: str


class VideoInfo(TypedDict):
    path: Path
    frame_count: int
    fps: float
    duration_second: float
    width: int
    height: int


def get_backend() -> PaddleOCR:
    if torch.cuda.is_available():
        device = "gpu:0"
    else:
        device = "cpu"
    return PaddleOCR(
        text_detection_model_name="PP-OCRv6_medium_det",
        text_recognition_model_name="PP-OCRv6_medium_rec",
        engine="transformers",
        device=device,
        use_doc_orientation_classify=False,  # 文档方向分类
        use_doc_unwarping=False,  # 文本图像矫正
        use_textline_orientation=True,  # 文本行方向分类
        text_rec_score_thresh=0.8,
    )


def edit_distance(a: str, b: str) -> int:
    """计算两个字符串的编辑距离（Levenshtein distance）"""
    if len(a) < len(b):
        a, b = b, a
    # 只用两行，节省内存
    prev = list(range(len(b) + 1))
    curr = [0] * (len(b) + 1)
    for i, ca in enumerate(a, 1):
        curr[0] = i
        for j, cb in enumerate(b, 1):
            curr[j] = (
                prev[j - 1] if ca == cb else 1 + min(prev[j], curr[j - 1], prev[j - 1])
            )
        prev, curr = curr, prev
    return prev[-1]


def get_video_info(file: Path) -> VideoInfo:
    """使用 ffprobe 获取视频元信息"""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)

    video_stream = next(s for s in data["streams"] if s["codec_type"] == "video")

    fps_num, fps_den = map(int, video_stream["r_frame_rate"].split("/"))
    fps = fps_num / fps_den
    width = video_stream["width"]
    height = video_stream["height"]

    nb_frames = video_stream.get("nb_frames")
    if nb_frames is not None:
        frame_count = int(nb_frames)
    else:
        frame_count = int(float(data["format"]["duration"]) * fps)

    return VideoInfo(
        path=file,
        frame_count=frame_count,
        fps=fps,
        duration_second=float(data["format"]["duration"]),
        width=width,
        height=height,
    )


def stream_frames(
        file: Path,
        info: VideoInfo,
) -> Generator[tuple[int, np.ndarray], None, None]:
    """使用 ffmpeg 每秒抽取一帧，yield (秒数, RGB 帧)"""
    w, h = info["width"], info["height"]
    duration = int(info["duration_second"])

    args = [
        "ffmpeg",
        "-hwaccel",
        "cuda",
        "-i",
        str(file),
        "-vf",
        "fps=1",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert proc.stdout is not None

    frame_size = w * h * 3
    try:
        for second in range(duration):
            raw = proc.stdout.read(frame_size)
            if len(raw) < frame_size:
                break
            frame = np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3))
            yield second, frame
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()


def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    """转为灰度并裁切底部 30%（字幕区域）"""
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    h, _ = gray.shape
    return gray[int(h * 0.7): h, :]


def parse_ocr_result(predict_result: list[OCRResult]) -> str | None:
    """从 PaddleOCR 结果中提取文本，无文本返回 None"""
    chunks: list[str] = []
    for chunk in predict_result:
        if texts := chunk.get("rec_texts"):
            chunks.extend(texts)
    result = " ".join(t.strip() for t in chunks)
    return result if result.strip() else None


def should_merge(a: str, b: str) -> bool:
    """判断两段 OCR 文本是否应视为同一条字幕"""
    dist = edit_distance(a, b)
    threshold = max(2, int(min(len(a), len(b)) * 0.3))
    return dist <= threshold


def export_srt(subtitles: list[SubtitleItem], output: Path) -> None:
    """将字幕列表导出为 SRT 文件"""
    items = [
        pysrt.SubRipItem(
            start=pysrt.SubRipTime(milliseconds=sub["start_time"]),
            end=pysrt.SubRipTime(milliseconds=sub["end_time"]),
            text=sub["content"],
        )
        for sub in subtitles
        if sub.get("start_time") != sub.get("end_time") and len(sub.get("content")) > 1
    ]
    pysrt.SubRipFile(items).save(str(output), encoding="utf-8")


def main(file: Path) -> list[SubtitleItem]:
    ocr = get_backend()
    info = get_video_info(file)

    subtitle_result: list[SubtitleItem] = []
    subtitle_buffer: SubtitleItem | None = None

    for second, frame in tqdm(
            stream_frames(file, info),
            total=int(info["duration_second"]),
    ):
        text = parse_ocr_result(ocr.predict(preprocess_frame(frame)))
        if text is None:
            continue

        current_ms = second * 1000
        if subtitle_buffer is None:
            subtitle_buffer = SubtitleItem(
                start_time=current_ms,
                end_time=current_ms,
                content=text,
            )
        elif should_merge(text, subtitle_buffer["content"]):
            subtitle_buffer["end_time"] = current_ms
        else:
            subtitle_buffer["end_time"] = current_ms
            subtitle_result.append(subtitle_buffer)
            subtitle_buffer = SubtitleItem(
                start_time=current_ms,
                end_time=current_ms,
                content=text,
            )

    if subtitle_buffer is not None:
        subtitle_result.append(subtitle_buffer)

    export_srt(subtitle_result, file.with_suffix(".srt"))
    return subtitle_result


if __name__ == "__main__":
    main(Path("input.mp4"))
