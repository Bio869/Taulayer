import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Download, 
  RefreshCw, 
  Search, 
  Filter, 
  ArrowUpDown,
  X 
} from "lucide-react";
import { DashboardFilters } from "@/pages/Dashboard";
import { useToast } from "@/hooks/use-toast";

interface ControlPanelProps {
  filters: DashboardFilters;
  onFiltersChange: (filters: Partial<DashboardFilters>) => void;
  onRefresh: () => void;
}

const sortOptions = [
  { value: "timestamp", label: "Timestamp" },
  { value: "cpr", label: "Est. CPR" },
  { value: "latency", label: "Est. Latency" },
  { value: "total_cost_saved_usd", label: "Cost Saved" },
  { value: "total_time_saved_ms", label: "Time Saved" },
];

export const ControlPanel = ({ 
  filters, 
  onFiltersChange, 
  onRefresh 
}: ControlPanelProps) => {
  const [userIdInput, setUserIdInput] = useState(filters.userId);
  const [searchInput, setSearchInput] = useState(filters.searchPrompt);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const { toast } = useToast();

  const handleUserIdFilter = (value: string) => {
    setUserIdInput(value);
    // Debounce the filter application
    const timer = setTimeout(() => {
      onFiltersChange({ userId: value });
    }, 300);

    return () => clearTimeout(timer);
  };

  const handleSearchFilter = (value: string) => {
    setSearchInput(value);
    // Debounce the filter application
    const timer = setTimeout(() => {
      onFiltersChange({ searchPrompt: value });
    }, 300);

    return () => clearTimeout(timer);
  };

  const addSortField = (field: string, direction: 'asc' | 'desc' = 'desc') => {
    const existingIndex = filters.sortBy.findIndex(s => s.field === field);
    
    if (existingIndex >= 0) {
      // Update existing sort
      const newSortBy = [...filters.sortBy];
      newSortBy[existingIndex] = { field, direction };
      onFiltersChange({ sortBy: newSortBy });
    } else {
      // Add new sort
      onFiltersChange({ 
        sortBy: [...filters.sortBy, { field, direction }] 
      });
    }
  };

  const removeSortField = (field: string) => {
    onFiltersChange({ 
      sortBy: filters.sortBy.filter(s => s.field !== field) 
    });
  };

  const toggleSortDirection = (field: string) => {
    const newSortBy = filters.sortBy.map(s => 
      s.field === field 
        ? { ...s, direction: s.direction === 'asc' ? 'desc' as const : 'asc' as const }
        : s
    );
    onFiltersChange({ sortBy: newSortBy });
  };

  const handleExport = (format: 'csv' | 'json') => {
    // Get the filtered data from the parent component
    // For now, we'll create a mock dataset to export
    const mockData = {
      exportDate: new Date().toISOString(),
      filters: filters,
      data: [] // This would be the actual filtered data
    };

    if (format === 'csv') {
      // Convert to CSV format
      const csvContent = "data:text/csv;charset=utf-8," + 
        "User ID,Prompt Request,Model Name,Timestamp,Est. CPR,Est. Latency,Cost Saved,Time Saved\n" +
        "Sample data would go here...";
      
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `tlayer-export-${new Date().getTime()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      // Export as JSON
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(mockData, null, 2));
      const link = document.createElement("a");
      link.setAttribute("href", dataStr);
      link.setAttribute("download", `tlayer-export-${new Date().getTime()}.json`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    toast({
      title: "Export Complete",
      description: `Data exported successfully as ${format.toUpperCase()}`,
    });
  };

  const clearAllFilters = () => {
    setUserIdInput("");
    setSearchInput("");
    onFiltersChange({ 
      userId: "", 
      searchPrompt: "",
      sortBy: [{ field: "timestamp", direction: "desc" }]
    });
  };

  return (
    <div className="space-y-6">
      {/* Filter by User ID */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filter by User ID
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Input
              placeholder="Search user ID..."
              value={userIdInput}
              onChange={(e) => handleUserIdFilter(e.target.value)}
              className="text-sm"
            />
            <p className="text-xs text-muted-foreground">
              Supports exact match and prefix search
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Search Prompt Requests */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Search className="h-4 w-4" />
            Search Prompt Requests
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Input
              placeholder="Search prompts..."
              value={searchInput}
              onChange={(e) => handleSearchFilter(e.target.value)}
              className="text-sm"
            />
            <p className="text-xs text-muted-foreground">
              Full-text search across prompt requests
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Sort By */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <ArrowUpDown className="h-4 w-4" />
            Sort By
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Select onValueChange={(value) => addSortField(value)}>
              <SelectTrigger className="text-sm">
                <SelectValue placeholder="Add sort field..." />
              </SelectTrigger>
              <SelectContent>
                {sortOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <div className="space-y-2">
              {filters.sortBy.map((sort, index) => (
                <div key={`${sort.field}-${index}`} className="flex items-center gap-2">
                  <Badge 
                    variant="secondary" 
                    className="text-xs cursor-pointer"
                    onClick={() => toggleSortDirection(sort.field)}
                  >
                    {sortOptions.find(o => o.value === sort.field)?.label}
                    <span className="ml-1">
                      ({sort.direction === 'asc' ? '↑' : '↓'})
                    </span>
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeSortField(sort.field)}
                    className="h-6 w-6 p-0"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
            
            <p className="text-xs text-muted-foreground">
              Click badges to toggle asc/desc
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Export Data */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export Data
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => handleExport('csv')}
                className="flex-1"
              >
                CSV
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => handleExport('json')}
                className="flex-1"
              >
                JSON
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Exports current filtered data with suggestions
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Refresh Controls */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onRefresh}
              className="w-full"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Now
            </Button>
            
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="auto-refresh" 
                checked={autoRefresh}
                onCheckedChange={(checked) => setAutoRefresh(checked === true)}
              />
              <Label htmlFor="auto-refresh" className="text-xs">
                Auto-refresh every 30s
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Clear Filters */}
      <Button 
        variant="ghost" 
        size="sm" 
        onClick={clearAllFilters}
        className="w-full text-muted-foreground hover:text-foreground"
      >
        Clear All Filters
      </Button>
    </div>
  );
};