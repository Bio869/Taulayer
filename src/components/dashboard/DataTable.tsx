import { useState, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { 
  ChevronLeft, 
  ChevronRight, 
  Copy, 
  ExternalLink,
  MoreHorizontal,
  Bot
} from "lucide-react";
import { DashboardFilters } from "@/pages/Dashboard";
import { SuggestionDrawer } from "./SuggestionDrawer";
import { useToast } from "@/hooks/use-toast";

export interface DataRow {
  user_id: string;
  prompt_request: string;
  submitted_prompt: string;
  model_name: string;
  timestamp: string;
  estimated_cpr_usd: number;
  estimated_latency_ms: number;
  suggestions: Array<{
    text: string;
    estimated_new_cpr_usd: number;
    estimated_new_latency_ms: number;
    estimated_new_quality_pct: number;
    is_selected?: boolean;
  }>;
  total_time_saved_ms: number;
  total_cost_saved_usd: number;
  prompt_quality_pct: number;
  suggestion_type: 'latency' | 'cost' | 'clarification' | 'none';
}

interface DataTableProps {
  filters: DashboardFilters;
  refreshKey: number;
}

// Mock data generator
const generateMockData = (): DataRow[] => {
  const mockRows: DataRow[] = [];
  const userIds = ["usr_9a3f12", "usr_2b4c89", "usr_7d8e45", "usr_3f6g91"];
  const models = ["GPT-4o", "LLaMA 3", "Claude 3.5", "Gemini Pro"];
  const prompts = [
    "Summarize sprint tickets and flag blockers",
    "Generate API documentation for user endpoints", 
    "Analyze performance metrics from last week",
    "Create test cases for authentication module",
    "Review code changes in pull request #234",
    "Generate deployment checklist for production"
  ];
  const submittedPrompts = [
    "Please summarize all the sprint tickets from this week and identify any critical blockers that might affect our delivery timeline",
    "Can you help me generate comprehensive API documentation for all user-related endpoints including authentication and profile management?",
    "I need you to analyze our application performance metrics from the past week and highlight any concerning trends",
    "Please create a complete test suite for our authentication module covering happy paths and edge cases",
    "Review the code changes in pull request #234 and provide feedback on potential security issues and code quality",
    "Generate a detailed deployment checklist for our upcoming production release including all necessary verification steps"
  ];

  for (let i = 0; i < 50; i++) {
    const originalCost = 0.015 + Math.random() * 0.02;
    const originalLatency = 1500 + Math.random() * 2000;
    
    const suggestions = Array.from({ length: 3 }, (_, idx) => {
      const newCost = originalCost * (0.7 + Math.random() * 0.2);
      const newLatency = originalLatency * (0.6 + Math.random() * 0.3);
      const newQuality = Math.min(100, Math.max(0, Math.floor(Math.random() * 101) + 5)); // Slight improvement over original
      return {
        text: `Optimized version ${idx + 1}: ${prompts[Math.floor(Math.random() * prompts.length)]}`,
        estimated_new_cpr_usd: newCost,
        estimated_new_latency_ms: newLatency,
        estimated_new_quality_pct: newQuality,
        is_selected: false
      };
    });

    // Randomly decide if user selected an optimization (70% chance)
    const userOptimized = Math.random() < 0.7;
    let selectedSuggestion = null;
    let costSaved = 0;
    let timeSaved = 0;
    
    if (userOptimized) {
      const selectedIndex = Math.floor(Math.random() * suggestions.length);
      suggestions[selectedIndex].is_selected = true;
      selectedSuggestion = suggestions[selectedIndex];
      costSaved = Math.max(0, originalCost - selectedSuggestion.estimated_new_cpr_usd);
      timeSaved = Math.max(0, originalLatency - selectedSuggestion.estimated_new_latency_ms);
    }

    // Random quality percentage (0-100%)
    const promptQuality = Math.floor(Math.random() * 101);
    
    // Random suggestion type (or none if user didn't optimize)
    const suggestionTypes: ('latency' | 'cost' | 'clarification' | 'none')[] = ['latency', 'cost', 'clarification'];
    const suggestionType = userOptimized 
      ? suggestionTypes[Math.floor(Math.random() * suggestionTypes.length)]
      : 'none';

    mockRows.push({
      user_id: userIds[Math.floor(Math.random() * userIds.length)],
      prompt_request: prompts[Math.floor(Math.random() * prompts.length)],
      submitted_prompt: submittedPrompts[Math.floor(Math.random() * submittedPrompts.length)],
      model_name: models[Math.floor(Math.random() * models.length)],
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      estimated_cpr_usd: originalCost,
      estimated_latency_ms: originalLatency,
      suggestions,
      total_time_saved_ms: timeSaved,
      total_cost_saved_usd: costSaved,
      prompt_quality_pct: promptQuality,
      suggestion_type: suggestionType
    });
  }

  return mockRows;
};

export const DataTable = ({ filters, refreshKey }: DataTableProps) => {
  const [data, setData] = useState<DataRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedSuggestions, setSelectedSuggestions] = useState<{
    row: DataRow;
    isOpen: boolean;
  } | null>(null);
  const { toast } = useToast();
  
  const rowsPerPage = 25;

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      let mockData = generateMockData();
      
      // Apply filters
      if (filters.userId) {
        mockData = mockData.filter(row => 
          row.user_id.toLowerCase().includes(filters.userId.toLowerCase())
        );
      }
      
      if (filters.searchPrompt) {
        mockData = mockData.filter(row =>
          row.prompt_request.toLowerCase().includes(filters.searchPrompt.toLowerCase())
        );
      }
      
      // Apply sorting
      if (filters.sortBy.length > 0) {
        mockData.sort((a, b) => {
          for (const sort of filters.sortBy) {
            let aVal, bVal;
            switch (sort.field) {
              case 'timestamp':
                aVal = new Date(a.timestamp).getTime();
                bVal = new Date(b.timestamp).getTime();
                break;
              case 'cpr':
                aVal = a.estimated_cpr_usd;
                bVal = b.estimated_cpr_usd;
                break;
              case 'latency':
                aVal = a.estimated_latency_ms;
                bVal = b.estimated_latency_ms;
                break;
              case 'total_cost_saved_usd':
                aVal = a.total_cost_saved_usd;
                bVal = b.total_cost_saved_usd;
                break;
              case 'total_time_saved_ms':
                aVal = a.total_time_saved_ms;
                bVal = b.total_time_saved_ms;
                break;
              default:
                aVal = a[sort.field as keyof DataRow];
                bVal = b[sort.field as keyof DataRow];
            }
            
            if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1;
          }
          return 0;
        });
      }
      
      setData(mockData);
      setLoading(false);
      setCurrentPage(1);
    };

    loadData();
  }, [filters, refreshKey]);

  const formatCurrency = (amount: number): string => {
    if (amount < 0.01) {
      return `$${amount.toFixed(3)}`;
    }
    return `$${amount.toFixed(2)}`;
  };

  const formatLatency = (ms: number): string => {
    if (ms < 1000) {
      return `${Math.round(ms)} ms`;
    }
    return `${(ms / 1000).toFixed(1)} s`;
  };

  const formatTimestamp = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to clipboard",
      description: `${label} copied successfully`,
    });
  };

  const truncateText = (text: string, maxLength: number): string => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + "...";
  };

  const paginatedData = data.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  const totalPages = Math.ceil(data.length / rowsPerPage);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border bg-card">
          <div className="p-6">
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex space-x-4">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-40" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="space-y-4">
         <div className="rounded-lg border bg-card">
          <Table>
            <TableHeader>
            <TableRow>
              <TableHead>User ID</TableHead>
              <TableHead>Prompt Requests</TableHead>
              <TableHead>Quality</TableHead>
              <TableHead>Model Name</TableHead>
              <TableHead>Timestamp</TableHead>
              <TableHead>Est. CPR</TableHead>
              <TableHead>Est. Latency</TableHead>
              <TableHead>Top Suggestions</TableHead>
              <TableHead>New Cost</TableHead>
              <TableHead>New Latency</TableHead>
              <TableHead>New Quality</TableHead>
              <TableHead>Time Saved</TableHead>
              <TableHead>Cost Saved</TableHead>
            </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={13} className="text-center py-8 text-muted-foreground">
                    No data yet. Try adjusting filters or refresh.
                  </TableCell>
                </TableRow>
              ) : (
                paginatedData.map((row, index) => {
                  const getSuggestionTooltip = (type: string) => {
                    switch (type) {
                      case 'latency':
                        return 'Optimize for speed';
                      case 'cost':
                        return 'Optimize for cost';
                      case 'clarification':
                        return 'Gain clarity';
                      case 'none':
                        return 'View AI suggestions';
                      default:
                        return 'View AI suggestions';
                    }
                  };

                  const getSuggestionIcon = (type: string) => {
                    return <Bot className="h-4 w-4" />;
                  };

                  return (
                    <TableRow key={index}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <code className="text-sm bg-muted px-2 py-1 rounded">
                            {row.user_id}
                          </code>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(row.user_id, "User ID")}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-xs">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div className="cursor-pointer">
                              <p className="line-clamp-2 text-sm">
                                {row.prompt_request}
                              </p>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent className="max-w-md">
                            <p>{row.prompt_request}</p>
                          </TooltipContent>
                        </Tooltip>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(row.prompt_request, "Prompt")}
                          className="mt-1"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Tooltip>
                          <TooltipTrigger>
                            <Badge variant="outline" className="font-mono">
                              {row.prompt_quality_pct}%
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            Prompt clarity score (0-100%)
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono">
                          {row.model_name}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {formatTimestamp(row.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Tooltip>
                          <TooltipTrigger>
                            {formatCurrency(row.estimated_cpr_usd)}
                          </TooltipTrigger>
                          <TooltipContent>
                            Predicted pre-execution cost
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell>{formatLatency(row.estimated_latency_ms)}</TableCell>
                      <TableCell>
                        <Tooltip>
                          <TooltipTrigger asChild>
                      <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedSuggestions({
                                row,
                                isOpen: true
                              })}
                              className="flex items-center justify-center transition-colors cursor-pointer hover:bg-primary hover:text-primary-foreground"
                            >
                              {getSuggestionIcon(row.suggestion_type)}
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>{getSuggestionTooltip(row.suggestion_type)}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {row.suggestions.map((suggestion, idx) => (
                            <Badge 
                              key={idx} 
                              variant="secondary" 
                              className={`text-xs ${suggestion.is_selected ? 'bg-yellow-100 text-yellow-800 border-yellow-300' : ''}`}
                            >
                              {formatCurrency(suggestion.estimated_new_cpr_usd)}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {row.suggestions.map((suggestion, idx) => (
                            <Badge 
                              key={idx} 
                              variant="secondary" 
                              className={`text-xs ${suggestion.is_selected ? 'bg-yellow-100 text-yellow-800 border-yellow-300' : ''}`}
                            >
                              {formatLatency(suggestion.estimated_new_latency_ms)}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {row.suggestions.map((suggestion, idx) => (
                            <Badge 
                              key={idx} 
                              variant="secondary" 
                              className={`text-xs ${suggestion.is_selected ? 'bg-yellow-100 text-yellow-800 border-yellow-300' : ''}`}
                            >
                              {suggestion.estimated_new_quality_pct}%
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Tooltip>
                          <TooltipTrigger>
                            {formatLatency(row.total_time_saved_ms)}
                          </TooltipTrigger>
                          <TooltipContent>
                            Original latency - selected suggestion latency
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Tooltip>
                          <TooltipTrigger>
                            {formatCurrency(row.total_cost_saved_usd)}
                          </TooltipTrigger>
                          <TooltipContent>
                            Original cost - selected suggestion cost
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {((currentPage - 1) * rowsPerPage) + 1} to{' '}
            {Math.min(currentPage * rowsPerPage, data.length)} of {data.length} results
          </p>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            
            <span className="text-sm px-3 py-1 bg-muted rounded">
              Page {currentPage} of {totalPages}
            </span>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {selectedSuggestions && (
          <SuggestionDrawer
            row={selectedSuggestions.row}
            open={selectedSuggestions.isOpen}
            onOpenChange={(open) => 
              setSelectedSuggestions(open ? selectedSuggestions : null)
            }
          />
        )}
      </div>
    </TooltipProvider>
  );
};