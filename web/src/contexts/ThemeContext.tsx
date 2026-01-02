/**
 * Theme Context for KIE v3
 *
 * Provides theme management (dark/light) across the application.
 */

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

export type ThemeMode = 'dark' | 'light';

interface ThemeColors {
  backgroundPrimary: string;
  backgroundSecondary: string;
  backgroundTertiary: string;
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  brandPrimary: string;
  brandAccent: string;
  brandLight: string;
  borderPrimary: string;
  borderSecondary: string;
  success: string;
  warning: string;
  error: string;
  info: string;
}

interface ThemeContextType {
  mode: ThemeMode;
  colors: ThemeColors;
  toggleTheme: () => void;
  setTheme: (mode: ThemeMode) => void;
}

// Dark theme colors
const DARK_COLORS: ThemeColors = {
  backgroundPrimary: '#1E1E1E',
  backgroundSecondary: '#2A2A2A',
  backgroundTertiary: '#3A3A3A',
  textPrimary: '#FFFFFF',
  textSecondary: '#E0E0E0',
  textTertiary: '#B0B0B0',
  brandPrimary: '#7823DC',
  brandAccent: '#9B4DCA',
  brandLight: '#E0D2FA',
  borderPrimary: '#7823DC',
  borderSecondary: '#4B4B4B',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
};

// Light theme colors
const LIGHT_COLORS: ThemeColors = {
  backgroundPrimary: '#FFFFFF',
  backgroundSecondary: '#F5F5F5',
  backgroundTertiary: '#E5E5E5',
  textPrimary: '#1E1E1E',
  textSecondary: '#4B4B4B',
  textTertiary: '#787878',
  brandPrimary: '#7823DC',
  brandAccent: '#9B4DCA',
  brandLight: '#E0D2FA',
  borderPrimary: '#7823DC',
  borderSecondary: '#D2D2D2',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
  defaultMode?: ThemeMode;
}

export function ThemeProvider({ children, defaultMode = 'dark' }: ThemeProviderProps) {
  // Load theme from localStorage or use default
  const [mode, setMode] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem('kie-theme');
    return (saved as ThemeMode) || defaultMode;
  });

  // Get current colors
  const colors = mode === 'dark' ? DARK_COLORS : LIGHT_COLORS;

  // Toggle between dark and light
  const toggleTheme = () => {
    setMode((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Set specific theme
  const setTheme = (newMode: ThemeMode) => {
    setMode(newMode);
  };

  // Save to localStorage when mode changes
  useEffect(() => {
    localStorage.setItem('kie-theme', mode);
  }, [mode]);

  // Apply theme to document root
  useEffect(() => {
    const root = document.documentElement;

    // Set theme mode class
    root.classList.remove('dark', 'light');
    root.classList.add(mode);

    // Set CSS variables
    root.style.setProperty('--bg-primary', colors.backgroundPrimary);
    root.style.setProperty('--bg-secondary', colors.backgroundSecondary);
    root.style.setProperty('--bg-tertiary', colors.backgroundTertiary);
    root.style.setProperty('--text-primary', colors.textPrimary);
    root.style.setProperty('--text-secondary', colors.textSecondary);
    root.style.setProperty('--text-tertiary', colors.textTertiary);
    root.style.setProperty('--brand-primary', colors.brandPrimary);
    root.style.setProperty('--brand-accent', colors.brandAccent);
    root.style.setProperty('--brand-light', colors.brandLight);
    root.style.setProperty('--border-primary', colors.borderPrimary);
    root.style.setProperty('--border-secondary', colors.borderSecondary);
    root.style.setProperty('--color-success', colors.success);
    root.style.setProperty('--color-warning', colors.warning);
    root.style.setProperty('--color-error', colors.error);
    root.style.setProperty('--color-info', colors.info);

    // Set background color
    document.body.style.backgroundColor = colors.backgroundPrimary;
    document.body.style.color = colors.textPrimary;
  }, [mode, colors]);

  const value = {
    mode,
    colors,
    toggleTheme,
    setTheme,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * Hook to access theme context
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

/**
 * KDS Chart Colors (same for both themes)
 */
export const KDS_CHART_COLORS = [
  '#D2D2D2', // 1 - Light Gray
  '#A5A6A5', // 2 - Medium Gray
  '#787878', // 3 - Dark Gray
  '#E0D2FA', // 4 - Light Purple
  '#C8A5F0', // 5 - Medium Light Purple
  '#AF7DEB', // 6 - Medium Purple
  '#4B4B4B', // 7 - Charcoal
  '#1E1E1E', // 8 - Black / Kearney Black
  '#9150E1', // 9 - Bright Purple
  '#7823DC', // 10 - Kearney Purple
];
