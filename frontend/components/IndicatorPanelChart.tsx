'use client';

import { useEffect, useRef } from 'react';
import { createChart, ColorType, type IChartApi, type ISeriesApi, type LineData } from 'lightweight-charts';

type Point = {
  time: number;
  value: number;
};

type Props = {
  title: string;
  points: Point[];
  height?: number;
  color?: string;
  minValue?: number;
  maxValue?: number;
  guideLines?: Array<{ value: number; label: string }>;
};

export function IndicatorPanelChart({ title, points, height = 150, color = '#2563eb', minValue, maxValue, guideLines = [] }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const lineRef = useRef<ISeriesApi<'Line'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#667085',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#f1f5f9' },
        horzLines: { color: '#f1f5f9' },
      },
      rightPriceScale: {
        borderColor: '#dde5f1',
      },
      timeScale: {
        borderColor: '#dde5f1',
        timeVisible: true,
      },
    });
    if (minValue !== undefined || maxValue !== undefined) {
      chart.priceScale('right').applyOptions({
        autoScale: false,
        scaleMargins: { top: 0.08, bottom: 0.08 },
      });
    }
    const line = chart.addLineSeries({ color, lineWidth: 2, title, priceLineVisible: false });
    chartRef.current = chart;
    lineRef.current = line;

    const resize = () => {
      if (!containerRef.current) return;
      chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    resize();
    window.addEventListener('resize', resize);

    return () => {
      window.removeEventListener('resize', resize);
      chart.remove();
      chartRef.current = null;
      lineRef.current = null;
    };
  }, [height, color, title, minValue, maxValue]);

  useEffect(() => {
    if (!lineRef.current || !chartRef.current) return;
    const data: LineData[] = points.map((point) => ({ time: point.time as LineData['time'], value: point.value }));
    lineRef.current.setData(data);
    chartRef.current.timeScale().fitContent();
  }, [points]);

  if (!points.length) {
    return <div style={{ minHeight: height, display: 'grid', placeItems: 'center', color: 'var(--muted)' }}>{title} için yeterli veri yok.</div>;
  }

  return (
    <div style={{ display: 'grid', gap: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>
        <span>{title}</span>
        {guideLines.length ? <span>{guideLines.map((line) => `${line.label}: ${line.value}`).join(' · ')}</span> : null}
      </div>
      <div ref={containerRef} style={{ width: '100%', minHeight: height }} />
    </div>
  );
}
