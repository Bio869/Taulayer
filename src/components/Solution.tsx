import { CheckCircle, Zap, Target, Shield, TrendingUp, Bell, Users, Cpu } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const Solution = () => {
  const valueProps = [
    {
      icon: Zap,
      title: "Eliminate Latency",
      description: "Predict query execution time and prevent slow operations before they start",
      color: "text-primary",
      bg: "bg-primary/10"
    },
    {
      icon: Users,
      title: "Increase Engagement",
      description: "Smart suggestions and real-time updates keep users engaged during processing",
      color: "text-accent",
      bg: "bg-accent/10"
    },
    {
      icon: Target,
      title: "Smart Suggestions",
      description: "Automatically recommend query optimizations during peak hours or for complex requests",
      color: "text-success",
      bg: "bg-success/10"
    },
    {
      icon: Shield,
      title: "Reduce Costs",
      description: "Prevent expensive operations and optimize resource allocation automatically",
      color: "text-warning",
      bg: "bg-warning/10"
    },
    {
      icon: Bell,
      title: "Automate Reporting",
      description: "Schedule reports for users who don't want to wait or wish to reschedule data insights",
      color: "text-primary",
      bg: "bg-primary/10"
    },
    {
      icon: Cpu,
      title: "Resource Allocation",
      description: "Intelligent inference resource allocation with user priority management",
      color: "text-accent",
      bg: "bg-accent/10"
    }
  ];

  return (
    <section className="py-20 bg-gradient-secondary">
      <div className="container px-4 mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <div className="inline-flex items-center px-4 py-2 bg-success/10 rounded-full text-sm font-medium text-success mb-4">
            <CheckCircle className="w-4 h-4 mr-2" />
            Smart Solution
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
            Pre-Execution Intelligence & Real-Time Engagement
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
            A lightweight API layer that gives your LLM agents complete visibility and control over backend operations.
          </p>
          
          <div className="flex flex-wrap justify-center gap-4 mb-12">
            <Badge variant="secondary" className="px-4 py-2 text-sm">
              <TrendingUp className="w-4 h-4 mr-2" />
              85% Cost Reduction
            </Badge>
            <Badge variant="secondary" className="px-4 py-2 text-sm">
              <Zap className="w-4 h-4 mr-2" />
              3x Faster Responses
            </Badge>
            <Badge variant="secondary" className="px-4 py-2 text-sm">
              <Shield className="w-4 h-4 mr-2" />
              Zero Backend Overloads
            </Badge>
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {valueProps.map((prop, index) => (
            <Card key={index} className="p-6 border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-xl group animate-slide-up bg-background/50 backdrop-blur-sm" style={{animationDelay: `${index * 100}ms`}}>
              <div className={`w-12 h-12 ${prop.bg} rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                <prop.icon className={`w-6 h-6 ${prop.color}`} />
              </div>
              <h3 className="font-semibold text-foreground mb-3">{prop.title}</h3>
              <p className="text-sm text-muted-foreground">{prop.description}</p>
            </Card>
          ))}
        </div>

        <div className="bg-background/80 backdrop-blur-sm rounded-2xl p-8 border-2 border-primary/20 animate-glow">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-foreground mb-4">Complete Value Proposition</h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Transform your AI features from unpredictable cost centers into efficient, user-friendly experiences
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h4 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 text-success mr-2" />
                For Your Business
              </h4>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                  <span className="text-sm text-muted-foreground">Reduce compute and data access costs by up to 85%</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                  <span className="text-sm text-muted-foreground">Prevent backend overloads and system timeouts</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                  <span className="text-sm text-muted-foreground">Clear ROI on foundation model integration</span>
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold text-foreground mb-4 flex items-center">
                <Users className="w-5 h-5 text-primary mr-2" />
                For Your Users
              </h4>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                  <span className="text-sm text-muted-foreground">Faster, smarter, more scoped AI responses</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                  <span className="text-sm text-muted-foreground">Transparent latency expectations and progress</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-success mt-0.5" />
                  <span className="text-sm text-muted-foreground">Proactive guidance before costly mistakes happen</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};