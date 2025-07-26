import { Code, ArrowRight, CheckCircle, HelpCircle, BrainCircuit} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const HowItWorks = () => {
  const apiEndpoints = [
  {
    name: "Predict API",
    method: "POST",
    endpoint: "/api/predict",
    description: "Analyze query before execution",
    code: `{
  "query": "Summarize churned users with high lifetime value",
  "user_id": "my2dog5is",
  "client_id": "acme_corp",
  "context": {
    "channel": "agentic AI",
    "urgency": "high",
    "file_attached": true,
    "file_metadata": {
      "type": "tabular",
      "size_mb": 8.3,
       "description": [
        "Tabular file with structured records and mixed data types",
        "High column count (40 fields)",
        "Estimated row volume 500K",
        "Multiple date/time fields"
      ]
    }
  }
}`
  },
  {
    name: "Response",
    method: "200",
    endpoint: "Success",
    description: "Intelligent guidance",
    code: `{
  "status": "query_optimization_available",
  "analysis": {
    "token_estimate": {
      "level": "high", "value": 12450
    },
    "latency": {
      "level": "medium", "predicted": "12s"
    },
    "execution_complexity": {
      "level": "medium",
      "reason": "2 joins","No filters applied", ...
    }
  },
  "suggestions": [
    "Apply date_range=<last_90_days> to reduce data scanned",
    "Limit SELECT fields to: churn_status, lifetime_value, date_joined",
    "Auto-schedule execution to 1:00am–4:00am off-peak window"
  ]
}`
  }
];

  const flowSteps = [
    {
      step: 1,
      icon: ArrowRight,
      title: "User Query",
      description: "User submits natural language request to LLM agent",
      status: "neutral"
    },
    {
      step: 2,
      icon: Code,
      title: "Pre-Analysis",
      description: "Our API analyzes query complexity and resource requirements",
      status: "processing"
    },
    {
      step: 3,
      icon: CheckCircle,
      title: "Smart Decision",
      description: "Return guidance: execute, optimize, or clarify",
      status: "success"
    },
    {
      step: 4,
      icon: ArrowRight,
      title: "Execution",
      description: "Proceed with optimized query or user engagement",
      status: "neutral"
    }
  ];

  return (
    <section className="py-20 bg-background">
      <div className="container px-4 mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <div className="inline-flex items-center px-4 py-2 bg-primary/10 rounded-full text-sm font-medium text-primary mb-4">
            <Code className="w-4 h-4 mr-2" />
            How It Works
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
            Simple API Integration
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Lightweight, stateless API calls that embed seamlessly into your existing workflows
          </p>
        </div>

        {/* Flow Diagram */}
        <div className="mb-16">
          <div className="grid md:grid-cols-4 gap-4 mb-12">
            {flowSteps.map((step, index) => (
              <div key={index} className="text-center animate-slide-up" style={{animationDelay: `${index * 200}ms`}}>
                <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center text-white font-bold text-lg
                  ${step.status === 'success' ? 'bg-success' : 
                    step.status === 'processing' ? 'bg-primary' : 'bg-muted-foreground'}`}>
                  {step.step}
                </div>
                <h3 className="font-semibold text-foreground mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* API Examples */}
        <div className="grid lg:grid-cols-2 gap-8 mb-16">
          {apiEndpoints.map((api, index) => (
            <Card key={index} className="p-6 animate-slide-up" style={{animationDelay: `${index * 300}ms`}}>
              <div className="flex items-center gap-3 mb-4">
                <Badge variant={api.method === 'POST' ? 'default' : 'secondary'} className="font-mono">
                  {api.method}
                </Badge>
                <span className="font-mono text-sm text-muted-foreground">{api.endpoint}</span>
              </div>
              <h3 className="font-semibold text-foreground mb-2">{api.name}</h3>
              <p className="text-sm text-muted-foreground mb-4">{api.description}</p>
              <div className="bg-muted/50 rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm font-mono text-foreground whitespace-pre-wrap">
                  {api.code}
                </pre>
              </div>
            </Card>
          ))}
        </div>

        {/* Response Types */}
        <div className="bg-gradient-secondary rounded-2xl p-8 border">
          <h3 className="text-2xl font-bold text-foreground text-center mb-8">Intelligent Response Types</h3>
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="p-6 text-center border-2 border-success/30 bg-success/5">
              <CheckCircle className="w-12 h-12 text-success mx-auto mb-4" />
              <h4 className="font-semibold text-foreground mb-2">🟢 Safe to Execute</h4>
              <p className="text-sm text-muted-foreground">Request is optimized and ready to run</p>
            </Card>
            
            <Card className="p-6 text-center border-2 border-warning/30 bg-warning/5">
              <BrainCircuit className="w-12 h-12 text-warning mx-auto mb-4" />
              <h4 className="font-semibold text-foreground mb-2">🧊 Smart Enhancer</h4>
              <p className="text-sm text-muted-foreground">Recommend limits, filters or scheduling</p>
            </Card>
            
            <Card className="p-6 text-center border-2 border-primary/30 bg-primary/5">
              <HelpCircle className="w-12 h-12 text-primary mx-auto mb-4" />
              <h4 className="font-semibold text-foreground mb-2">✔️ Clarify Intent</h4>
              <p className="text-sm text-muted-foreground">Help users and AI agents query efficiently</p>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};