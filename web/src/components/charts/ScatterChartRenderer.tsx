/**
 * Scatter Chart Renderer
 *
 * Renders scatter plots from Python-generated RechartsConfig with KDS compliance.
 * Enforces: no gridlines, no axis lines, no tick lines, Inter font, KDS colors.
 */

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ZAxis,
} from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

interface ScatterChartRendererProps {
  config: {
    type: string;
    data: Array<Record<string, any>>;
    config: {
      title?: string;
      subtitle?: string;
      width?: number;
      height?: number;
      margin?: { top: number; right: number; bottom: number; left: number };
      xAxis: {
        dataKey: string;
        axisLine?: boolean;
        tickLine?: boolean;
        tick?: Record<string, any>;
        type?: 'number' | 'category';
      };
      yAxis: {
        dataKey: string;
        axisLine?: boolean;
        tickLine?: boolean;
        tick?: Record<string, any>;
        type?: 'number' | 'category';
      };
      scatter: {
        dataKey: string;
        fill: string;
        shape?: 'circle' | 'cross' | 'diamond' | 'square' | 'star' | 'triangle' | 'wye';
      };
      legend?: {
        verticalAlign?: 'top' | 'middle' | 'bottom';
        align?: 'left' | 'center' | 'right';
        iconType?: string;
        wrapperStyle?: Record<string, any>;
      };
      tooltip?: {
        contentStyle?: Record<string, any>;
        labelStyle?: Record<string, any>;
        itemStyle?: Record<string, any>;
      };
      gridLines?: boolean;
      fontFamily?: string;
    };
  };
}

/**
 * ScatterChartRenderer
 *
 * KDS Compliance:
 * - axisLine: false (enforced)
 * - tickLine: false (enforced)
 * - gridLines: false (enforced)
 * - fontFamily: Inter (enforced)
 * - Colors from KDS palette (from Python config)
 */
export function ScatterChartRenderer({ config }: ScatterChartRendererProps) {
  const { colors } = useTheme();
  const chartConfig = config.config;

  // KDS-compliant defaults
  const height = chartConfig.height || 400;
  const margin = chartConfig.margin || { top: 20, right: 30, bottom: 20, left: 40 };

  // KDS: NO axis lines or tick lines (enforced)
  const axisLineStyle = false;
  const tickLineStyle = false;

  // Tick styling (KDS-compliant)
  const tickStyle = {
    fill: colors.textSecondary,
    fontSize: 12,
    fontFamily: chartConfig.fontFamily || 'Inter, sans-serif',
  };

  // Tooltip styling (theme-aware)
  const tooltipStyle = chartConfig.tooltip?.contentStyle || {
    backgroundColor: colors.backgroundSecondary,
    border: `1px solid ${colors.borderSecondary}`,
    borderRadius: '4px',
    padding: '8px',
    fontSize: 12,
  };

  // Legend styling
  const legendStyle = chartConfig.legend?.wrapperStyle || {
    fontSize: 12,
    fontFamily: 'Inter, sans-serif',
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart
        data={config.data}
        margin={margin}
      >
        {/* KDS: No gridlines */}
        <CartesianGrid strokeDasharray="0" stroke="transparent" />

        {/* X Axis - KDS compliant */}
        <XAxis
          dataKey={chartConfig.xAxis.dataKey}
          axisLine={axisLineStyle}
          tickLine={tickLineStyle}
          tick={tickStyle}
          type={chartConfig.xAxis.type || 'number'}
          name={chartConfig.xAxis.dataKey}
        />

        {/* Y Axis - KDS compliant */}
        <YAxis
          dataKey={chartConfig.yAxis.dataKey}
          axisLine={axisLineStyle}
          tickLine={tickLineStyle}
          tick={tickStyle}
          type={chartConfig.yAxis.type || 'number'}
          name={chartConfig.yAxis.dataKey}
        />

        {/* Z Axis (optional - for bubble size) */}
        <ZAxis range={[60, 400]} />

        {/* Tooltip */}
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={chartConfig.tooltip?.labelStyle}
          itemStyle={chartConfig.tooltip?.itemStyle}
          cursor={{ strokeDasharray: '3 3' }}
        />

        {/* Legend */}
        {chartConfig.legend && (
          <Legend
            verticalAlign={chartConfig.legend.verticalAlign || 'bottom'}
            align={chartConfig.legend.align || 'center'}
            iconType={chartConfig.legend.iconType as any || 'circle'}
            wrapperStyle={legendStyle}
          />
        )}

        {/* Scatter Points */}
        <Scatter
          name={chartConfig.scatter.dataKey}
          data={config.data}
          fill={chartConfig.scatter.fill}
          shape={chartConfig.scatter.shape || 'circle'}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export default ScatterChartRenderer;
