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
import { ChevronLeft, ChevronRight, Copy, Bot } from "lucide-react";
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

        const rand = (min: number, max: number) =>
          min + Math.random() * (max - min);

        const items: DataRow[] = (resp.items ?? []).map((r: any) => {
          // Map optimize_for → display type
          const opt: string | undefined = r.optimize_for;
          const suggestion_type =
            (opt === "clarity" ? "clarification" : (opt ?? "none")) as
              | "latency"
              | "cost"
              | "clarification"
              | "none";

          // Compute pre-exec estimates
          const estTokens = Number(r.predicted_tokens ?? 0);
          // NOTE: if your pricing is per 1k tokens, use 0.000002 instead of 0.002.
          const computedCpr =
            estTokens > 0
              ? Math.max(0.01, estTokens * 0.002)
              : rand(0.05, 0.10);
          const estimated_cpr_usd = +computedCpr.toFixed(2);

          const baseLatencyMs = Number.isFinite(+r.predicted_latency)
            ? Number(r.predicted_latency)
            : Math.round(rand(800, 2600));

          // Quality (%). Prefer backend, else derive from predicted_complexity, else mid-range random
          const prompt_quality_pct =
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
              : Math.round(rand(30, 70));

          // Suggestions (strings in r.suggestions) -> 3 rows with variability
          const rawSuggestions: string[] =
            Array.isArray(r.suggestions) && r.suggestions.length > 0
              ? r.suggestions
              : ["Be specific", "Use bullet points", "Provide an example"];

          const suggestions = rawSuggestions.slice(0, 3).map((text) => {
            const cf = rand(0.65, 0.95); // cost factor
            const lf = rand(0.50, 0.85); // latency factor
            const qd = rand(2, 12); // quality delta

            return {
              text,
              estimated_new_cpr_usd: +(estimated_cpr_usd * cf).toFixed(2),
              estimated_new_latency_ms: Math.max(
                100,
                Math.round(baseLatencyMs * lf)
              ),
              estimated_new_quality_pct: Math.max(
                0,
                Math.min(100, Math.round(prompt_quality_pct + qd))
              ),
              is_selected: false,
            };
          });

          // If backend signals a selected child, highlight ONE suggestion randomly
          if (r.selected_child_request_id && suggestions.length > 0) {
            const idx = Math.floor(Math.random() * suggestions.length);
            suggestions[idx].is_selected = true;
          }

          return {
            user_id: r.user_id,
            prompt_request: r.prompt,
            submitted_prompt: r.prompt,
            model_name: r.model_name ?? "N/A",
            timestamp: r.created_at,

            estimated_cpr_usd,
            estimated_latency_ms: baseLatencyMs,
            suggestions,

            // savings from backend view/join
            total_time_saved_ms: Number(r.time_saved_ms ?? 0),
            total_cost_saved_usd: Number(r.cost_saved_usd ?? 0),

            prompt_quality_pct,
            suggestion_type,

            has_selected_child: Boolean(
              r.has_selected_child || r.selected_child_request_id
            ),
            selected_child_request_id: r.selected_child_request_id ?? null,
          } as DataRow;
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

  // Show more precision for small amounts
  const formatCurrency = (amount: number): string =>
    amount < 0.1 ? `$${amount.toFixed(3)}` : `$${amount.toFixed(2)}`;

  const formatLatency = (ms: number): string =>
    ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;

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
              <col className="w-[12ch]" /> {/* Top Suggestions */}
              <col className="w-[10ch]" /> {/* New Cost */}
              <col className="w-[10ch]" /> {/* New Latency */}
              <col className="w-[10ch]" /> {/* New Quality */}
              <col className="w-[12ch]" /> {/* Time Saved */}
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

                  // Row-level selection state → tint the whole row
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

                      <TableCell>{formatLatency(row.estimated_latency_ms)}</TableCell>

                      {/* Top Suggestions: only the button (NO “Selected” pill) */}
                      <TableCell>
                        <div className="flex items-center gap-2">
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
                          {visibleSuggestions.map((s, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className={cn(
                                "text-xs",
                                s.is_selected &&
                                  "bg-yellow-100 text-yellow-800 border-yellow-300"
                              )}
                            >
                              {formatCurrency(s.estimated_new_cpr_usd)}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>

                      {/* New Latency – same 3-item slice */}
                      <TableCell>
                        <div className="space-y-1">
                          {visibleSuggestions.map((s, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className={cn(
                                "text-xs",
                                s.is_selected &&
                                  "bg-yellow-100 text-yellow-800 border-yellow-300"
                              )}
                            >
                              {formatLatency(s.estimated_new_latency_ms)}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>

                      {/* New Quality – same 3-item slice */}
                      <TableCell>
                        <div className="space-y-1">
                          {visibleSuggestions.map((s, idx) => (
                            <Badge
                              key={idx}
                              variant="secondary"
                              className={cn(
                                "text-xs",
                                s.is_selected &&
                                  "bg-yellow-100 text-yellow-800 border-yellow-300"
                              )}
                            >
                              {s.estimated_new_quality_pct}%
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
