/**
 * KDS-Compliant Badge Component
 *
 * Uses ONLY KDS-approved colors (purple family + neutrals).
 * NO traffic light colors (green/yellow/red/blue).
 */

import * as React from 'react';
import { AlertCircle, CheckCircle2, Info } from 'lucide-react';

type BadgeVariant =
  | 'decision'
  | 'direction'
  | 'info'
  | 'ok'
  | 'caveat'
  | 'internal';

interface BadgeProps {
  variant: BadgeVariant;
  children?: React.ReactNode;
}

const badgeStyles: Record<
  BadgeVariant,
  {
    className: string;
    icon?: React.ComponentType<{ className?: string }>;
    defaultLabel?: string;
  }
> = {
  // Actionability badges (section-level)
  decision: {
    className:
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-primary text-white border border-primary',
    icon: CheckCircle2,
    defaultLabel: 'DECISION',
  },
  direction: {
    className:
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-transparent text-primary border border-primary',
    icon: Info,
    defaultLabel: 'DIRECTION',
  },
  info: {
    className:
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-muted/30 text-muted-foreground border border-border',
    icon: Info,
    defaultLabel: 'INFO',
  },

  // Visual quality badges (chart-level)
  ok: {
    className:
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-primary/10 text-primary border border-primary/30',
    icon: CheckCircle2,
    defaultLabel: 'OK',
  },
  caveat: {
    className:
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-muted text-foreground border border-border',
    icon: AlertCircle,
    defaultLabel: '⚠️ Caveat',
  },
  internal: {
    className:
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-charcoal text-muted-foreground border border-muted',
    defaultLabel: 'Internal Only',
  },
};

export function Badge({ variant, children }: BadgeProps) {
  const style = badgeStyles[variant];
  const Icon = style.icon;
  const label = children || style.defaultLabel;

  return (
    <span className={style.className}>
      {Icon && <Icon className="w-3.5 h-3.5" />}
      {label}
    </span>
  );
}
