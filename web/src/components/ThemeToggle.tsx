/**
 * Theme Toggle Component
 *
 * Button to switch between dark and light themes.
 */


import { useTheme } from '../contexts/ThemeContext';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
}

export function ThemeToggle({ className = '', showLabel = true }: ThemeToggleProps) {
  const { mode, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-colors ${className}`}
      style={{
        backgroundColor: 'var(--bg-secondary)',
        borderColor: 'var(--border-secondary)',
        color: 'var(--text-primary)',
      }}
      aria-label="Toggle theme"
    >
      {/* Icon */}
      {mode === 'dark' ? (
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
          />
        </svg>
      ) : (
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
      )}

      {/* Label */}
      {showLabel && (
        <span className="font-medium">
          {mode === 'dark' ? 'Dark' : 'Light'}
        </span>
      )}
    </button>
  );
}

export default ThemeToggle;
