#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from loguru import logger

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

# Lazy import to avoid forcing heavy deps when not needed
_faster_whisper_model = None

# Optional Vosk
_vosk_model = None


def _ensure_dirs(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


@dataclass
class TranscriptMetadata:
    filename: str
    basename: str
    created_at: Optional[str]
    date: Optional[str]
    time: Optional[str]
    source_path: str
    duration_seconds: Optional[float]
    backend: str


@dataclass
class TranscriptResult:
    text: str
    language: Optional[str]
    segments: Optional[list]
    metadata: TranscriptMetadata


VIDEOS_DIR = Path("data/input/videos")
OUT_DIR = Path("data/processed/transcripts")
MODELS_DIR = Path("data/models")


FILENAME_DT_REGEX = re.compile(r"(\d{4})-(\d{2})-(\d{2})[_-](\d{2})-(\d{2})-(\d{2})")


def parse_datetime_from_filename(name: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    match = FILENAME_DT_REGEX.search(name)
    if not match:
        return None, None, None
    y, m, d, hh, mm, ss = match.groups()
    try:
        dt = datetime(int(y), int(m), int(d), int(hh), int(mm), int(ss))
        return dt.isoformat(), dt.date().isoformat(), dt.time().isoformat(timespec="seconds")
    except Exception:
        return None, None, None


def get_duration_seconds(path: Path) -> Optional[float]:
    try:
        import ffmpeg  # type: ignore

        probe = ffmpeg.probe(str(path))
        for stream in probe.get("streams", []):
            if stream.get("codec_type") == "video":
                if stream.get("duration"):
                    return float(stream["duration"])  # type: ignore
        if probe.get("format", {}).get("duration"):
            return float(probe["format"]["duration"])  # type: ignore
    except Exception:
        return None
    return None


def use_openai() -> bool:
    return os.getenv("OPENAI_API_KEY") is not None and OpenAI is not None


def transcribe_with_openai(video_path: Path) -> Dict[str, Any]:
    client = OpenAI()
    with open(video_path, "rb") as f:
        # Using Whisper-1 transcription
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            temperature=0,
            language="ru",
        )
    # transcript is pydantic-like; convert to dict
    return json.loads(transcript.model_dump_json())  # type: ignore


def load_faster_whisper():
    global _faster_whisper_model
    if _faster_whisper_model is not None:
        return _faster_whisper_model
    from faster_whisper import WhisperModel  # type: ignore

    model_size = os.getenv("WHISPER_MODEL", "small")
    device = os.getenv("WHISPER_DEVICE", "auto")  # auto/cpu/cuda
    compute_type = os.getenv("WHISPER_COMPUTE", "auto")  # auto/int8/float16/float32

    _faster_whisper_model = WhisperModel(model_size, device=device, compute_type=compute_type)
    return _faster_whisper_model


def transcribe_with_faster_whisper(video_path: Path) -> Dict[str, Any]:
    model = load_faster_whisper()
    segments, info = model.transcribe(
        str(video_path), language="ru", vad_filter=True, vad_parameters={"min_silence_duration_ms": 300}
    )
    segs = []
    text_parts = []
    for seg in segments:
        segs.append(
            {
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
            }
        )
        text_parts.append(seg.text.strip())
    return {
        "text": " ".join(text_parts).strip(),
        "language": info.language if hasattr(info, "language") else None,
        "segments": segs,
    }


# ---------------- VOSK FALLBACK -----------------

def ensure_vosk_model() -> Optional[Path]:
    """Ensure a small Russian Vosk model is available. Download if missing."""
    model_env = os.getenv("VOSK_MODEL_PATH")
    if model_env:
        p = Path(model_env)
        return p if p.exists() else None

    target = MODELS_DIR / "vosk-model-small-ru-0.22"
    if target.exists():
        return target

    try:
        import zipfile
        import urllib.request

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        url = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
        zip_path = MODELS_DIR / "vosk-model-small-ru-0.22.zip"
        logger.info("Downloading Vosk RU small model (~50MB) ...")
        urllib.request.urlretrieve(url, zip_path)  # nosec - controlled URL
        logger.info("Extracting model archive ...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(MODELS_DIR)
        zip_path.unlink(missing_ok=True)
        return target
    except Exception as e:
        logger.error("Failed to download Vosk model: {}", e)
        return None


def load_vosk():
    global _vosk_model
    if _vosk_model is not None:
        return _vosk_model
    from vosk import Model  # type: ignore

    model_path = ensure_vosk_model()
    if not model_path:
        raise RuntimeError("Vosk model not available")
    _vosk_model = Model(str(model_path))
    return _vosk_model


def extract_wav_mono16k(src: Path, dst: Path) -> None:
    import ffmpeg  # type: ignore

    stream = ffmpeg.input(str(src))
    audio = stream.audio
    out = ffmpeg.output(audio, str(dst), ac=1, ar=16000, format="wav")
    out = ffmpeg.overwrite_output(out)
    ffmpeg.run(out, quiet=True)


def transcribe_with_vosk(video_path: Path) -> Dict[str, Any]:
    model = load_vosk()
    wav_path = OUT_DIR / f"{video_path.stem}.tmp.wav"
    _ensure_dirs(OUT_DIR)
    extract_wav_mono16k(video_path, wav_path)

    import wave
    from vosk import KaldiRecognizer  # type: ignore

    wf = wave.open(str(wav_path), "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    segments = []
    text_parts = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            if res.get("text"):
                segments.append({"text": res.get("text", "")})
                text_parts.append(res.get("text", ""))
    final = json.loads(rec.FinalResult())
    if final.get("text"):
        segments.append({"text": final.get("text", "")})
        text_parts.append(final.get("text", ""))

    try:
        wf.close()
        wav_path.unlink(missing_ok=True)
    except Exception:
        pass

    return {
        "text": " ".join([t.strip() for t in text_parts if t.strip()]).strip(),
        "language": "ru",
        "segments": segments,
    }


# ------------------------------------------------

def transcribe_file(video_path: Path) -> TranscriptResult:
    created_at, date, time_ = parse_datetime_from_filename(video_path.name)
    duration = get_duration_seconds(video_path)

    raw: Dict[str, Any]
    backend: str

    if use_openai():
        logger.info("Transcribing with OpenAI: {}", video_path.name)
        raw = transcribe_with_openai(video_path)
        backend = "openai-whisper-1"
    else:
        # Prefer faster-whisper, fallback to vosk
        try:
            logger.info("Transcribing with faster-whisper (local): {}", video_path.name)
            raw = transcribe_with_faster_whisper(video_path)
            backend = "faster-whisper"
        except Exception as e_fw:
            logger.warning("faster-whisper failed: {}. Falling back to Vosk.", e_fw)
            raw = transcribe_with_vosk(video_path)
            backend = "vosk-small-ru"

    text = raw.get("text", "")
    language = raw.get("language")
    segments = raw.get("segments")

    metadata = TranscriptMetadata(
        filename=video_path.name,
        basename=video_path.stem,
        created_at=created_at,
        date=date,
        time=time_,
        source_path=str(video_path),
        duration_seconds=duration,
        backend=backend,
    )
    return TranscriptResult(text=text, language=language, segments=segments, metadata=metadata)


def save_transcript(result: TranscriptResult) -> None:
    _ensure_dirs(OUT_DIR)
    base = result.metadata.basename
    json_path = OUT_DIR / f"{base}.json"
    txt_path = OUT_DIR / f"{base}.txt"

    payload = {
        "text": result.text,
        "language": result.language,
        "segments": result.segments,
        "metadata": asdict(result.metadata),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    txt_path.write_text(result.text, encoding="utf-8")
    logger.info("Saved {} and {}", json_path, txt_path)


def main() -> int:
    if not VIDEOS_DIR.exists():
        logger.error("Videos directory not found: {}", VIDEOS_DIR)
        return 1

    files = sorted([p for p in VIDEOS_DIR.iterdir() if p.suffix.lower() == ".mp4"])
    if not files:
        logger.warning("No .mp4 files found in {}", VIDEOS_DIR)
        return 0

    logger.info("Found {} video(s) for transcription", len(files))

    for video in files:
        try:
            result = transcribe_file(video)
            save_transcript(result)
        except Exception as e:
            logger.exception("Failed to transcribe {}: {}", video.name, e)

    logger.info("Transcription complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
