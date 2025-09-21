// src/components/dashboard/DataTable.tsx
import { cn } from "@/lib/utils";
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
import { listRequests } from "@/lib/api";
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
  Bot,
} from "lucide-react";
import { DashboardFilters } from "@/pages/Dashboard";
import { SuggestionDrawer } from "./SuggestionDrawer";
import { useToast } from "@/hooks/use-toast";

console.log("DataTable build: NO_PLUS_BADGE");

export interface DataRow {
  user_id: string;
  prompt_request: string;
  submitted_prompt: string;
  model_name: string;
  timestamp: string;

  // Estimates shown pre-execution
  estimated_cpr_usd: number;
  estimated_latency_ms: number;

  // Suggestions shown in the table
  suggestions: Array<{
    text: string;
    estimated_new_cpr_usd: number;
    estimated_new_latency_ms: number;
    estimated_new_quality_pct: number;
    is_selected?: boolean;
  }>;

  // Savings & quality (from API/view joins)
  total_time_saved_ms: number;
  total_cost_saved_usd: number;
  prompt_quality_pct: number;

  // “Optimize for …” type
  suggestion_type: "latency" | "cost" | "clarification" | "none";

  // Row-level selection flags (optional, from API)
  has_selected_child?: boolean;
  selected_child_request_id?: string | null;
}

