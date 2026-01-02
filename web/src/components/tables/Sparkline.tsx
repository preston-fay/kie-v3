/**
 * Sparkline Component
 *
 * Mini charts for table cells (line, bar, area).
 */


import { LineChart, Line, BarChart, Bar, AreaChart, Area, ResponsiveContainer } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

interface SparklineProps {
  data: number[];
  type?: 'line' | 'bar' | 'area';
  color?: string;
  width?: number;
  height?: number;
  showTooltip?: boolean;
}

export function Sparkline({
  data,
  type = 'line',
  color,
  width = 100,
  height = 30,
  showTooltip = false,
}: SparklineProps) {
  const { colors } = useTheme();
  const chartColor = color || colors.brandPrimary;

  // Convert data to format Recharts expects
  const chartData = data.map((value, index) => ({
    index,
    value,
  }));

  const commonProps = {
    width,
    height,
    data: chartData,
    margin: { top: 2, right: 2, bottom: 2, left: 2 },
  };

  switch (type) {
    case 'line':
      return (
        <ResponsiveContainer {...commonProps}>
          <LineChart>
            <Line
              type="monotone"
              dataKey="value"
              stroke={chartColor}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      );

    case 'bar':
      return (
        <ResponsiveContainer {...commonProps}>
          <BarChart>
            <Bar dataKey="value" fill={chartColor} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      );

    case 'area':
      return (
        <ResponsiveContainer {...commonProps}>
          <AreaChart>
            <Area
              type="monotone"
              dataKey="value"
              stroke={chartColor}
              fill={chartColor}
              fillOpacity={0.3}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      );

    default:
      return null;
  }
}

export default Sparkline;
