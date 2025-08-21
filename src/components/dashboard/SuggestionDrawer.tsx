import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Copy, Play, TrendingDown, Clock } from "lucide-react";
import { DataRow } from "./DataTable";
import { useToast } from "@/hooks/use-toast";

interface SuggestionDrawerProps {
  row: DataRow;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const SuggestionDrawer = ({ 
  row, 
  open, 
  onOpenChange 
}: SuggestionDrawerProps) => {
  const { toast } = useToast();

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

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to clipboard",
      description: `${label} copied successfully`,
    });
  };

  const handleApplyAndRerun = (suggestion: typeof row.suggestions[0]) => {
    toast({
      title: "Apply & Re-run",
      description: "Applying optimized request and executing...",
    });
    
    // Mock the apply and re-run functionality
    setTimeout(() => {
      toast({
        title: "Request Optimized",
        description: "The optimized request has been applied and executed successfully.",
      });
    }, 2000);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[600px] sm:max-w-[600px]">
        <SheetHeader>
          <SheetTitle>Optimization Suggestions</SheetTitle>
          <SheetDescription>
            Review and apply AI-powered optimizations for your prompt request
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Original Request */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Original Request</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm bg-muted p-3 rounded-lg">
                  {row.prompt_request}
                </p>
                
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <span>Cost:</span>
                    <Badge variant="outline">
                      {formatCurrency(row.estimated_cpr_usd)}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1">
                    <span>Latency:</span>
                    <Badge variant="outline">
                      {formatLatency(row.estimated_latency_ms)}
                    </Badge>
                  </div>
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(row.prompt_request, "Original request")}
                  className="w-full"
                >
                  <Copy className="h-3 w-3 mr-2" />
                  Copy Original Request
                </Button>
              </div>
            </CardContent>
          </Card>

          <Separator />

          {/* Suggestions */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium">Optimized Suggestions</h3>
            
            {row.suggestions.map((suggestion, index) => {
              const costSavings = row.estimated_cpr_usd - suggestion.estimated_new_cpr_usd;
              const timeSavings = row.estimated_latency_ms - suggestion.estimated_new_latency_ms;
              const costSavingsPercent = (costSavings / row.estimated_cpr_usd) * 100;
              const timeSavingsPercent = (timeSavings / row.estimated_latency_ms) * 100;

              return (
                <Card key={index} className="border-l-4 border-l-primary">
                  <CardHeader>
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <span className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs">
                        {index + 1}
                      </span>
                      Suggestion {index + 1}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <p className="text-sm bg-accent p-3 rounded-lg">
                        {suggestion.text}
                      </p>
                      
                      {/* Metrics */}
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-xs">
                            <TrendingDown className="h-3 w-3 text-green-600" />
                            <span className="font-medium">Cost Savings</span>
                          </div>
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span>New cost:</span>
                              <Badge variant="secondary">
                                {formatCurrency(suggestion.estimated_new_cpr_usd)}
                              </Badge>
                            </div>
                            <div className="flex justify-between text-xs">
                              <span>Saved:</span>
                              <Badge variant="secondary" className="text-green-600">
                                {formatCurrency(Math.max(0, costSavings))} 
                                ({Math.max(0, costSavingsPercent).toFixed(1)}%)
                              </Badge>
                            </div>
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-xs">
                            <Clock className="h-3 w-3 text-blue-600" />
                            <span className="font-medium">Time Savings</span>
                          </div>
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span>New latency:</span>
                              <Badge variant="secondary">
                                {formatLatency(suggestion.estimated_new_latency_ms)}
                              </Badge>
                            </div>
                            <div className="flex justify-between text-xs">
                              <span>Saved:</span>
                              <Badge variant="secondary" className="text-blue-600">
                                {formatLatency(Math.max(0, timeSavings))} 
                                ({Math.max(0, timeSavingsPercent).toFixed(1)}%)
                              </Badge>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex gap-2 pt-2">
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleApplyAndRerun(suggestion)}
                          className="flex-1"
                        >
                          <Play className="h-3 w-3 mr-2" />
                          Apply & Re-run
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(suggestion.text, `Suggestion ${index + 1}`)}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Overall Summary */}
          <Card className="bg-accent/50">
            <CardHeader>
              <CardTitle className="text-sm font-medium">Best Optimization Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-medium text-green-600">Total Cost Saved</div>
                  <div className="text-lg font-bold">
                    {formatCurrency(row.total_cost_saved_usd)} 
                    <span className="text-sm font-normal text-muted-foreground">
                      ({row.pct_cost_saved.toFixed(1)}%)
                    </span>
                  </div>
                </div>
                <div>
                  <div className="font-medium text-blue-600">Total Time Saved</div>
                  <div className="text-lg font-bold">
                    {formatLatency(row.total_time_saved_ms)} 
                    <span className="text-sm font-normal text-muted-foreground">
                      ({row.pct_time_saved.toFixed(1)}%)
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </SheetContent>
    </Sheet>
  );
};