/**
 * Bar Chart Renderer
 *
 * Renders bar charts from Python-generated RechartsConfig with KDS compliance.
 * Enforces: no gridlines, no axis lines, no tick lines, Inter font, KDS colors.
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

interface BarChartRendererProps {
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
      };
      yAxis: {
        dataKey?: string;
        axisLine?: boolean;
        tickLine?: boolean;
        tick?: Record<string, any>;
      };
      bars: Array<{
        dataKey: string;
        fill: string;
        radius?: number[];
        label?: any;
      }>;
      layout?: 'horizontal' | 'vertical';
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
 * BarChartRenderer
 *
 * KDS Compliance:
 * - axisLine: false (enforced)
 * - tickLine: false (enforced)
 * - gridLines: false (enforced)
 * - fontFamily: Inter (enforced)
 * - Colors from KDS palette (from Python config)
 */
export function BarChartRenderer({ config }: BarChartRendererProps) {
  const { colors } = useTheme();
  const chartConfig = config.config;

  // KDS-compliant defaults
  const height = chartConfig.height || 400;
  const margin = chartConfig.margin || { top: 20, right: 30, bottom: 20, left: 40 };
  const layout = chartConfig.layout || 'horizontal';

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
      <BarChart
        data={config.data}
        margin={margin}
        layout={layout}
      >
        {/* KDS: No gridlines */}
        <CartesianGrid strokeDasharray="0" stroke="transparent" />

        {/* X Axis - KDS compliant */}
        <XAxis
          dataKey={chartConfig.xAxis.dataKey}
          axisLine={axisLineStyle}
          tickLine={tickLineStyle}
          tick={tickStyle}
          type={layout === 'vertical' ? 'number' : 'category'}
        />

        {/* Y Axis - KDS compliant */}
        <YAxis
          axisLine={axisLineStyle}
          tickLine={tickLineStyle}
          tick={tickStyle}
          type={layout === 'vertical' ? 'category' : 'number'}
        />

        {/* Tooltip */}
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={chartConfig.tooltip?.labelStyle}
          itemStyle={chartConfig.tooltip?.itemStyle}
        />

        {/* Legend (if multiple series) */}
        {chartConfig.legend && chartConfig.bars.length > 1 && (
          <Legend
            verticalAlign={chartConfig.legend.verticalAlign || 'bottom'}
            align={chartConfig.legend.align || 'center'}
            iconType={chartConfig.legend.iconType as any || 'square'}
            wrapperStyle={legendStyle}
          />
        )}

        {/* Bars */}
        {chartConfig.bars.map((bar, index) => (
          <Bar
            key={index}
            dataKey={bar.dataKey}
            fill={bar.fill}
            radius={(bar.radius || [4, 4, 0, 0]) as [number, number, number, number]}
            label={bar.label}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export default BarChartRenderer;
