import React, { useEffect, useRef } from 'react';

/**
 * Real-time audio waveform responding to Web Audio API analyser frequencies.
 * Displays clean, clinical teal animated bars.
 */
export function AudioWaveform({ analyser, isActive, isMuted }) {
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const BAR_COUNT = 24;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      let values = new Uint8Array(BAR_COUNT);
      if (analyser && isActive && !isMuted) {
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.getByteFrequencyData(dataArray);

        // Subsample frequency bins into BAR_COUNT bars
        const step = Math.floor(bufferLength / BAR_COUNT);
        for (let i = 0; i < BAR_COUNT; i++) {
          values[i] = dataArray[i * step] || 0;
        }
      }

      const totalWidth = canvas.width;
      const barWidth = 3;
      const gap = (totalWidth - BAR_COUNT * barWidth) / (BAR_COUNT - 1);
      const centerY = canvas.height / 2;

      for (let i = 0; i < BAR_COUNT; i++) {
        // Calculate height based on volume or subtle idle breathing wave
        let height = 4;
        if (isActive && !isMuted) {
          const normalized = values[i] / 255;
          height = Math.max(4, normalized * (canvas.height - 8));
        } else if (isActive && isMuted) {
          height = 3;
        }

        const x = i * (barWidth + gap);
        const y = centerY - height / 2;

        ctx.fillStyle = isMuted ? '#94A3B8' : '#0D9488';
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, height, 2);
        ctx.fill();
      }

      animationFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [analyser, isActive, isMuted]);

  return (
    <div className="w-full flex items-center justify-center py-2">
      <canvas
        ref={canvasRef}
        width={180}
        height={36}
        className="block"
      />
    </div>
  );
}
