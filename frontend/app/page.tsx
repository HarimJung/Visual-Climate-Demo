"use client";

import React, { useEffect, useState } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from "recharts";
import {
  Zap, Sprout, Heart, TrendingUp, Globe, AlertTriangle, Activity,
  ArrowUpRight, ArrowDownRight, Wind, Droplets, Wallet, Users, ChevronDown, List, Download
} from "lucide-react";

// --- Types ---
interface ClusterData {
  current: number | null;
  history: Record<string, number>;
  growth_5y: number | null;
}

interface ClusterGroup {
  [indicatorKey: string]: ClusterData;
}

interface ClusterProfile {
  iso3: string;
  name: string;
  data: {
    energy_transition?: ClusterGroup;
    agricultural_resilience?: ClusterGroup;
    urban_health?: ClusterGroup;
    economic_risk?: ClusterGroup;
  }
}

// --- Icons & Config ---

const CLUSTER_CONFIG = {
  energy_transition: { icon: <Zap className="w-5 h-5" />, color: "text-blue-500", label: "Energy Transition" },
  agricultural_resilience: { icon: <Sprout className="w-5 h-5" />, color: "text-emerald-500", label: "Agricultural Resilience" },
  urban_health: { icon: <Heart className="w-5 h-5" />, color: "text-rose-500", label: "Urban Health" },
  economic_risk: { icon: <Wallet className="w-5 h-5" />, color: "text-purple-500", label: "Economic Risk" }
};

// --- Components ---

function MetricCard({ label, value, trend, unit, icon, colorClass }: any) {
  const isPositive = trend > 0;
  const trendColor = isPositive ? 'text-emerald-500' : 'text-rose-500';

  return (
    <div className="bg-card border border-border/50 p-5 rounded-2xl shadow-sm relative overflow-hidden group hover:border-primary/50 transition-colors">
      <div className={`absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity ${colorClass}`}>
        {icon}
      </div>
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">{label}</p>
      <div className="flex items-baseline space-x-1">
        <span className="text-2xl font-bold tracking-tight text-foreground">{value !== null && value !== undefined ? Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 }) : "-"}</span>
        <span className="text-sm text-muted-foreground font-medium">{unit}</span>
      </div>
      {trend !== null && trend !== undefined && (
        <div className={`flex items-center mt-2 text-xs font-medium ${trendColor}`}>
          {isPositive ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
          {Math.abs(trend).toFixed(1)}% (5y avg)
        </div>
      )}
    </div>
  )
}

