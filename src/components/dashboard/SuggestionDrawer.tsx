import React from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Copy, TrendingDown, Clock, MessageCircle, Gauge } from "lucide-react";
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

  const getOptimizationType = (suggestion: typeof row.suggestions[0], costSavings: number, timeSavings: number) => {
    // Determine optimization type based on suggestion content and savings
    if (suggestion.text.toLowerCase().includes('clarify') || suggestion.text.toLowerCase().includes('clear') || suggestion.text.toLowerCase().includes('specify')) {
      return { type: 'clarity', label: 'Gain more clarity', icon: MessageCircle, color: 'text-purple-600' };
    }
    if (timeSavings > costSavings * 1000) {
      return { type: 'speed', label: 'Reduce latency', icon: Gauge, color: 'text-blue-600' };
    }
    if (costSavings > 0) {
      return { type: 'cost', label: 'Reduce cost', icon: TrendingDown, color: 'text-green-600' };
    }
    return { type: 'quality', label: 'Improve quality', icon: Clock, color: 'text-orange-600' };
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

        <ScrollArea className="h-[calc(100vh-100px)] mt-6">
          <div className="space-y-6 pr-4">
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
                    <div className="flex items-center gap-1">
                      <span>Quality:</span>
                      <Badge variant="outline">
                        {row.prompt_quality_pct}%
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
                const optimizationType = getOptimizationType(suggestion, costSavings, timeSavings);

                return (
                  <Card 
                    key={index} 
                    className={`border-l-4 ${
                      suggestion.is_selected 
                        ? 'border-l-yellow-500 bg-yellow-50/50' 
                        : 'border-l-primary'
                    }`}
                  >
                    <CardHeader>
                      <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <span className={`rounded-full w-6 h-6 flex items-center justify-center text-xs ${
                          suggestion.is_selected
                            ? 'bg-yellow-500 text-yellow-50'
                            : 'bg-primary text-primary-foreground'
                        }`}>
                          {index + 1}
                        </span>
                        Suggestion {index + 1}
                        <Badge variant="outline" className={`${optimizationType.color} border-current`}>
                          {React.createElement(optimizationType.icon, { className: "h-3 w-3 mr-1" })}
                          {optimizationType.label}
                        </Badge>
                        {suggestion.is_selected && (
                          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-300">
                            Selected
                          </Badge>
                        )}
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
                          
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-xs">
                              <MessageCircle className="h-3 w-3 text-purple-600" />
                              <span className="font-medium">Quality Score</span>
                            </div>
                            <div className="space-y-1">
                              <div className="flex justify-between text-xs">
                                <span>New quality:</span>
                                <Badge variant="secondary">
                                  {suggestion.estimated_new_quality_pct}%
                                </Badge>
                              </div>
                              <div className="flex justify-between text-xs">
                                <span>Change:</span>
                                <Badge variant="secondary" className={`${
                                  suggestion.estimated_new_quality_pct > row.prompt_quality_pct 
                                    ? 'text-green-600' 
                                    : suggestion.estimated_new_quality_pct < row.prompt_quality_pct 
                                    ? 'text-red-600' 
                                    : 'text-gray-600'
                                }`}>
                                  {suggestion.estimated_new_quality_pct > row.prompt_quality_pct ? '+' : ''}
                                  {(suggestion.estimated_new_quality_pct - row.prompt_quality_pct).toFixed(1)}%
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        {/* Actions */}
                        <div className="flex justify-end pt-2">
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

          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
};