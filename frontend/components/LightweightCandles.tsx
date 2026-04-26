'use client';

import { useEffect, useRef } from 'react';
import { createChart, ColorType, type IChartApi, type ISeriesApi, type CandlestickData, type HistogramData } from 'lightweight-charts';

type Candle = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type Props = {
  candles: Candle[];
  height?: number;
};

function toUnixTime(timestamp: string) {
  return Math.floor(new Date(timestamp).getTime() / 1000);
}

export function LightweightCandles({ candles, height = 390 }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#475467',
        fontSize: 12,
      },
      grid: {
        vertLines: { color: '#edf2f7' },
        horzLines: { color: '#edf2f7' },
      },
      rightPriceScale: {
        borderColor: '#dde5f1',
      },
      timeScale: {
        borderColor: '#dde5f1',
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#16a34a',
      downColor: '#dc2626',
      borderUpColor: '#16a34a',
      borderDownColor: '#dc2626',
      wickUpColor: '#16a34a',
      wickDownColor: '#dc2626',
    });

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: '',
      color: '#93c5fd',
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.82,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candleRef.current = candleSeries;
    volumeRef.current = volumeSeries;

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
      candleRef.current = null;
      volumeRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!candleRef.current || !volumeRef.current || !chartRef.current) return;

    const candleData: CandlestickData[] = candles.map((item) => ({
      time: toUnixTime(item.timestamp) as CandlestickData['time'],
      open: Number(item.open),
      high: Number(item.high),
      low: Number(item.low),
      close: Number(item.close),
    }));

    const volumeData: HistogramData[] = candles.map((item) => ({
      time: toUnixTime(item.timestamp) as HistogramData['time'],
      value: Number(item.volume),
      color: Number(item.close) >= Number(item.open) ? 'rgba(22, 163, 74, 0.28)' : 'rgba(220, 38, 38, 0.24)',
    }));

    candleRef.current.setData(candleData);
    volumeRef.current.setData(volumeData);
    chartRef.current.timeScale().fitContent();
  }, [candles]);

  if (!candles.length) {
    return (
      <div style={{ minHeight: height, display: 'grid', placeItems: 'center', color: 'var(--muted)' }}>
        Grafik için mum verisi yok. Önce veri toplama/worker çalışmalı.
      </div>
    );
  }

  return <div ref={containerRef} style={{ width: '100%', minHeight: height }} />;
}
