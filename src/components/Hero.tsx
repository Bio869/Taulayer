import { Button } from "@/components/ui/button";
import { ArrowRight, Zap, Shield, TrendingUp } from "lucide-react";
import { useState } from "react";
import { SignUpDialog } from "@/components/dialogs/SignUpDialog";

export const Hero = () => {
  const [signUpOpen, setSignUpOpen] = useState(false);
  const [dialogTitle, setDialogTitle] = useState("");
  return (
    <section className="pt-24 md:pt-32 relative min-h-screen flex items-center justify-center bg-gradient-secondary overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/10" />
      <div className="absolute top-20 left-10 w-64 h-64 bg-primary/10 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-accent/10 rounded-full blur-3xl animate-pulse delay-1000" />
      
      <div className="container px-4 mx-auto relative z-10 pb-24 md:pb-0">
        <div className="grid lg:grid-cols-[1fr_1.2fr] gap-12 items-center">
          <div className="space-y-8 animate-fade-in">
            <div className="space-y-4">
              <div className="inline-flex items-center px-4 py-2 bg-primary/10 rounded-full text-sm font-medium text-primary">
                <Zap className="w-4 h-4 mr-2" />
                AI Workflows that Deliver More
              </div>
              <h1 className="text-4xl md:text-6xl font-bold text-foreground leading-tight">
                Pre-Execution AI Readiness That Cuts
                <span className="bg-gradient-primary bg-clip-text text-transparent"> Latency, Cost & Load</span>
                {/*<span className="bg-gradient-accent bg-clip-text text-transparent"> Satisfaction</span>*/}
              </h1>
              <p className="text-xl text-muted-foreground max-w-lg">
                Prompt- or backend-triggered requests often lead to high-cost, high-latency workloads—τLayer reveals and mitigates system load before execution.
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4">
              <Button 
                size="lg" 
                className="bg-gradient-primary hover:shadow-lg hover:scale-105 transition-all duration-300"
                onClick={() => {
                  setDialogTitle("Get Started with τLayer");
                  setSignUpOpen(true);
                }}
              >
                Get Started <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
               <Button 
                variant="outline" 
                size="lg" 
                className="border-primary/30 hover:border-primary"
                onClick={() => {
                  setDialogTitle("View Demo - Get Started");
                  setSignUpOpen(true);
                }}
              >
                View Demo
              </Button>
            </div>
            
            <div className="flex items-center gap-8 pt-8">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-success" />
                <span className="text-sm font-medium">45% Cost Reduction</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-success" />
                <span className="text-sm font-medium">3x Faster Responses</span>
              </div>
            </div>
          </div>
          
          <div className="relative animate-slide-up delay-300">
            <div className="relative z-10">
            <div
            className="relative w-full aspect-[16/9] transition-all duration-300 hover:shadow-[0_25px_35px_rgba(100,80,206,0.35)] rounded-2xl"
            style={{ filter: 'drop-shadow(0 10px 10px rgba(139, 92, 246, 1))' }}
            >
              <video 
                src="/lovable-uploads/Presentation1.mp4"
                autoPlay 
                loop 
                muted
                playsInline
                className="w-full h-full object-contain rounded-2xl shadow-2xl"
              />
            </div>
            </div>
            <div className="absolute inset-0 bg-gradient-primary rounded-2xl blur-2xl opacity-20 scale-110" />
          </div>
        </div>
      </div>
      <SignUpDialog 
        open={signUpOpen} 
        onOpenChange={setSignUpOpen} 
        title={dialogTitle}
      />
    </section>
  );
};
