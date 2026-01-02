/**
 * Line Chart Renderer
 *
 * Renders line charts from Python-generated RechartsConfig with KDS compliance.
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

interface LineChartRendererProps {
  config: {
    type: string;
    data: Array<Record<string, any>>;
    config: {
      height?: number;
      margin?: { top: number; right: number; bottom: number; left: number };
      xAxis: {
        dataKey: string;
        axisLine?: boolean;
        tickLine?: boolean;
        tick?: Record<string, any>;
      };
      yAxis: {
        axisLine?: boolean;
        tickLine?: boolean;
        tick?: Record<string, any>;
      };
      lines: Array<{
        dataKey: string;
        stroke: string;
        strokeWidth?: number;
        dot?: Record<string, any> | boolean;
        activeDot?: Record<string, any>;
        label?: any;
      }>;
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
      fontFamily?: string;
    };
  };
}

/**
 * LineChartRenderer
 *
 * KDS Compliance:
 * - axisLine: false
 * - tickLine: false
 * - No gridlines
 * - Inter font
 */
export function LineChartRenderer({ config }: LineChartRendererProps) {
  const { colors } = useTheme();
  const chartConfig = config.config;

  const height = chartConfig.height || 400;
  const margin = chartConfig.margin || { top: 20, right: 30, bottom: 20, left: 40 };

  const tickStyle = {
    fill: colors.textSecondary,
    fontSize: 12,
    fontFamily: chartConfig.fontFamily || 'Inter, sans-serif',
  };

  const tooltipStyle = chartConfig.tooltip?.contentStyle || {
    backgroundColor: colors.backgroundSecondary,
    border: `1px solid ${colors.borderSecondary}`,
    borderRadius: '4px',
    padding: '8px',
    fontSize: 12,
  };

  const legendStyle = chartConfig.legend?.wrapperStyle || {
    fontSize: 12,
    fontFamily: 'Inter, sans-serif',
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={config.data} margin={margin}>
        {/* KDS: No gridlines */}
        <CartesianGrid strokeDasharray="0" stroke="transparent" />

        {/* X Axis - KDS compliant */}
        <XAxis
          dataKey={chartConfig.xAxis.dataKey}
          axisLine={false}
          tickLine={false}
          tick={tickStyle}
        />

        {/* Y Axis - KDS compliant */}
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={tickStyle}
        />

        {/* Tooltip */}
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={chartConfig.tooltip?.labelStyle}
          itemStyle={chartConfig.tooltip?.itemStyle}
        />

        {/* Legend */}
        {chartConfig.legend && chartConfig.lines.length > 1 && (
          <Legend
            verticalAlign={chartConfig.legend.verticalAlign || 'bottom'}
            align={chartConfig.legend.align || 'center'}
            iconType={chartConfig.legend.iconType as any || 'line'}
            wrapperStyle={legendStyle}
          />
        )}

        {/* Lines */}
        {chartConfig.lines.map((line, index) => (
          <Line
            key={index}
            type="monotone"
            dataKey={line.dataKey}
            stroke={line.stroke}
            strokeWidth={line.strokeWidth || 2}
            dot={line.dot !== undefined ? line.dot : { r: 4 }}
            activeDot={line.activeDot || { r: 6 }}
            label={line.label}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export default LineChartRenderer;
