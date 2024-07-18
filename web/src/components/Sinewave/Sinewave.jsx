import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

export default function Sinewave({
  maxAmplitude,
  length,
  frequency,
  y,
  style,
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    canvas.width = window.innerWidth;
    canvas.height = 50;

    let increment = Math.random() * 360;
    let amplitude = 0;

    const draw = () => {
      // Clear the canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Set stroke style for the sine wave
      ctx.strokeStyle = '#90caf9';

      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);

      for (let i = 0; i < canvas.width; i += 1) {
        ctx.lineTo(
          i,
          (y !== undefined ? y : canvas.height / 2) + Math.sin(i / length + increment) * amplitude,
        );
      }

      ctx.stroke();
      ctx.closePath();

      amplitude = Math.sin(increment) * maxAmplitude;
      increment -= frequency / 1000;

      requestAnimationFrame(draw);
    };

    draw();

  }, [maxAmplitude, length, frequency, y]);

  return <canvas ref={canvasRef} style={style} />;
}

Sinewave.propTypes = {
  maxAmplitude: PropTypes.number,
  length: PropTypes.number,
  frequency: PropTypes.number,
  y: PropTypes.number,
  style: PropTypes.object
};

Sinewave.defaultProps = {
  maxAmplitude: 20,
  length: 100,
  frequency: 15,
  y: undefined,
  style: {}
};
