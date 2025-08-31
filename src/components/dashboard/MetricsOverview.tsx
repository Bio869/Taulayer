import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrendingUp, Clock, DollarSign, Target } from "lucide-react";

interface MetricsData {
  totalTimeSaved: number; // in milliseconds
  totalCostSaved: number; // in USD
  averageQualityLift: number; // percentage
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

  const currentData = data[selectedPeriod];

  const formatTime = (ms: number): string => {
    const hours = Math.floor(ms / (1000 * 60 * 60));
    const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
  };

  const formatCurrency = (amount: number): string => `$${amount.toFixed(2)}`;

  const metrics = [
    { title: "Total Time Saved", value: formatTime(currentData.totalTimeSaved), icon: Clock, color: "text-blue-600", bgColor: "bg-blue-50", change: "+23% vs last period" },
    { title: "Total Cost Saved", value: formatCurrency(currentData.totalCostSaved), icon: DollarSign, color: "text-green-600", bgColor: "bg-green-50", change: "+15% vs last period" },
    { title: "Average Quality Lift", value: `${currentData.averageQualityLift}%`, icon: Target, color: "text-purple-600", bgColor: "bg-purple-50", change: "+12% vs last period" },
    { title: "Total Optimizations", value: String(currentData.totalOptimizations), icon: TrendingUp, color: "text-orange-600", bgColor: "bg-orange-50", change: "+31% vs last period" }
  ];

  return (
    <section aria-labelledby="overview-heading" className="space-y-3 sm:space-y-4">
      {/* Header + period tabs: wrap gracefully on small screens */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="overview-heading" className="text-base sm:text-lg font-semibold text-foreground">
          Performance Overview
        </h2>
        <div className="flex gap-1 rounded-lg bg-muted p-1">
          {(["7d", "30d", "ytd"] as PeriodType[]).map((period) => (
            <Button
              key={period}
              variant={selectedPeriod === period ? "default" : "ghost"}
              size="sm"
              onClick={() => setSelectedPeriod(period)}
              className="px-2.5 sm:px-3 py-1 text-[11px] sm:text-xs"
            >
              {periodLabels[period]}
            </Button>
          ))}
        </div>
      </div>

      {/* Cards grid: 1 → 2 → 4 cols, tighter gaps on small screens */}
      <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-4 xl:gap-6">
        {metrics.map((metric, i) => (
          <Card key={i} className="h-full transition-shadow hover:shadow-md">
            <CardHeader className="p-4 sm:p-5 lg:p-6 pb-2 flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-[12px] sm:text-sm font-medium text-muted-foreground">
                {metric.title}
              </CardTitle>
              <span className={`rounded-full ${metric.bgColor} p-1.5 sm:p-2`}>
                <metric.icon className={`h-4 w-4 sm:h-5 sm:w-5 ${metric.color}`} />
              </span>
            </CardHeader>

            <CardContent className="p-4 sm:p-5 lg:p-6 pt-0">
              <div className="space-y-1">
                {/* Value scales with clamp; tabular-nums improves number alignment */}
                <div className="font-semibold leading-tight tabular-nums text-[clamp(1.125rem,1.5vw+0.8rem,1.75rem)]">
                  {metric.value}
                </div>
                <p className="text-[11px] sm:text-xs text-muted-foreground">{metric.change}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
};
