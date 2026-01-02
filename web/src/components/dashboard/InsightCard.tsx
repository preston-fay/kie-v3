/**
 * Insight Card Component
 *
 * Displays analytical insights and findings following KDS patterns.
 */

import { LightbulbIcon, AlertCircle, CheckCircle, Info, type LucideIcon } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

interface InsightCardProps {
  title: string;
  description: string;
  type?: 'insight' | 'warning' | 'success' | 'info';
  icon?: LucideIcon;
  metric?: string;
  metricLabel?: string;
  className?: string;
}

/**
 * InsightCard - Displays analytical insights
 *
 * KDS Compliance:
 * - Clean typography
 * - Color-coded by insight type
 * - Icon support from Lucide
 * - Responsive design
 */
export function InsightCard({
  title,
  description,
  type = 'insight',
  icon,
  metric,
  metricLabel,
  className = '',
}: InsightCardProps) {
  const { colors } = useTheme();

  // Icon and color by type
  const getIconAndColor = () => {
    if (icon) {
      return { Icon: icon, color: colors.brandPrimary };
    }

    switch (type) {
      case 'warning':
        return { Icon: AlertCircle, color: colors.warning };
      case 'success':
        return { Icon: CheckCircle, color: colors.success };
      case 'info':
        return { Icon: Info, color: colors.info };
      default:
        return { Icon: LightbulbIcon, color: colors.brandPrimary };
    }
  };

  const { Icon, color } = getIconAndColor();

  return (
    <div
      className={`bg-bg-secondary rounded-lg border border-border-secondary p-6 ${className}`}
      style={{ fontFamily: 'Inter, sans-serif' }}
    >
      {/* Header with icon */}
      <div className="flex items-start gap-3 mb-3">
        <div
          className="p-2 rounded-lg"
          style={{ backgroundColor: colors.backgroundTertiary }}
        >
          <Icon
            className="w-5 h-5"
            style={{ color }}
          />
        </div>
        <div className="flex-1">
          <h3
            className="font-semibold text-base mb-1"
            style={{ color: colors.textPrimary }}
          >
            {title}
          </h3>
        </div>
      </div>

      {/* Description */}
      <p
        className="text-sm leading-relaxed mb-3"
        style={{ color: colors.textSecondary }}
      >
        {description}
      </p>

      {/* Optional metric */}
      {metric && (
        <div className="mt-4 pt-4 border-t" style={{ borderColor: colors.borderSecondary }}>
          <div className="flex items-baseline justify-between">
            <span className="text-xs" style={{ color: colors.textTertiary }}>
              {metricLabel || 'Key Metric'}
            </span>
            <span
              className="text-xl font-bold"
              style={{ color: colors.brandPrimary }}
            >
              {metric}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default InsightCard;
