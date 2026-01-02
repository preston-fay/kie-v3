/**
 * Dashboard Layout Component
 *
 * Main dashboard layout following official KDS specifications:
 * - 4-column KPI grid (responsive: 4-col desktop, 2-col tablet, 1-col mobile)
 * - 2-column main chart grid
 * - 3-column insights grid
 *
 * Based on: /Users/pfay01/Projects/Kearney Design System/src/app/components/kearney/DashboardExample.tsx
 */

import type { ReactNode } from 'react';

interface DashboardLayoutProps {
  kpis?: ReactNode;
  charts?: ReactNode;
  insights?: ReactNode;
  className?: string;
}

/**
 * DashboardLayout - Main dashboard container
 *
 * KDS Compliance:
 * - 4-column KPI grid: `sm:grid-cols-2 lg:grid-cols-4`
 * - 2-column chart grid: `lg:grid-cols-2`
 * - 3-column insight grid: `md:grid-cols-3`
 * - gap-6 spacing throughout
 */
export function DashboardLayout({
  kpis,
  charts,
  insights,
  className = '',
}: DashboardLayoutProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      {/* KPI Grid - 4 columns on desktop, 2 on tablet, 1 on mobile */}
      {kpis && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {kpis}
        </div>
      )}

      {/* Chart Grid - 2 columns on desktop */}
      {charts && (
        <div className="grid lg:grid-cols-2 gap-6">
          {charts}
        </div>
      )}

      {/* Insights Grid - 3 columns on desktop */}
      {insights && (
        <div className="grid md:grid-cols-3 gap-6">
          {insights}
        </div>
      )}
    </div>
  );
}

/**
 * DashboardSection - Generic section wrapper
 *
 * Use this for custom sections that don't fit the standard grids.
 */
interface DashboardSectionProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function DashboardSection({
  title,
  children,
  className = '',
}: DashboardSectionProps) {
  return (
    <div className={`space-y-4 ${className}`}>
      {title && (
        <h2 className="text-xl font-bold text-text-primary">
          {title}
        </h2>
      )}
      <div>{children}</div>
    </div>
  );
}

export default DashboardLayout;
