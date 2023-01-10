import { Chart } from 'chart.js';
import theme from 'style/theme';
import { CustomChartDataSet } from './GaugeChart';

const drawNeedle = (
  ctx: CanvasRenderingContext2D,
  { x, y }: { x: number; y: number },
  angle: number,
  color: string,
  needleLength: number,
  circleRadius: number,
  type: 'big' | 'small',
) => {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  ctx.beginPath();
  ctx.moveTo(0, -circleRadius);
  ctx.lineTo(needleLength, type === 'small' ? 0 : -1);
  ctx.lineTo(needleLength, 1);
  ctx.lineTo(0, circleRadius);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = 'whitesmoke';
  ctx.stroke();
  ctx.restore();
};

const drawCircle = (
  ctx: CanvasRenderingContext2D,
  { x, y }: { x: number; y: number },
  radius: number,
  color: string,
) => {
  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = 'whitesmoke';
  ctx.stroke();
  ctx.restore();
};

const drawText = (
  ctx: CanvasRenderingContext2D,
  text: string,
  { x, y }: { x: number; y: number },
) => {
  ctx.font = '12px Manrope';
  ctx.fillStyle = theme.colors.gray[6];
  ctx.fillText(text, x, y);
};

export const afterDraw = (chart: Chart) => {
  const { data, needleValues, needleColors } = chart.config.data
    .datasets[0] as CustomChartDataSet<number[]>;
  const dataTotal = data.reduce((a, b) => a + b, 0);
  const angles = needleValues.map(
    (value) => Math.PI + (1 / dataTotal) * value * Math.PI,
  );

  const ctx = chart.ctx;
  const cw = chart.canvas.offsetWidth;

  const paddingBottom = 30;
  const paddingTop = 10;
  const totalPadding = paddingBottom + paddingTop;

  const cx = cw / 2;
  const circleRadius = cx - totalPadding;
  const innerCircleRadius = circleRadius / 10;
  const cy = circleRadius + paddingTop;

  const needleLengthUnit = Math.sqrt(
    Math.pow(circleRadius, 2) + Math.pow(innerCircleRadius / 2, 2),
  );
  const needleLength = [needleLengthUnit, (needleLengthUnit * 35) / 40];

  if (angles[1]) {
    drawNeedle(
      ctx,
      { x: cx, y: cy },
      angles[1],
      needleColors[1],
      needleLength[0],
      innerCircleRadius,
      'big',
    );
  }
  drawCircle(ctx, { x: cx, y: cy }, innerCircleRadius, needleColors[0]);
  drawNeedle(
    ctx,
    { x: cx, y: cy },
    angles[0],
    needleColors[0],
    needleLength[1],
    innerCircleRadius,
    'small',
  );
  drawCircle(ctx, { x: cx, y: cy }, (innerCircleRadius * 2) / 5, 'white');

  const textBottomPadding = 18;
  const rightTextWidth = ctx.measureText(String(dataTotal)).width;
  const rightTextX = circleRadius * 2 + totalPadding - rightTextWidth;
  drawText(ctx, '0', {
    x: totalPadding,
    y: cy + textBottomPadding,
  });
  drawText(ctx, String(dataTotal), {
    x: rightTextX,
    y: cy + textBottomPadding,
  });
};
