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
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-foreground">τLayer Dashboard</h1>
            
            <div className="flex items-center gap-4">
              <div className="text-right text-sm">
                <div className="font-medium text-foreground">Cybersecurity Corp</div>
                <div className="text-muted-foreground">john.doe@company.com</div>
              </div>
              
              <div className="flex items-center gap-2">
                <SettingsDialog />
                <Button variant="outline" size="icon" title="Log Out">
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>
      
      <div className="w-full px-6 py-8 space-y-8">
        {/* Metrics Overview - slightly wider */}
        <div className="max-w-[1600px] mx-auto">
          <MetricsOverview />
        </div>

        {/* Table + Control Panel - capped for readability */}
        <div className="max-w-7xl mx-auto flex gap-8">
          <div className="flex-1">
            <DataTable filters={filters} refreshKey={refreshKey} />
          </div>

          <div className="w-80">
            <ControlPanel
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onRefresh={handleRefresh}
            />
          </div>
        </div>
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