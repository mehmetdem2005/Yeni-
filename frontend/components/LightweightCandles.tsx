'use client';

import { useEffect, useRef } from 'react';
import { createChart, ColorType, type IChartApi, type ISeriesApi, type CandlestickData, type HistogramData } from 'lightweight-charts';
import { bollingerBands, emaLine } from '@/lib/chart-indicators';

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
  showVolume?: boolean;
  showEma?: boolean;
  showBollinger?: boolean;
  emaPeriod?: number;
};

function toUnixTime(timestamp: string) {
  return Math.floor(new Date(timestamp).getTime() / 1000);
}

export function LightweightCandles({ candles, height = 390, showVolume = true, showEma = true, showBollinger = false, emaPeriod = 50 }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const emaRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbUpperRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbMiddleRef = useRef<ISeriesApi<'Line'> | null>(null);
  const bbLowerRef = useRef<ISeriesApi<'Line'> | null>(null);

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

    const emaSeries = chart.addLineSeries({
      color: '#2563eb',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      title: `EMA ${emaPeriod}`,
    });

    const bbUpper = chart.addLineSeries({ color: 'rgba(124, 58, 237, 0.65)', lineWidth: 1, priceLineVisible: false, lastValueVisible: false, title: 'BB Üst' });
    const bbMiddle = chart.addLineSeries({ color: 'rgba(124, 58, 237, 0.42)', lineWidth: 1, priceLineVisible: false, lastValueVisible: false, title: 'BB Orta' });
    const bbLower = chart.addLineSeries({ color: 'rgba(124, 58, 237, 0.65)', lineWidth: 1, priceLineVisible: false, lastValueVisible: false, title: 'BB Alt' });

    chartRef.current = chart;
    candleRef.current = candleSeries;
    volumeRef.current = volumeSeries;
    emaRef.current = emaSeries;
    bbUpperRef.current = bbUpper;
    bbMiddleRef.current = bbMiddle;
    bbLowerRef.current = bbLower;

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
      emaRef.current = null;
      bbUpperRef.current = null;
      bbMiddleRef.current = null;
      bbLowerRef.current = null;
    };
  }, [height, emaPeriod]);

  useEffect(() => {
    if (!candleRef.current || !volumeRef.current || !emaRef.current || !chartRef.current || !bbUpperRef.current || !bbMiddleRef.current || !bbLowerRef.current) return;

    const candleData: CandlestickData[] = candles.map((item) => ({
      time: toUnixTime(item.timestamp) as CandlestickData['time'],
      open: Number(item.open),
      high: Number(item.high),
      low: Number(item.low),
      close: Number(item.close),
    }));

    const volumeData: HistogramData[] = showVolume
      ? candles.map((item) => ({
          time: toUnixTime(item.timestamp) as HistogramData['time'],
          value: Number(item.volume),
          color: Number(item.close) >= Number(item.open) ? 'rgba(22, 163, 74, 0.28)' : 'rgba(220, 38, 38, 0.24)',
        }))
      : [];

    const emaData = showEma ? emaLine(candles, emaPeriod) : [];
    const bands = showBollinger ? bollingerBands(candles, 20, 2) : { upper: [], middle: [], lower: [] };

    candleRef.current.setData(candleData);
    volumeRef.current.setData(volumeData);
    emaRef.current.setData(emaData);
    bbUpperRef.current.setData(bands.upper);
    bbMiddleRef.current.setData(bands.middle);
    bbLowerRef.current.setData(bands.lower);
    chartRef.current.timeScale().fitContent();
  }, [candles, showVolume, showEma, showBollinger, emaPeriod]);

  if (!candles.length) {
    return (
      <div style={{ minHeight: height, display: 'grid', placeItems: 'center', color: 'var(--muted)' }}>
        Grafik için mum verisi yok. API canlı veriyle doldurmayı deneyecek.
      </div>
    );
  }

  return <div ref={containerRef} style={{ width: '100%', minHeight: height }} />;
}
