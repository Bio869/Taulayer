import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrendingUp, Clock, DollarSign, Target } from "lucide-react";

interface MetricsData {
  totalTimeSaved: number;
  totalCostSaved: number;
  averageQualityLift: number;
  totalOptimizations: number;
}
type PeriodType = "7d" | "30d" | "ytd";
interface MetricsOverviewProps {
  data?: Record<PeriodType, MetricsData>;
}

export const MetricsOverview = ({
  data = {
    "7d": { totalTimeSaved: 12800000, totalCostSaved: 8.23, averageQualityLift: 12.1, totalOptimizations: 47 },
    "30d": { totalTimeSaved: 45600000, totalCostSaved: 24.56, averageQualityLift: 18.3, totalOptimizations: 143 },
    "ytd": { totalTimeSaved: 186400000, totalCostSaved: 142.89, averageQualityLift: 22.7, totalOptimizations: 687 }
  }
}: MetricsOverviewProps) => {
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>("30d");

  const periodLabels: Record<PeriodType, string> = {
    "7d": "Past 7 Days",
    "30d": "Past 30 Days",
    "ytd": "Year to Date"
  };

  const current = data[selectedPeriod];
  const formatTime = (ms: number) => {
    const h = Math.floor(ms / 3_600_000);
    const m = Math.floor((ms % 3_600_000) / 60_000);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };
  const formatCurrency = (v: number) => `$${v.toFixed(2)}`;

  const metrics = [
    { title: "Total Time Saved", value: formatTime(current.totalTimeSaved), icon: Clock, color: "text-blue-600", bg: "bg-blue-50", change: "+23% vs last period" },
    { title: "Total Cost Saved", value: formatCurrency(current.totalCostSaved), icon: DollarSign, color: "text-green-600", bg: "bg-green-50", change: "+15% vs last period" },
    { title: "Average Quality Lift", value: `${current.averageQualityLift}%`, icon: Target, color: "text-purple-600", bg: "bg-purple-50", change: "+12% vs last period" },
    { title: "Total Optimizations", value: String(current.totalOptimizations), icon: TrendingUp, color: "text-orange-600", bg: "bg-orange-50", change: "+31% vs last period" }
  ];

  return (
    <section className="space-y-4">
      {/* Header + period tabs */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold text-base sm:text-lg text-foreground">Performance Overview</h2>
        <div className="hidden sm:flex gap-1 rounded-lg bg-muted p-1">
          {(["7d", "30d", "ytd"] as PeriodType[]).map((p) => (
            <Button
              key={p}
              variant={selectedPeriod === p ? "default" : "ghost"}
              size="sm"
              onClick={() => setSelectedPeriod(p)}
              className="px-3 py-1 text-xs"
            >
              {periodLabels[p]}
            </Button>
          ))}
        </div>
        <select
          className="sm:hidden w-auto rounded-md border bg-background px-2 py-1 text-sm"
          value={selectedPeriod}
          onChange={(e) => setSelectedPeriod(e.target.value as PeriodType)}
        >
          <option value="7d">Past 7 Days</option>
          <option value="30d">Past 30 Days</option>
          <option value="ytd">Year to Date</option>
        </select>
      </div>

      {/* Desktop/tablet grid — unaffected */}
      <div className="hidden md:grid grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m, i) => (
          <Card key={i} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{m.title}</CardTitle>
              <span className={`p-2 rounded-full ${m.bg}`}>
                <m.icon className={`h-4 w-4 ${m.color}`} />
              </span>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                <div className="text-2xl font-bold tabular-nums text-foreground">{m.value}</div>
                <p className="text-xs text-muted-foreground">{m.change}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Mobile-only carousel (scoped) */}
      <div className="block md:hidden -mx-2 px-2">
        <div
          className="
            flex gap-4 overflow-x-auto pb-2
            snap-x snap-mandatory
            [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden
            [scroll-padding-inline:8px]
            touch-pan-x
          "
          aria-label="Swipe metrics"
        >
          {metrics.map((m, i) => (
            <Card
              key={i}
              className="
                snap-center shrink-0
                basis-[90%] max-w-[520px]
                hover:shadow-md transition-shadow
              "
            >
              <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-sm font-medium text-muted-foreground">{m.title}</CardTitle>
                <span className={`rounded-full ${m.bg} p-2`}>
                  <m.icon className={`h-4 w-4 ${m.color}`} />
                </span>
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <div className="space-y-1">
                  <div className="text-xl font-semibold tabular-nums text-foreground">{m.value}</div>
                  <p className="text-xs text-muted-foreground">{m.change}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};
