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
    direction: "asc" | "desc";
  }>;
}

const Dashboard = () => {
  const [filters, setFilters] = useState<DashboardFilters>({
    userId: "",
    searchPrompt: "",
    sortBy: [{ field: "timestamp", direction: "desc" }],
  });

  const [refreshKey, setRefreshKey] = useState(0);

  const handleFiltersChange = (newFilters: Partial<DashboardFilters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="max-w-screen-2xl mx-auto px-6 py-4">
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
        {/* Metrics — narrower than total: right padding equals sidebar (20rem) + gap (2rem) */}
        <div className="max-w-screen-2xl mx-auto xl:pr-[20rem]">
          <MetricsOverview />
        </div>

        {/* Main row: table + sidebar */}
        <div className="max-w-screen-2xl mx-auto flex flex-col xl:flex-row gap-8 items-start">
          {/* Table */}
          <div className="flex-1 min-w-0">
            <DataTable filters={filters} refreshKey={refreshKey} />
          </div>

          {/* Sidebar (fixed width on xl, full width on mobile) */}
          <aside className="w-full xl:w-72 xl:flex-shrink-0">
            <ControlPanel
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onRefresh={handleRefresh}
            />
          </aside>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