interface DataTableProps {
  filters: DashboardFilters;
  refreshKey: number;
}

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
    const load = async () => {
      setLoading(true);
      try {
        const sort = filters.sortBy[0] ?? {
          field: "timestamp",
          direction: "desc" as const,
        };

        // UI field -> API column
        const sortMap: Record<string, string> = {
          timestamp: "created_at",
          cpr: "predicted_tokens", // proxy
          latency: "predicted_latency",
          total_cost_saved_usd: "predicted_tokens", // proxy
          total_time_saved_ms: "predicted_latency", // proxy
        };

        const resp = await listRequests({
          userId: filters.userId || undefined,
          q: filters.searchPrompt || undefined,
          sortBy: sortMap[sort.field] ?? "created_at",
          sortDir: sort.direction,
          page: 1,
          pageSize: rowsPerPage,
        });

        const items: DataRow[] = (resp.items ?? []).map((r: any) => {
          // Map optimize_for → display type
          const opt: string | undefined = r.optimize_for;
          const suggestionType =
            (opt === "clarity" ? "clarification" : (opt ?? "none")) as
              | "latency"
              | "cost"
              | "clarification"
              | "none";

          // Compute pre-exec estimates
          const estTokens = Number(r.predicted_tokens ?? 0);
          const estLatency = Number(r.predicted_latency ?? 0);
          const estimated_cpr_usd = Math.max(0.01, estTokens * 0.000002);

          // Build suggestions (you can replace with real per-child rows later)
          const suggestions = (r.suggestions ?? []).map((s: string) => ({
            text: s,
            estimated_new_cpr_usd: Math.max(0.01, estTokens * 0.0000016),
            estimated_new_latency_ms: Math.max(1, estLatency * 0.7),
            estimated_new_quality_pct: 50,
            is_selected: false,
          })) as DataRow["suggestions"];

          // If the backend says a child was selected but we only have strings,
          // mark ONE suggestion heuristically as selected (fastest).
          if (r.selected_child_request_id && suggestions.length > 0) {
            let minIdx = 0;
            for (let i = 1; i < suggestions.length; i++) {
              if (
                suggestions[i].estimated_new_latency_ms <
                suggestions[minIdx].estimated_new_latency_ms
              ) {
                minIdx = i;
              }
            }
            suggestions[minIdx].is_selected = true;
          }

          // Savings and quality from API/view joins
          const timeSavedMs = Number(r.time_saved_ms ?? 0);
          const costSavedUsd = Number(r.cost_saved_usd ?? 0);

          // If backend provides row-level quality lift, use it;
          // otherwise derive a % from predicted_complexity in [0..1] → higher % = better
          const promptQualityPct =
            r.quality_lift_pct != null
              ? Number(r.quality_lift_pct)
              : r.predicted_complexity != null
              ? Math.max(
                  0,
                  Math.min(
                    100,
                    Math.round((1 - Number(r.predicted_complexity)) * 100)
                  )
                )
              : 50;

          return {
            user_id: r.user_id,
            prompt_request: r.prompt,
            submitted_prompt: r.prompt,
            model_name: r.model_name ?? "N/A",
            timestamp: r.created_at,

            estimated_cpr_usd,
            estimated_latency_ms: estLatency,

            suggestions,

            // ✅ single (non-duplicated) assignment of savings
            total_time_saved_ms: timeSavedMs,
            total_cost_saved_usd: costSavedUsd,

            // ✅ quality mapped from API or derived
            prompt_quality_pct: promptQualityPct,

            suggestion_type: suggestionType,

            // Optional row-level selection flags from API, used by UI highlighting
            has_selected_child: Boolean(
              r.has_selected_child || r.selected_child_request_id
            ),
            selected_child_request_id: r.selected_child_request_id ?? null,
          };
        });

        setData(items);
      } catch (e) {
        console.error(e);
        setData([]);
      } finally {
        setLoading(false);
        setCurrentPage(1);
      }
    };
    load();
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
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to clipboard",
      description: `${label} copied successfully`,
    });
  };

  const paginatedData = data.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  );

  const totalPages = Math.max(1, Math.ceil(data.length / rowsPerPage));

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
          <Table className="table-fixed w-full">
            <colgroup>
              <col className="w-[20ch]" /> {/* User ID */}
              <col className="w-[24ch]" /> {/* Prompt Requests */}
              <col className="w-[8ch]" /> {/* Quality */}
              <col className="w-[12ch]" /> {/* Model Name */}
              <col className="w-[14ch]" /> {/* Timestamp */}
              <col className="w-[10ch]" /> {/* Est. CPR */}
              <col className="w-[10ch]" /> {/* Est. Latency */}
              <col className="w-[16ch]" /> {/* Top Suggestions */}
              <col className="w-[10ch]" /> {/* New Cost */}
              <col className="w-[10ch]" /> {/* New Latency */}
              <col className="w-[10ch]" /> {/* New Quality */}
              <col className="w-[11ch]" /> {/* Time Saved */}
              <col className="w-[10ch]" /> {/* Cost Saved */}
            </colgroup>

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
                  <TableCell
                    colSpan={13}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No data yet. Try adjusting filters or refresh.
                  </TableCell>
                </TableRow>
              ) : (
                paginatedData.map((row, index) => {
                  const getSuggestionTooltip = (type: string) => {
                    switch (type) {
                      case "latency":
                        return "Optimize for speed";
                      case "cost":
                        return "Optimize for cost";
                      case "clarification":
                        return "Gain clarity";
                      case "none":
                      default:
                        return "View AI suggestions";
                    }
                  };

                  const getSuggestionIcon = () => <Bot className="h-4 w-4" />;

                  // Limit how many suggestions we show in the main table
                  const allSuggestions = Array.isArray(row.suggestions)
                    ? row.suggestions
                    : [];
                  const selectedIndex = allSuggestions.findIndex(
                    (s) => s.is_selected
                  );

                  // By default, show the first 3
                  let visibleSuggestions = allSuggestions.slice(0, 3);

                  // If the selected suggestion isn't in the first 3, include it
                  if (selectedIndex >= 3) {
                    visibleSuggestions = [
                      allSuggestions[selectedIndex],
                      ...allSuggestions.slice(0, 2),
                    ];
                  }

                  // Row-level selection state
                  const rowSelected = Boolean(
                    row.has_selected_child ||
                      row.selected_child_request_id ||
                      selectedIndex !== -1
                  );

                  return (
                    <TableRow
                      key={index}
                      className={rowSelected ? "bg-amber-50/40" : ""}
                    >
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <code className="text-sm bg-muted px-2 py-1 rounded">
                            {row.user_id.length > 14
                              ? row.user_id.slice(0, 14) + "..."
                              : row.user_id}
                          </code>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              copyToClipboard(row.user_id, "User ID")
                            }
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>

                      <TableCell className="overflow-hidden">
                        <div className="min-w-0 w-full flex items-center gap-2">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="flex-1 text-sm cursor-pointer whitespace-pre-wrap break-all">
                                {row.prompt_request.length > 26
                                  ? row.prompt_request.slice(0, 26) + "..."
                                  : row.prompt_request}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-[640px]">
                              <p className="whitespace-pre-wrap break-words">
                                {row.prompt_request}
                              </p>
                            </TooltipContent>
                          </Tooltip>

                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              copyToClipboard(row.prompt_request, "Prompt")
                            }
                            title="Copy full prompt"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>

                      <TableCell>
                        <Tooltip>
                          <TooltipTrigger>
                            <Badge variant="outline" className="font-mono">
                              {row.prompt_quality_pct}%
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            Prompt clarity/quality (0–100%)
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

                      <TableCell>
                        {formatLatency(row.estimated_latency_ms)}
                      </TableCell>

                      <TableCell>
                        <div className="flex items-center gap-2">
                          {/* Yellow “Selected” pill if any suggestion chosen */}
                          <span
                            className={cn(
                              "inline-flex items-center rounded px-1.5 py-0.5 text-[11px]",
                              rowSelected
                                ? "bg-amber-100 text-amber-800 ring-1 ring-amber-300"
                                : "bg-muted text-muted-foreground"
                            )}
                          >
                            {rowSelected ? "Selected" : "—"}
                          </span>

                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  setSelectedSuggestions({
                                    row,
                                    isOpen: true,
                                  })
                                }
                                aria-label={getSuggestionTooltip(
                                  row.suggestion_type
                                )}
                                className="flex items-center justify-center transition-colors cursor-pointer hover:bg-primary hover:text-primary-foreground"
                              >
                                {getSuggestionIcon()}
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>{getSuggestionTooltip(row.suggestion_type)}</p>
                            </TooltipContent>
                          </Tooltip>
                        </div>
                      </TableCell>

                      {/* New Cost – show only visibleSuggestions (+ optional +N more) */}
                      <TableCell>
                        <div className="space-y-1">
                          {visibleSuggestions.map((suggestion, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className={cn(
                                "text-xs",
                                suggestion.is_selected &&
                                  "bg-yellow-100 text-yellow-800 border-yellow-300"
                              )}
                            >
                              {formatCurrency(
                                suggestion.estimated_new_cpr_usd
                              )}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>

                      {/* New Latency – same 3-item slice */}
                      <TableCell>
                        <div className="space-y-1">
                          {visibleSuggestions.map((suggestion, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className={cn(
                                "text-xs",
                                suggestion.is_selected &&
                                  "bg-yellow-100 text-yellow-800 border-yellow-300"
                              )}
                            >
                              {formatLatency(
                                suggestion.estimated_new_latency_ms
                              )}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>

                      {/* New Quality – same 3-item slice */}
                      <TableCell>
                        <div className="space-y-1">
                          {visibleSuggestions.map((suggestion, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className={cn(
                                "text-xs",
                                suggestion.is_selected &&
                                  "bg-yellow-100 text-yellow-800 border-yellow-300"
                              )}
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
                            Original latency – selected latency
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>

                      <TableCell>
                        <Tooltip>
                          <TooltipTrigger>
                            {formatCurrency(row.total_cost_saved_usd)}
                          </TooltipTrigger>
                          <TooltipContent>
                            Original cost – selected cost
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
            Showing {(currentPage - 1) * rowsPerPage + 1} to{" "}
            {Math.min(currentPage * rowsPerPage, data.length)} of {data.length}{" "}
            results
          </p>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
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
              onClick={() =>
                setCurrentPage((prev) => Math.min(totalPages, prev + 1))
              }
              disabled={currentPage === totalPages}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {selectedSuggestions && (
          <SuggestionDrawer
            key={`${selectedSuggestions.row.user_id}-${selectedSuggestions.row.timestamp}`}
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
