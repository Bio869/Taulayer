import { DataTable } from "@/components/dashboard/DataTable";
import { ControlPanel } from "@/components/dashboard/ControlPanel";
import { MetricsOverview } from "@/components/dashboard/MetricsOverview";
import { SettingsDialog } from "@/components/dashboard/SettingsDialog";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

export interface DashboardFilters {
  userId: string;
  searchPrompt: string;
  sortBy: Array<{
    field: string;
    direction: 'asc' | 'desc';
  }>;
}

const Dashboard = () => {
  const [filters, setFilters] = useState<DashboardFilters>({
    userId: "",
    searchPrompt: "",
    sortBy: [{ field: "timestamp", direction: "desc" }]
  });

  const [refreshKey, setRefreshKey] = useState(0);

  const handleFiltersChange = (newFilters: Partial<DashboardFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-3">
          {/* one-row header; prevent wrapping */}
          <div className="flex items-center gap-2 flex-nowrap min-w-0">
            {/* Title: no wrap, may truncate on very small widths */}
            <h1 className="font-bold leading-tight text-xl sm:text-2xl text-foreground
                          whitespace-nowrap truncate max-w-[46%]">
              τLayer Dashboard
            </h1>

            {/* Right side */}
            <div className="ml-auto flex items-center gap-2 sm:gap-3 shrink-0">
              {/* Company + email: allow truncation so row never wraps */}
              <div className="text-right leading-tight text-xs sm:text-sm
                              max-w-[42vw] sm:max-w-none overflow-hidden">
                <div className="font-medium text-foreground truncate">
                  Cybersecurity Corp
                </div>
                <div className="text-muted-foreground truncate">
                  john.doe@company.com
                </div>
              </div>

              <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                <SettingsDialog />
                <Button
                  variant="outline"
                  size="icon"
                  title="Log Out"
                  className="h-8 w-8 sm:h-9 sm:w-9"
                >
                  <LogOut className="h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      <div className="container mx-auto px-6 py-8 space-y-8">
        {/* Metrics Overview */}
        <MetricsOverview />
        
        <div className="flex items-start gap-8">
          {/* Main Content Area */}
          <div className="flex-1">
            <DataTable 
              filters={filters} 
              refreshKey={refreshKey}
            />
          </div>
          
          {/* Control Panel */}
          <div className="w-80">
            <ControlPanel 
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onRefresh={handleRefresh}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;