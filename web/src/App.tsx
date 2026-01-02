/**
 * KIE v3 Dashboard Application
 *
 * Main application component showcasing KDS-compliant dashboard.
 */

import { ThemeProvider } from './contexts/ThemeContext';
import { ThemeToggle } from './components/ThemeToggle';
import { DashboardLayout } from './components/dashboard/DashboardLayout';
import { KPICard } from './components/dashboard/KPICard';
import { InsightCard } from './components/dashboard/InsightCard';
import { ChartRenderer } from './components/charts/ChartRenderer';
import { DollarSign, Users, ShoppingCart, TrendingUp } from 'lucide-react';

// Sample data for demonstration
const sampleBarChartConfig = {
  type: 'bar' as const,
  title: 'Revenue by Region',
  data: [
    { region: 'North', revenue: 125000 },
    { region: 'South', revenue: 98000 },
    { region: 'East', revenue: 145000 },
    { region: 'West', revenue: 110000 },
  ],
  config: {
    height: 300,
    xAxis: {
      dataKey: 'region',
      axisLine: false,
      tickLine: false,
    },
    yAxis: {
      axisLine: false,
      tickLine: false,
    },
    bars: [
      {
        dataKey: 'revenue',
        fill: '#7823DC', // Kearney Purple
        radius: [4, 4, 0, 0],
      },
    ],
    gridLines: false,
    fontFamily: 'Inter, sans-serif',
  },
};

const sampleLineChartConfig = {
  type: 'line' as const,
  title: 'Monthly Growth Trend',
  data: [
    { month: 'Jan', value: 100 },
    { month: 'Feb', value: 120 },
    { month: 'Mar', value: 115 },
    { month: 'Apr', value: 140 },
    { month: 'May', value: 155 },
    { month: 'Jun', value: 170 },
  ],
  config: {
    height: 300,
    xAxis: {
      dataKey: 'month',
      axisLine: false,
      tickLine: false,
    },
    yAxis: {
      axisLine: false,
      tickLine: false,
    },
    lines: [
      {
        dataKey: 'value',
        stroke: '#7823DC',
        strokeWidth: 2,
      },
    ],
    fontFamily: 'Inter, sans-serif',
  },
};

function App() {
  return (
    <ThemeProvider defaultMode="dark">
      <div className="min-h-screen bg-bg-primary">
        {/* Header */}
        <header className="border-b border-border-secondary bg-bg-secondary">
          <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <div>
              <h1
                className="text-2xl font-bold"
                style={{ color: '#7823DC', fontFamily: 'Inter, sans-serif' }}
              >
                KIE Dashboard
              </h1>
              <p className="text-sm text-text-secondary mt-1">
                Kearney Insight Engine v3.0
              </p>
            </div>
            <ThemeToggle />
          </div>
        </header>

        {/* Main Dashboard */}
        <main className="max-w-7xl mx-auto px-6 py-8">
          <DashboardLayout
            kpis={
              <>
                <KPICard
                  label="Total Revenue"
                  value="$478K"
                  change="+12.5%"
                  trend="up"
                  progress={75}
                  icon={DollarSign}
                />
                <KPICard
                  label="Active Users"
                  value="2,543"
                  change="+8.2%"
                  trend="up"
                  progress={60}
                  icon={Users}
                />
                <KPICard
                  label="Conversion Rate"
                  value="3.2%"
                  change="-2.1%"
                  trend="down"
                  progress={32}
                  icon={ShoppingCart}
                />
                <KPICard
                  label="Growth Rate"
                  value="15.8%"
                  change="+5.4%"
                  trend="up"
                  progress={80}
                  icon={TrendingUp}
                />
              </>
            }
            charts={
              <>
                <ChartRenderer config={sampleBarChartConfig} />
                <ChartRenderer config={sampleLineChartConfig} />
              </>
            }
            insights={
              <>
                <InsightCard
                  title="Strong Q4 Performance"
                  description="Revenue increased by 12.5% compared to Q3, driven primarily by East region sales expansion."
                  type="success"
                  metric="+$52K"
                  metricLabel="Quarter Growth"
                />
                <InsightCard
                  title="Regional Opportunity"
                  description="South region shows potential for growth. Current performance is 32% below average."
                  type="insight"
                  metric="$98K"
                  metricLabel="Current Revenue"
                />
                <InsightCard
                  title="Conversion Decline"
                  description="Monitor conversion rates closely. The 2.1% decline may indicate need for optimization."
                  type="warning"
                  metric="-2.1%"
                  metricLabel="Change"
                />
              </>
            }
          />

          {/* Footer */}
          <footer className="mt-12 pt-8 border-t border-border-secondary">
            <div className="flex items-center justify-between text-sm text-text-tertiary">
              <p>
                Powered by <span style={{ color: '#7823DC', fontWeight: 600 }}>KIE v3.0</span>
              </p>
              <p>
                KDS Compliant • No Gridlines • Kearney Purple #7823DC
              </p>
            </div>
          </footer>
        </main>
      </div>
    </ThemeProvider>
  );
}

export default App;
