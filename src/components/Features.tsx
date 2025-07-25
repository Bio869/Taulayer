import { 
  Zap, 
  Shield, 
  TrendingUp, 
  Clock, 
  Users, 
  Database, 
  Settings, 
  Bell,
  Target,
  BarChart3
} from "lucide-react";
import { Card } from "@/components/ui/card";

export const Features = () => {
  const features = [
    {
      icon: Zap,
      title: "Real-Time Query Analysis",
      description: "Instant analysis of natural language queries with complexity scoring and resource prediction",
      gradient: "from-yellow-400 to-orange-500"
    },
    {
      icon: Shield,
      title: "Cost Protection",
      description: "Prevent expensive operations with intelligent cost estimation and automatic query optimization",
      gradient: "from-green-400 to-emerald-500"
    },
    {
      icon: Clock,
      title: "Latency Prediction",
      description: "Accurate execution time estimates based on query complexity, data size, and current system load",
      gradient: "from-blue-400 to-indigo-500"
    },
    {
      icon: Users,
      title: "Smart User Experience",
      description: "Keep users engaged with progress updates, wait-time UX, and smart scheduling options",
      gradient: "from-purple-400 to-pink-500"
    },
    {
      icon: Target,
      title: "Priority Management",
      description: "Intelligent user priority scoring with resource allocation based on subscription tiers",
      gradient: "from-violet-400 to-purple-500"
    },
    {
      icon: BarChart3,
      title: "Analytics & Insights",
      description: "Comprehensive insights into query patterns, cost savings, and performance improvements",
      gradient: "from-teal-400 to-cyan-500"
    }
  ];

  return (
    <section className="py-20 bg-gradient-secondary">
      <div className="container px-4 mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <div className="inline-flex items-center px-4 py-2 bg-primary/10 rounded-full text-sm font-medium text-primary mb-4">
            <Settings className="w-4 h-4 mr-2" />
            Platform Features
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
            Complete AI Optimization Suite
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Everything you need to transform your AI-powered features into efficient, cost-effective, and user-friendly experiences
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              className="p-6 border-2 hover:border-primary/50 transition-all duration-500 hover:shadow-xl group animate-slide-up bg-background/80 backdrop-blur-sm relative overflow-hidden"
              style={{animationDelay: `${index * 100}ms`}}
            >
              {/* Gradient background on hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500`} />
              
              <div className="relative z-10">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                
                <h3 className="font-semibold text-foreground mb-3 group-hover:text-primary transition-colors duration-300">
                  {feature.title}
                </h3>
                
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </Card>
          ))}
        </div>

        {/* Technical Highlights */}
        <div className="mt-16 bg-background/80 backdrop-blur-sm rounded-2xl p-8 border-2 border-primary/20">
          <h3 className="text-2xl font-bold text-foreground text-center mb-8">Technical Excellence</h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-primary" />
              </div>
              <h4 className="font-semibold text-foreground mb-2">&lt; 50ms Response</h4>
              <p className="text-sm text-muted-foreground">Lightning-fast API responses that don't slow down your workflow</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-success" />
              </div>
              <h4 className="font-semibold text-foreground mb-2">99.9% Uptime</h4>
              <p className="text-sm text-muted-foreground">Enterprise-grade reliability with global redundancy</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Database className="w-8 h-8 text-accent" />
              </div>
              <h4 className="font-semibold text-foreground mb-2">Zero Data Access</h4>
              <p className="text-sm text-muted-foreground">No PII or sensitive data passes through our systems</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};