function TimeSeriesChart({ title, data, dataKey, color, unit }: any) {
  const chartData = Object.entries(data || {})
    .map(([year, val]) => ({ year: parseInt(year), value: val }))
    .sort((a, b) => a.year - b.year);

  if (chartData.length === 0) return (
    <div className="bg-card border border-border/50 p-6 rounded-2xl shadow-sm h-[250px] flex items-center justify-center text-muted-foreground text-sm">
      No historical data available for {title}
    </div>
  );

  return (
    <div className="bg-card border border-border/50 p-6 rounded-2xl shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-sm font-semibold flex items-center text-foreground">
          {title}
        </h4>
        <span className="text-xs text-muted-foreground px-2 py-1 bg-secondary rounded">{unit}</span>
      </div>
      <div className="h-[200px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.5} />
            <XAxis
              dataKey="year"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
              minTickGap={30}
            />
            <YAxis
              fontSize={10}
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
              width={35}
              tickFormatter={(val) => val >= 1000 ? `${val / 1000}k` : val}
            />
            <Tooltip
              contentStyle={{ backgroundColor: 'hsl(var(--popover))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
              itemStyle={{ color: 'hsl(var(--foreground))' }}
              labelStyle={{ color: 'hsl(var(--muted-foreground))' }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              fill={`url(#gradient-${dataKey})`}
              strokeWidth={2}
              activeDot={{ r: 4 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function DataTable({ profile }: { profile: ClusterProfile }) {
  // Flatten all data for table view
  const allData: any[] = [];
  Object.entries(profile.data).forEach(([clusterKey, indicators]) => {
    Object.entries(indicators as ClusterGroup).forEach(([key, value]) => {
      // Find config to get label
      let label = key;
      let unit = '';
      // Search in our configs (a bit inefficient but works for display)
      // We can reconstruct configs or just use key
      // Let's use a flat loop or switch/case if needed, or better, infer from known configs
      // For now just use key.

      // Get history years
      const history = value.history || {};
      const years = Object.keys(history).sort();
      if (years.length > 0) {
        const startYear = years[0];
        const endYear = years[years.length - 1];
        const startVal = history[startYear];
        const endVal = history[endYear];

        allData.push({
          cluster: clusterKey,
          indicator: key,
          current: value.current,
          growth: value.growth_5y,
          startYear,
          startVal,
          endYear,
          endVal
        });
      }
    });
  });

  const downloadCSV = () => {
    const headers = ["Cluster", "Indicator", "Current Value", "5y Growth Rate", "Start Year", "Start Value", "End Year", "End Value"];
    const rows = allData.map(d => [
      d.cluster,
      d.indicator,
      d.current,
      (d.growth ? (d.growth * 100).toFixed(2) + '%' : ''),
      d.startYear,
      d.startVal,
      d.endYear,
      d.endVal
    ]);

    const csvContent = "data:text/csv;charset=utf-8,"
      + headers.join(",") + "\n"
      + rows.map(e => e.join(",")).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${profile.name}_climate_data.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-card border border-border/50 rounded-2xl shadow-sm overflow-hidden animate-fade-in">
      <div className="p-6 border-b border-border/40 flex justify-between items-center">
        <h3 className="font-semibold text-lg">Detailed Indicators Table</h3>
        <button
          onClick={downloadCSV}
          className="flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <Download className="w-4 h-4" />
          <span>Export CSV</span>
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-secondary/50 text-muted-foreground uppercase text-xs font-semibold">
            <tr>
              <th className="px-6 py-4">Cluster</th>
              <th className="px-6 py-4">Indicator</th>
              <th className="px-6 py-4 text-right">Latest Value</th>
              <th className="px-6 py-4 text-right">5y Growth</th>
              <th className="px-6 py-4 text-right">Trend (First vs Last)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/40">
            {allData.map((row, idx) => (
              <tr key={idx} className="hover:bg-muted/30 transition-colors">
                <td className="px-6 py-4 font-medium capitalize text-muted-foreground">{row.cluster.replace('_', ' ')}</td>
                <td className="px-6 py-4 font-medium text-foreground">{row.indicator.replace(/_/g, ' ')}</td>
                <td className="px-6 py-4 text-right font-mono">{row.current ? Number(row.current).toLocaleString(undefined, { maximumFractionDigits: 2 }) : '-'}</td>
                <td className={`px-6 py-4 text-right font-mono ${row.growth > 0 ? 'text-emerald-500' : (row.growth < 0 ? 'text-rose-500' : '')}`}>
                  {row.growth ? (row.growth * 100).toFixed(1) + '%' : '-'}
                </td>
                <td className="px-6 py-4 text-right text-xs text-muted-foreground">
                  {row.startYear} ({Number(row.startVal).toFixed(1)}) → {row.endYear} ({Number(row.endVal).toFixed(1)})
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ClusterDashboard({ clusterKey, profile }: { clusterKey: string, profile: ClusterProfile }) {
  if (clusterKey === 'data_table') {
    return <DataTable profile={profile} />;
  }

  const clusterData = profile.data[clusterKey as keyof typeof profile.data];

  if (!clusterData) {
    return (
      <div className="p-12 text-center border border-dashed border-border rounded-2xl bg-secondary/10">
        <Activity className="mx-auto w-12 h-12 text-muted-foreground mb-3 opacity-50" />
        <h3 className="text-lg font-medium text-foreground">Data Unavailable</h3>
        <p className="text-muted-foreground">Detailed metrics for this sector are currently missing from the source.</p>
      </div>
    );
  }

  // Refactored to match API Contract v1.0 Keys
  let configs = [];
  if (clusterKey === 'energy_transition') {
    configs = [
      { key: 'renewable_energy', label: 'Renewable Percent', unit: '%', color: '#3b82f6', icon: <Wind /> },
      { key: 'co2_emissions', label: 'CO2 Intensity', unit: 't/cap', color: '#f59e0b', icon: <Globe /> },
      { key: 'access_electricity', label: 'Grid Access', unit: '%', color: '#10b981', icon: <Zap /> },
      { key: 'fossil_fuel_energy_pct', label: 'Fossil Dependency', unit: '%', color: '#ef4444', icon: <AlertTriangle /> },
    ];
  } else if (clusterKey === 'agricultural_resilience') {
    configs = [
      { key: 'cereal_yield', label: 'Cereal Yield', unit: 'kg/ha', color: '#10b981', icon: <Sprout /> },
      { key: 'agricultural_land_pct', label: 'Agri Land', unit: '%', color: '#d97706', icon: <Globe /> },
      { key: 'methane_agriculture_pct', label: 'Methane (Ag)', unit: 'kt', color: '#dc2626', icon: <Wind /> },
      { key: 'freshwater_withdrawal_agri', label: 'Water Withdrawal', unit: '%', color: '#3b82f6', icon: <Droplets /> },
    ];
  } else if (clusterKey === 'urban_health') {
    configs = [
      { key: 'pm25_exposure', label: 'PM2.5 Exposure', unit: 'µg/m³', color: '#64748b', icon: <Wind /> },
      { key: 'urban_population_growth', label: 'Urban Growth', unit: '%', color: '#8b5cf6', icon: <TrendingUp /> },
      { key: 'mortality_air_pollution', label: 'Air Mortality', unit: '/100k', color: '#ef4444', icon: <Activity /> },
      { key: 'sanitation_safe_pct', label: 'Safe Sanitation', unit: '%', color: '#06b6d4', icon: <Heart /> },
    ];
  } else { // Economic Risk
    configs = [
      { key: 'gdp_growth', label: 'GDP Growth', unit: '%', color: '#10b981', icon: <TrendingUp /> },
      { key: 'inflation', label: 'Inflation', unit: '%', color: '#ef4444', icon: <TrendingUp /> },
      { key: 'fdi_net_inflows_pct', label: 'FDI Inflow', unit: '% GDP', color: '#8b5cf6', icon: <Wallet /> },
      { key: 'unemployment', label: 'Unemployment', unit: '%', color: '#f59e0b', icon: <Users /> },
    ];
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {configs.map((cfg) => {
          const item = clusterData[cfg.key];
          return (
            <MetricCard
              key={cfg.key}
              label={cfg.label}
              value={item?.current}
              unit={cfg.unit}
              trend={item?.growth_5y ? item.growth_5y * 100 : null}
              icon={cfg.icon}
              colorClass={cfg.color.replace('text-', 'text-').replace('#', 'text-[')}
            />
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {configs.map((cfg) => (
          <TimeSeriesChart
            key={cfg.key}
            title={cfg.label}
            data={clusterData[cfg.key]?.history}
            dataKey={cfg.key}
            color={cfg.color}
            unit={cfg.unit}
          />
        ))}
      </div>
    </div>
  )
}

// --- Main Page Component ---
export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('energy_transition');
  const [selectedCountry, setSelectedCountry] = useState('KOR');
  const [profile, setProfile] = useState<ClusterProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const countries = [
    { code: 'USA', name: 'United States' },
    { code: 'CHN', name: 'China' },
    { code: 'IND', name: 'India' },
    { code: 'DEU', name: 'Germany' },
    { code: 'KOR', name: 'South Korea' },
    { code: 'JPN', name: 'Japan' },
    { code: 'BRA', name: 'Brazil' },
    { code: 'IDN', name: 'Indonesia' },
    { code: 'ZAF', name: 'South Africa' },
    { code: 'NGA', name: 'Nigeria' },
    { code: 'GBR', name: 'United Kingdom' },
    { code: 'FRA', name: 'France' },
    { code: 'SAU', name: 'Saudi Arabia' },
    { code: 'AUS', name: 'Australia' },
    { code: 'KEN', name: 'Kenya' },
    { code: 'VNM', name: 'Vietnam' }
  ];

  useEffect(() => {
    setLoading(true);
    setError(null);
    const API_URL = "";

    fetch(`${API_URL}/api/v2/country/${selectedCountry}`)
      .then(res => {
        if (!res.ok) throw new Error(`API Error: ${res.status}`);
        return res.json();
      })
      .then(data => {
        setProfile(data);
      })
      .catch(err => {
        console.error("Failed to fetch country profile:", err);
        setError("Could not retrieve data. Backend might be syncing.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedCountry]);

  // Add Data Table Tab Config
  const TABS = [
    ...Object.entries(CLUSTER_CONFIG).map(([key, config]) => ({ key, ...config })),
    { key: 'data_table', icon: <List className="w-5 h-5" />, color: 'text-foreground', label: 'All Datasets' }
  ];

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20">

      {/* Navbar */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/40 transition-all">
        <div className="container mx-auto px-6 h-16 flex justify-between items-center">
          <div className="flex items-center space-x-3 cursor-pointer group">
            <div className="bg-primary/10 p-2 rounded-xl group-hover:bg-primary/20 transition-colors">
              <Globe className="h-5 w-5 text-primary" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight leading-none group-hover:text-primary transition-colors">UN Climate Intelligence</span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest">Live Data Feed</span>
            </div>
          </div>

          {/* Country Selector */}
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-xs text-muted-foreground font-medium">REGION:</span>
            </div>
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="appearance-none bg-secondary/50 hover:bg-secondary border border-border/50 hover:border-border rounded-lg py-2 pl-16 pr-10 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer transition-all shadow-sm"
            >
              {countries.map(c => <option key={c.code} value={c.code}>{c.name} ({c.code})</option>)}
            </select>
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-muted-foreground group-hover:text-foreground transition-colors">
              <ChevronDown size={14} />
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-10 max-w-7xl">
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive p-4 rounded-xl mb-6 text-sm flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-3 bg-gradient-to-br from-foreground to-muted-foreground bg-clip-text text-transparent">
              {countries.find(c => c.code === selectedCountry)?.name || selectedCountry}
            </h1>
            <p className="text-muted-foreground text-lg max-w-2xl leading-relaxed">
              Accessing 34 years of longitudinal data across 21 key UN indicators.
              Analyzing trends in Decarbonization, Resilience, Health, and Economy.
            </p>
          </div>
          <div className="hidden md:block text-right">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Database Coverage</div>
            <div className="text-sm font-medium">1990 - 2023</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-8 p-1.5 bg-secondary/30 rounded-2xl w-fit border border-border/40">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center space-x-2 px-5 py-3 rounded-xl text-sm font-bold transition-all duration-200 ${isActive ? 'bg-background shadow-md text-foreground ring-1 ring-border/50 scale-[1.02]' : 'text-muted-foreground hover:text-foreground hover:bg-background/40'}`}
              >
                <span className={isActive ? tab.color : 'text-muted-foreground'}>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="h-[500px] w-full bg-card/30 border border-dashed border-border rounded-3xl flex flex-col items-center justify-center space-y-6 animate-pulse">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-primary/20 rounded-full"></div>
              <div className="absolute top-0 left-0 w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            </div>
            <div className="text-center space-y-2">
              <h3 className="text-lg font-medium">Establishing Satellite Uplink</h3>
              <p className="text-sm text-muted-foreground">Aggregating {selectedCountry} dataset from World Bank Cloud...</p>
            </div>
          </div>
        ) : (
          <div className="transition-opacity duration-300 ease-in-out">
            {profile && <ClusterDashboard clusterKey={activeTab} profile={profile} />}
          </div>
        )}
      </main>
    </div>
  );
}
