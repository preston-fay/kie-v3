/**
 * KDS Design Tokens
 *
 * Official Kearney Design System tokens for dashboard UI.
 * NO arbitrary colors - only KDS-approved palette.
 */

export const tokens = {
  // KDS Color Palette (hex values)
  colors: {
    // Primary brand
    kearneyPurple: '#7823DC',
    kearneyBlack: '#1E1E1E',
    kearneyWhite: '#FFFFFF',

    // Purple family
    brightPurple: '#9150E1',
    mediumPurple: '#AF7DEB',
    lightPurple: '#C8A5F0',
    palePurple: '#E0D2FA',

    // Neutrals
    charcoal: '#4B4B4B',
    darkGray: '#787878',
    mediumGray: '#A5A6A5',
    lightGray: '#D2D2D2',
  },

  // Semantic color mapping (KDS-compliant)
  semantic: {
    background: 'var(--background)',
    surface: 'var(--card)',
    border: 'var(--border)',
    text: 'var(--foreground)',
    textMuted: 'var(--muted-foreground)',
    primary: 'var(--primary)',
    accent: 'var(--accent)',
  },

  // Typography scale (restrained, consultant-appropriate)
  typography: {
    pageTitle: {
      fontSize: '2rem',      // 32px
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.01em',
    },
    sectionTitle: {
      fontSize: '1.5rem',    // 24px
      fontWeight: 700,
      lineHeight: 1.3,
      letterSpacing: '-0.005em',
    },
    subsectionTitle: {
      fontSize: '1.125rem',  // 18px
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body: {
      fontSize: '0.875rem',  // 14px
      fontWeight: 400,
      lineHeight: 1.5,
    },
    caption: {
      fontSize: '0.75rem',   // 12px
      fontWeight: 400,
      lineHeight: 1.4,
    },
  },

  // Spacing scale
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
  },

  // Border radius
  radius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
  },
} as const;

export type Tokens = typeof tokens;
