'use client';

import { useEffect, useRef } from 'react';
import { createChart, ColorType, type HistogramData, type IChartApi, type ISeriesApi, type LineData } from 'lightweight-charts';
import type { MacdPoint } from '@/lib/chart-indicators';

type Props = {
  points: MacdPoint[];
  height?: number;
};

export function MacdPanelChart({ points, height = 170 }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const macdRef = useRef<ISeriesApi<'Line'> | null>(null);
  const signalRef = useRef<ISeriesApi<'Line'> | null>(null);
  const histogramRef = useRef<ISeriesApi<'Histogram'> | null>(null);

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
      rightPriceScale: { borderColor: '#dde5f1' },
      timeScale: { borderColor: '#dde5f1', timeVisible: true },
    });

    const histogram = chart.addHistogramSeries({ priceFormat: { type: 'price', precision: 4, minMove: 0.0001 }, priceLineVisible: false });
    const macd = chart.addLineSeries({ color: '#2563eb', lineWidth: 2, title: 'MACD', priceLineVisible: false });
    const signal = chart.addLineSeries({ color: '#ea580c', lineWidth: 2, title: 'Signal', priceLineVisible: false });

    chartRef.current = chart;
    histogramRef.current = histogram;
    macdRef.current = macd;
    signalRef.current = signal;

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
      histogramRef.current = null;
      macdRef.current = null;
      signalRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!chartRef.current || !macdRef.current || !signalRef.current || !histogramRef.current) return;

    const macdData: LineData[] = points.map((point) => ({ time: point.time as LineData['time'], value: point.macd }));
    const signalData: LineData[] = points.map((point) => ({ time: point.time as LineData['time'], value: point.signal }));
    const histData: HistogramData[] = points.map((point) => ({
      time: point.time as HistogramData['time'],
      value: point.histogram,
      color: point.histogram >= 0 ? 'rgba(22, 163, 74, 0.35)' : 'rgba(220, 38, 38, 0.32)',
    }));

    histogramRef.current.setData(histData);
    macdRef.current.setData(macdData);
    signalRef.current.setData(signalData);
    chartRef.current.timeScale().fitContent();
  }, [points]);

  if (!points.length) {
    return <div style={{ minHeight: height, display: 'grid', placeItems: 'center', color: 'var(--muted)' }}>MACD için yeterli veri yok.</div>;
  }

  return (
    <div style={{ display: 'grid', gap: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>
        <span>MACD 12/26/9</span>
        <span>Mavi: MACD · Turuncu: Signal</span>
      </div>
      <div ref={containerRef} style={{ width: '100%', minHeight: height }} />
    </div>
  );
}
