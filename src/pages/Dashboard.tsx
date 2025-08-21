import { DataTable } from "@/components/dashboard/DataTable";
import { ControlPanel } from "@/components/dashboard/ControlPanel";
import { useState } from "react";

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
          <h1 className="text-2xl font-bold text-foreground">τLayer Dashboard</h1>
        </div>
      </header>
      
      <div className="container mx-auto px-6 py-8">
        <div className="flex gap-8">
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