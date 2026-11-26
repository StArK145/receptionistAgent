"""Smooth jitter-buffered WebRTC audio output track for Pipecat SmallWebRTC."""

import asyncio
import fractions
import time
from collections import deque
from typing import Any

import numpy as np

try:
    from av import AudioFrame
    from pipecat.transports.smallwebrtc.transport import RawAudioTrack
except Exception:  # pragma: no cover - optional runtime imports
    AudioFrame = None
    RawAudioTrack = object


class SmoothAudioTrack(RawAudioTrack):
    """
    Drop-in replacement for Pipecat's RawAudioTrack that eliminates mid-utterance
    zero-silence underruns and post-silence burst transmission.

    Default RawAudioTrack resolves write futures only after the final 10ms chunk
    is popped, leaving the queue empty between every 40ms frame so any minor HTTP
    or OS-timer jitter injects 10ms of hard zeros (audible crackling).
    """

    def __init__(
        self,
        sample_rate: int,
        auto_silence: bool = True,
        lookahead_10ms: int = 8,
    ):
        super().__init__(sample_rate=sample_rate, auto_silence=auto_silence)
        self._lookahead_10ms = lookahead_10ms
        self._pending_futures: deque[tuple[int, asyncio.Future]] = deque()
        self._enqueued_chunks = 0
        self._popped_chunks = 0
        self._perf_start = time.perf_counter()
        self._in_utterance = False
        self._prebuffer_until: float | None = None
        self._last_sample = 0

    def add_audio_bytes(self, audio_bytes: bytes) -> asyncio.Future:
        """Queue 16-bit mono PCM audio in 10ms slices and resolve once buffered ahead."""
        if len(audio_bytes) % self._bytes_per_10ms != 0:
            raise ValueError("Audio bytes must be a multiple of 10ms size.")

        future = asyncio.get_running_loop().create_future()
        n_chunks = len(audio_bytes) // self._bytes_per_10ms
        was_idle = len(self._chunk_queue) == 0 and not self._in_utterance

        for i in range(0, len(audio_bytes), self._bytes_per_10ms):
            self._chunk_queue.append((audio_bytes[i : i + self._bytes_per_10ms], None))

        self._enqueued_chunks += n_chunks
        if was_idle and self._prebuffer_until is None:
            # Cushion utterance onset up to 45ms using normal zero frames (no RTP gap)
            self._prebuffer_until = time.perf_counter() + 0.045

        resolve_at = max(self._popped_chunks + 1, self._enqueued_chunks - self._lookahead_10ms)
        self._pending_futures.append((resolve_at, future))
        self._flush_ready_futures()
        return future

    def _flush_ready_futures(self) -> None:
        while self._pending_futures and self._popped_chunks >= self._pending_futures[0][0]:
            _, fut = self._pending_futures.popleft()
            if not fut.done():
                fut.set_result(True)

    def stop(self) -> None:
        """Resolve pending futures cleanly on teardown before stopping track."""
        while self._pending_futures:
            _, fut = self._pending_futures.popleft()
            if not fut.done():
                fut.set_result(False)
        super().stop()

    def _build_frame(self, samples: np.ndarray) -> Any:
        frame = AudioFrame.from_ndarray(samples[None, :], layout="mono")
        frame.sample_rate = self._sample_rate
        frame.pts = self._timestamp
        frame.time_base = fractions.Fraction(1, self._sample_rate)
        self._timestamp += self._samples_per_10ms
        return frame

    def _pop_next_samples(self) -> np.ndarray:
        self._in_utterance = True
        self._prebuffer_until = None
        chunk, _ = self._chunk_queue.popleft()
        self._popped_chunks += 1
        self._flush_ready_futures()
        samples = np.frombuffer(chunk, dtype=np.int16)
        self._last_sample = int(samples[-1]) if len(samples) else 0
        return samples

    async def recv(self):
        """Return the next 10ms AudioFrame on a steady monotonic clock."""
        if self._timestamp > 0:
            target = self._perf_start + (self._timestamp / self._sample_rate)
            wait = target - time.perf_counter()
            if wait > 0:
                await asyncio.sleep(wait)
            elif wait < -0.04:
                self._perf_start = time.perf_counter() - (self._timestamp / self._sample_rate)

        if not self._in_utterance and self._chunk_queue:
            if (
                len(self._chunk_queue) < 6
                and self._prebuffer_until is not None
                and time.perf_counter() < self._prebuffer_until
            ):
                return self._build_frame(np.zeros(self._samples_per_10ms, dtype=np.int16))

        if self._chunk_queue:
            return self._build_frame(self._pop_next_samples())

        if not self._auto_silence:
            while not self._chunk_queue:
                await asyncio.sleep(0.005)
            self._perf_start = time.perf_counter() - (self._timestamp / self._sample_rate)
            return self._build_frame(self._pop_next_samples())

        self._in_utterance = False
        self._prebuffer_until = None
        samples = np.zeros(self._samples_per_10ms, dtype=np.int16)
        if self._last_sample != 0:
            ramp_len = min(self._samples_per_10ms, max(48, self._sample_rate // 500))
            samples[:ramp_len] = np.linspace(self._last_sample, 0, ramp_len, dtype=np.int16)
            self._last_sample = 0
        return self._build_frame(samples)


def install_smooth_audio_track(transport: Any) -> None:
    """
    Hooks SmallWebRTCClient._handle_client_connected so outbound TTS audio uses
    SmoothAudioTrack instead of Pipecat's default unbuffered RawAudioTrack.
    """
    client = getattr(transport, "_client", None)
    if client is None or RawAudioTrack is object or AudioFrame is None:
        return

    orig_connected = getattr(client, "_handle_client_connected", None)
    if orig_connected is None:
        return

    async def _wrapped_client_connected():
        await orig_connected()
        params = getattr(client, "_params", None)
        conn = getattr(client, "_webrtc_connection", None)
        out_track = getattr(client, "_audio_output_track", None)
        if (
            params
            and getattr(params, "audio_out_enabled", False)
            and conn is not None
            and out_track is not None
            and not isinstance(out_track, SmoothAudioTrack)
        ):
            smooth_track = SmoothAudioTrack(
                sample_rate=client._out_sample_rate,
                auto_silence=params.audio_out_auto_silence,
            )
            out_track.stop()
            client._audio_output_track = smooth_track
            conn.replace_audio_track(smooth_track)

    client._handle_client_connected = _wrapped_client_connected
