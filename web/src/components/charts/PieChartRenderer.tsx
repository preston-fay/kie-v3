/**
 * Pie Chart Renderer
 *
 * Renders pie/donut charts from Python-generated RechartsConfig with KDS compliance.
 */

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

interface PieChartRendererProps {
  config: {
    type: string;
    data: Array<Record<string, any>>;
    config: {
      height?: number;
      margin?: { top: number; right: number; bottom: number; left: number };
      pie: {
        dataKey: string;
        nameKey: string;
        cx?: string | number;
        cy?: string | number;
        innerRadius?: number;
        outerRadius?: number;
        paddingAngle?: number;
        label?: any;
      };
      colors: string[];
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
 * PieChartRenderer
 *
 * KDS Compliance:
 * - Uses KDS color palette (from Python config)
 * - Inter font
 * - Labels positioned outside
 */
export function PieChartRenderer({ config }: PieChartRendererProps) {
  const { colors } = useTheme();
  const chartConfig = config.config;

  const height = chartConfig.height || 400;

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

  // Custom label renderer (outside positioning)
  const renderLabel = (entry: any) => {
    return entry.name;
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={config.data}
          dataKey={chartConfig.pie.dataKey}
          nameKey={chartConfig.pie.nameKey}
          cx={chartConfig.pie.cx || '50%'}
          cy={chartConfig.pie.cy || '50%'}
          innerRadius={chartConfig.pie.innerRadius || 0}
          outerRadius={chartConfig.pie.outerRadius || 80}
          paddingAngle={chartConfig.pie.paddingAngle || 2}
          label={chartConfig.pie.label !== undefined ? chartConfig.pie.label : renderLabel}
        >
          {config.data.map((_entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={chartConfig.colors[index % chartConfig.colors.length]}
            />
          ))}
        </Pie>

        {/* Tooltip */}
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={chartConfig.tooltip?.labelStyle}
          itemStyle={chartConfig.tooltip?.itemStyle}
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
      </PieChart>
    </ResponsiveContainer>
  );
}

export default PieChartRenderer;
