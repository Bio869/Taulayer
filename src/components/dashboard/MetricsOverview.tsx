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

type PeriodType = '7d' | '30d' | 'ytd';

interface MetricsOverviewProps {
  data?: Record<PeriodType, MetricsData>;
}

export const MetricsOverview = ({ 
  data = {
    '7d': {
      totalTimeSaved: 12800000, // 3.56 hours
      totalCostSaved: 8.23,
      averageQualityLift: 12.1,
      totalOptimizations: 47
    },
    '30d': {
      totalTimeSaved: 45600000, // 12.67 hours
      totalCostSaved: 24.56,
      averageQualityLift: 18.3,
      totalOptimizations: 143
    },
    'ytd': {
      totalTimeSaved: 186400000, // 51.78 hours
      totalCostSaved: 142.89,
      averageQualityLift: 22.7,
      totalOptimizations: 687
    }
  }
}: MetricsOverviewProps) => {
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>('30d');
  
  const periodLabels: Record<PeriodType, string> = {
    '7d': 'Past 7 Days',
    '30d': 'Past 30 Days',
    'ytd': 'Year to Date'
  };

  const currentData = data[selectedPeriod];
  const formatTime = (ms: number): string => {
    const hours = Math.floor(ms / (1000 * 60 * 60));
    const minutes = Math.floor((ms % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatCurrency = (amount: number): string => {
    return `$${amount.toFixed(2)}`;
  };

  const metrics = [
    {
      title: "Total Time Saved",
      value: formatTime(currentData.totalTimeSaved),
      icon: Clock,
      color: "text-blue-600",
      bgColor: "bg-blue-50",
      change: "+23% vs last period"
    },
    {
      title: "Total Cost Saved",
      value: formatCurrency(currentData.totalCostSaved),
      icon: DollarSign,
      color: "text-green-600",
      bgColor: "bg-green-50",
      change: "+15% vs last period"
    },
    {
      title: "Average Quality Lift",
      value: `${currentData.averageQualityLift}%`,
      icon: Target,
      color: "text-purple-600",
      bgColor: "bg-purple-50",
      change: "+12% vs last period"
    },
    {
      title: "Total Optimizations",
      value: currentData.totalOptimizations.toString(),
      icon: TrendingUp,
      color: "text-orange-600",
      bgColor: "bg-orange-50",
      change: "+31% vs last period"
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Performance Overview</h2>
        <div className="flex gap-1 bg-muted p-1 rounded-lg">
          {(['7d', '30d', 'ytd'] as PeriodType[]).map((period) => (
            <Button
              key={period}
              variant={selectedPeriod === period ? "default" : "ghost"}
              size="sm"
              onClick={() => setSelectedPeriod(period)}
              className="text-xs px-3 py-1"
            >
              {periodLabels[period]}
            </Button>
          ))}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {metric.title}
              </CardTitle>
              <div className={`p-2 rounded-full ${metric.bgColor}`}>
                <metric.icon className={`h-4 w-4 ${metric.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                <div className="text-2xl font-bold text-foreground">
                  {metric.value}
                </div>
                <p className="text-xs text-muted-foreground">
                  {metric.change}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};