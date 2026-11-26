"""Speech-to-Text provider factory (ElevenLabs Segmented Scribe v2 primary, Realtime fallback)."""

import io
import logging
import tempfile
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .pipecat_imports import (
    ElevenLabsRealtimeSTTService,
    ElevenLabsSTTService,
    CommitStrategy,
    Language,
)

try:
    from loguru import logger
except ImportError:  # pragma: no cover
    logger = logging.getLogger(__name__)


def _summarize_wav(audio_data: bytes) -> Dict[str, Any]:
    """Extract duration, amplitude, silence, and clipping stats from WAV bytes."""
    try:
        with wave.open(io.BytesIO(audio_data), "rb") as wf:
            params = wf.getparams()
            pcm = wf.readframes(params.nframes)
        arr = np.frombuffer(pcm, dtype=np.int16)
        n = len(arr)
        if n == 0 or params.framerate == 0:
            return {"dur_s": 0.0, "sr": params.framerate, "rms": 0.0, "peak": 0, "zero_pct": 100.0, "clip_pct": 0.0}
        rms = float(np.sqrt(np.mean(arr.astype(np.float64) ** 2)))
        peak = int(np.abs(arr).max())
        zero_pct = float(np.mean(np.abs(arr) < 16) * 100.0)
        clip_pct = float(np.mean(np.abs(arr) >= 32700) * 100.0)
        return {
            "dur_s": round(params.nframes / params.framerate, 2),
            "sr": params.framerate,
            "rms": round(rms, 1),
            "peak": peak,
            "zero_pct": round(zero_pct, 1),
            "clip_pct": round(clip_pct, 1),
        }
    except Exception:
        return {"dur_s": 0.0, "sr": 0, "rms": 0.0, "peak": 0, "zero_pct": 0.0, "clip_pct": 0.0}


def _diagnostic_hint(stats: Dict[str, Any]) -> str:
    """Return an acoustic diagnostic hint explaining why STT returned empty text."""
    if stats["rms"] < 25:
        return "very quiet/muted microphone"
    if stats["zero_pct"] > 55:
        return "choppy audio / heavy AEC suppression or packet drops"
    if stats["clip_pct"] > 1.0:
        return "heavy microphone clipping/distortion"
    return "no recognizable speech detected by Scribe"


