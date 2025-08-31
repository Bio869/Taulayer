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
      {/* Header */}
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

      {/* Main */}
      <div className="w-full px-6 py-8 space-y-8">
        <div className="max-w-screen-2xl mx-auto space-y-8">
          {/* Metrics:
              On xl+, use a 2-col grid [main 1fr | sidebar 18rem] and place metrics in col 1.
              On smaller screens, grid isn't applied → metrics are full width (no odd right gap). */}
          <div className="xl:grid xl:grid-cols-[minmax(0,1fr)_18rem] xl:gap-8">
            <section className="xl:col-span-1">
              <MetricsOverview />
            </section>
            {/* placeholder column to match sidebar width on xl+ */}
            <div className="hidden xl:block" />
          </div>

          {/* Table + Filters laid out with the same grid so widths align perfectly */}
          <div className="xl:grid xl:grid-cols-[minmax(0,1fr)_18rem] xl:gap-8 items-start">
            <section className="min-w-0 xl:col-span-1">
              <DataTable filters={filters} refreshKey={refreshKey} />
            </section>

            <aside className="mt-8 xl:mt-0 xl:col-span-1">
              {/* fill the 18rem sidebar column on xl+, full width on mobile */}
              <div className="w-full">
                <ControlPanel
                  filters={filters}
                  onFiltersChange={handleFiltersChange}
                  onRefresh={handleRefresh}
                />
              </div>
            </aside>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
