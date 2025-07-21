import { AlertTriangle, Clock, DollarSign, Users, Database, Cpu } from "lucide-react";
import { Card } from "@/components/ui/card";

export const Problem = () => {
  const problems = [
    {
      icon: Clock,
      title: "Zero Latency Awareness",
      description: "LLM agents generate queries without knowing if they'll take 300ms or 15 seconds",
      color: "text-warning"
    },
    {
      icon: DollarSign,
      title: "No Cost Estimation",
      description: "No visibility into API costs, compute time, or database load before execution",
      color: "text-destructive"
    },
    {
      icon: Database,
      title: "Backend Overloads",
      description: "Runaway queries risk overwhelming your infrastructure during peak hours",
      color: "text-warning"
    },
    {
      icon: Users,
      title: "Poor User Experience",
      description: "Long wait times and unclear progress lead to user frustration and mistrust",
      color: "text-destructive"
    }
  ];

  return (
    <section className="py-20 bg-background">
      <div className="container px-4 mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
            LLMs Blind to Task Complexity and Infra Limits—<br />Latency and Costs Spike
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Modern SaaS platforms embed LLM agents to drive user interactions—but these agents execute backend workflows with zero awareness of infrastructure cost, latency, or user impact.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {problems.map((problem, index) => (
            <Card key={index} className="p-6 border-2 border-red-100 hover:border-red-300 transition-all duration-300 hover:shadow-lg hover:shadow-red-100 group animate-slide-up bg-red-50/30" style={{animationDelay: `${index * 100}ms`}}>
              <problem.icon className={`w-8 h-8 ${problem.color} mb-4 group-hover:scale-110 transition-transform duration-300`} />
              <h3 className="font-semibold text-foreground mb-2">{problem.title}</h3>
              <p className="text-sm text-muted-foreground">{problem.description}</p>
            </Card>
          ))}
        </div>

        <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-2xl p-8 border border-red-100">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <Cpu className="w-12 h-12 text-red-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-foreground mb-2">High Infrastructure Costs</h3>
              <p className="text-muted-foreground">Unbounded queries consume excessive resources</p>
            </div>
            <div>
              <Clock className="w-12 h-12 text-orange-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-foreground mb-2">Unpredictable Performance</h3>
              <p className="text-muted-foreground">Users face inconsistent response times</p>
            </div>
            <div>
              <Users className="w-12 h-12 text-red-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-foreground mb-2">Lost User Trust</h3>
              <p className="text-muted-foreground">Poor AI experience damages product credibility</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};