if ElevenLabsSTTService and isinstance(ElevenLabsSTTService, type) and hasattr(ElevenLabsSTTService, "run_stt"):
    class DiagnosticElevenLabsSTTService(ElevenLabsSTTService):
        """
        ElevenLabsSTTService with per-segment acoustic telemetry, incoming audio
        cadence tracking, WAV dump on empty output, and safe metric cleanup.
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._rx_window_start: float | None = None
            self._rx_bytes: int = 0
            self._last_rx_ts: float | None = None
            self._max_gap_ms: float = 0.0
            self._rx_sr: int = 0
            self._rx_ch: int = 0

        async def process_audio_frame(self, frame, direction):
            now = time.perf_counter()
            if self._rx_window_start is None:
                self._rx_window_start = now
            if self._last_rx_ts is not None:
                gap_ms = (now - self._last_rx_ts) * 1000.0
                if gap_ms > self._max_gap_ms:
                    self._max_gap_ms = gap_ms
            self._last_rx_ts = now
            self._rx_bytes += len(getattr(frame, "audio", b""))
            self._rx_sr = getattr(frame, "sample_rate", 0)
            self._rx_ch = getattr(frame, "num_channels", 0)
            await super().process_audio_frame(frame, direction)

        def _pop_rx_cadence(self) -> str:
            now = time.perf_counter()
            elapsed = (now - self._rx_window_start) if self._rx_window_start else 0.0
            kbps = (self._rx_bytes / 1024.0 / elapsed) if elapsed > 0 else 0.0
            gap = round(self._max_gap_ms, 1)
            sr, ch = self._rx_sr, self._rx_ch
            self._rx_window_start = now
            self._rx_bytes = 0
            self._max_gap_ms = 0.0
            return f"rx={kbps:.1f}KB/s gap_max={gap}ms in={sr}Hz/{ch}ch"

        async def _transcribe_audio(self, audio_data: bytes) -> dict:
            stats = _summarize_wav(audio_data)
            cadence = self._pop_rx_cadence()
            t0 = time.perf_counter()
            result = await super()._transcribe_audio(audio_data)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            text = (result.get("text") or "").strip()
            lang = result.get("language_code", "?")
            prob = result.get("language_probability")
            prob_str = f"{prob:.2f}" if isinstance(prob, (int, float)) else "?"

            if text:
                logger.info(
                    f"[STT] dur={stats['dur_s']}s rms={stats['rms']} peak={stats['peak']} "
                    f"zero={stats['zero_pct']}% clip={stats['clip_pct']}% {cadence} {latency_ms}ms "
                    f"lang={lang}({prob_str}) -> {text!r}"
                )
            else:
                hint = _diagnostic_hint(stats)
                dump_path = Path(tempfile.gettempdir()) / "voice_doctor_last_stt.wav"
                try:
                    dump_path.write_bytes(audio_data)
                except Exception:
                    pass
                logger.warning(
                    f"[STT EMPTY] dur={stats['dur_s']}s rms={stats['rms']} peak={stats['peak']} "
                    f"zero={stats['zero_pct']}% clip={stats['clip_pct']}% {cadence} {latency_ms}ms "
                    f"lang={lang}({prob_str}) ({hint}) saved={dump_path}"
                )
            return result

        async def run_stt(self, audio: bytes):
            yielded = False
            async for frame in super().run_stt(audio):
                yielded = True
                yield frame
            if not yielded and hasattr(self, "stop_processing_metrics"):
                await self.stop_processing_metrics()
else:
    DiagnosticElevenLabsSTTService = ElevenLabsSTTService


def create_stt_service(
    elevenlabs_key: Optional[str],
    aiohttp_session: Any = None,
    keyterms: Optional[List[str]] = None,
) -> Any:
    """
    Creates the STT service.
    Prioritizes ElevenLabsSTTService (SegmentedSTTService / REST Scribe v2) with
    the pooled aiohttp_session so every InputAudioRawFrame passes unobstructed to
    LLMUserAggregator's Silero VAD while only VAD-bounded speech (with pre-speech
    rolling buffer and trailing silence padding) is transcribed accurately.
    Falls back to ElevenLabsRealtimeSTTService if aiohttp_session is unavailable.
    """
    if DiagnosticElevenLabsSTTService and aiohttp_session is not None:
        try:
            stt = DiagnosticElevenLabsSTTService(
                api_key=elevenlabs_key,
                aiohttp_session=aiohttp_session,
                ttfs_p99_latency=2.01,
                settings=ElevenLabsSTTService.Settings(
                    language="en",
                    tag_audio_events=False,
                    keyterms=keyterms,
                ),
            )
            logger.info("Using DiagnosticElevenLabsSTTService (segmented Scribe v2 via pooled aiohttp_session)")
            return stt
        except Exception as e:
            logger.warning(f"ElevenLabsSTTService init failed ({e}), falling back to Realtime STT")

    if ElevenLabsRealtimeSTTService:
        if hasattr(ElevenLabsRealtimeSTTService, "Settings") and CommitStrategy:
            logger.info("Using ElevenLabsRealtimeSTTService (CommitStrategy.VAD fallback)")
            return ElevenLabsRealtimeSTTService(
                api_key=elevenlabs_key,
                commit_strategy=CommitStrategy.VAD,
                settings=ElevenLabsRealtimeSTTService.Settings(
                    language=Language.EN if Language is not None else "en",
                    keyterms=keyterms,
                    vad_silence_threshold_secs=0.2,
                    vad_threshold=0.15,
                    min_speech_duration_ms=100,
                    min_silence_duration_ms=400,
                ),
            )
        return ElevenLabsRealtimeSTTService(api_key=elevenlabs_key)

    import aiohttp as _aiohttp
    return ElevenLabsSTTService(
        api_key=elevenlabs_key,
        aiohttp_session=_aiohttp.ClientSession(),
        settings=ElevenLabsSTTService.Settings(
            language="en",
            tag_audio_events=False,
            keyterms=keyterms,
        ),
    )
