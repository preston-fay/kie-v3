/**
 * KPI Card Component
 *
 * Displays key performance indicators following KDS dashboard patterns.
 * Based on official KDS DashboardExample.tsx specification.
 */

import { TrendingUp, TrendingDown, type LucideIcon } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

interface KPICardProps {
  label: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  progress?: number; // 0-100
  icon?: LucideIcon;
  className?: string;
}

/**
 * KPICard - Key Performance Indicator Card
 *
 * KDS Compliance:
 * - Responsive sizing
 * - Trend indicators with color coding
 * - Progress bar
 * - Inter font family
 * - Proper spacing and typography
 */
export function KPICard({
  label,
  value,
  change,
  trend = 'neutral',
  progress,
  icon: Icon,
  className = '',
}: KPICardProps) {
  const { colors } = useTheme();

  // Trend colors
  const trendColor = trend === 'up' ? colors.success : trend === 'down' ? colors.error : colors.textSecondary;
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : null;

  return (
    <div
      className={`bg-bg-secondary rounded-lg border border-border-secondary p-6 ${className}`}
      style={{ fontFamily: 'Inter, sans-serif' }}
    >
      {/* Header with icon */}
      <div className="flex items-start justify-between mb-2">
        <p className="text-sm text-text-secondary">{label}</p>
        {Icon && (
          <Icon
            className="w-5 h-5"
            style={{ color: colors.brandPrimary }}
          />
        )}
      </div>

      {/* Value */}
      <h2
        className="text-3xl font-bold mb-2"
        style={{ color: colors.textPrimary }}
      >
        {value}
      </h2>

      {/* Trend indicator */}
      {change && TrendIcon && (
        <div className="flex items-center gap-1 mb-3">
          <TrendIcon
            className="w-4 h-4"
            style={{ color: trendColor }}
          />
          <span
            className="text-sm font-medium"
            style={{ color: trendColor }}
          >
            {change}
          </span>
        </div>
      )}

      {/* Progress bar */}
      {progress !== undefined && (
        <div className="mt-3">
          <div
            className="h-2 rounded-full overflow-hidden"
            style={{ backgroundColor: colors.backgroundTertiary }}
          >
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(100, Math.max(0, progress))}%`,
                backgroundColor: colors.brandPrimary,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default KPICard;
