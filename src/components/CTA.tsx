import { Button } from "@/components/ui/button";
import { ArrowRight, Rocket, Mail } from "lucide-react";
import { useState } from "react";
import { SignUpDialog } from "@/components/dialogs/SignUpDialog";

export const CTA = () => {
  const [signUpOpen, setSignUpOpen] = useState(false);
  const [dialogTitle, setDialogTitle] = useState("");
  return (
    <section className="py-20 bg-gradient-primary relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-accent opacity-90" />
      <div className="absolute top-0 left-0 w-96 h-96 bg-white/10 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-2xl" />
      
      <div className="container px-4 mx-auto relative z-10">
        <div className="text-center max-w-4xl mx-auto animate-fade-in">
          <div className="inline-flex items-center px-4 py-2 bg-white/20 rounded-full text-sm font-medium text-white mb-6">
            <Rocket className="w-4 h-4 mr-2" />
            Ready to Transform Your AI Features?
          </div>
          
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6 leading-tight">
            Stop Flying Blind with
            <br />
            LLM Operations 
          </h2>
          
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Join forward-thinking teams who've eliminated AI latency, reduced costs by 45%, and transformed user trust in their AI features.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button 
              size="lg" 
              className="bg-white text-primary hover:bg-white/90 hover:scale-105 transition-all duration-300 shadow-xl"
              onClick={() => {
                setDialogTitle("Start Your Free Trial");
                setSignUpOpen(true);
              }}
            >
            Start Free Trial <ArrowRight className="ml-2 w-4 h-4" />
            </Button>

            <Button 
              size="lg" 
              className="bg-white text-primary hover:bg-white/90 hover:scale-105 transition-all duration-300 shadow-xl"
              onClick={() => {
                setDialogTitle("Book Your Demo");
                setSignUpOpen(true);
              }}
            >
            Book Demo <Mail className="mr-2 w-4 h-4" />
            </Button>
          </div>
          
          {/* Trust indicators */}
          <div className="flex flex-wrap justify-center items-center gap-8 text-white/80 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-success rounded-full" />
              <span>No setup fees</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-success rounded-full" />
              <span>30-day free trial</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-success rounded-full" />
              <span>Cancel anytime</span>
            </div>
          </div>
        </div>
        
        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-8 mt-16 text-center">
          <div className="animate-slide-up">
            <div className="text-3xl font-bold text-white mb-2">45%</div>
            <div className="text-white/80">Cost Reduction</div>
          </div>
          <div className="animate-slide-up" style={{animationDelay: '200ms'}}>
            <div className="text-3xl font-bold text-white mb-2">3x</div>
            <div className="text-white/80">Faster Responses</div>
          </div>
          <div className="animate-slide-up" style={{animationDelay: '400ms'}}>
            <div className="text-3xl font-bold text-white mb-2">99.9%</div>
            <div className="text-white/80">Uptime SLA</div>
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