import {
  Code,
  ArrowRight,
  CheckCircle,
  BrainCircuit,
  HelpCircle
} from "lucide-react";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious
} from "@/components/ui/carousel";

import { useState, useEffect } from "react";

export const HowItWorks = () => {
  const apiExamples = [
    {
      title: "Agent-Initiated Request",
      description: "Optimizing queries triggered by agent workflows",
      request: {
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
    "request_timestamp": "2025-11-20T08:30:00Z",
    "request_priority": "medium",
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
      response: {
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
    "Refine lifetime_value threshold threshold (e.g., >1000)"
    "Auto-schedule execution to 1:00am–4:00am off-peak window"
  ]
}`
      }
    },
    {
      title: "User Prompt Optimization",
      description: "Optimizing queries entered through UI workflows",
      request: {
        name: "Predict API",
        method: "POST",
        endpoint: "/api/predict",
        description: "AI agent query pre-analysis",
        code: `{
  "query": "Show all transactions flagged as suspicious",
  "user_id": "johndoe_123",
  "client_id": "fintrack_inc",
  "context": {
    "channel": "User Prompt",
    "request_timestamp": "2025-11-20T14:22:10Z",
    "request_priority": "high",
    "device_type": "desktop",
    "session_id": "sess_4932adc8",
    "file_attached": false,
    "file_metadata": {
      "type": null,
      "size_mb": 0,
      "description": []
  }
}`
      },
      response: {
        name: "Response",
        method: "200",
        endpoint: "Success",
        description: "Optimized execution plan",
        code: `{
  "status": "query_review_recommended",
  "analysis": {
    "token_estimate": { "level": "medium", "value": 7400 },
    "latency": { "level": "high", "predicted": "21s" },
    "execution_complexity": {
      "level": "high",
      "reason": "No filters, 3 joins, large dataset scanned."
    }
  },
  "suggestions": [
  "[Info] Query scope is broad —",
  "[Suggest] Limit to the last 30 days.",
  "[Suggest] Apply region filter: SF, US.",
  "[Suggest] Filter by unusual amount."
]
}`
      }
    }
  ];

  const flowSteps = [
    {
      step: 1,
      icon: ArrowRight,
      title: "Request Input (UI or Backend Trigger)",
      description: "A user or agent initiates a request from your app or workload",
      status: "neutral"
    },
    {
      step: 2,
      icon: Code,
      title: "Pre-Execution Evaluation (τLayer)",
      description: "Evaluated for complexity, latency, and cost —executes if viable, else returns guidance",
      status: "processing"
    },
    {
      step: 3,
      icon: CheckCircle,
      title: "Execution (Deployed in Your Stack)",
      description: "Runs on your AI stack, outside τLayer",
      status: "success"
    },
    {
      step: 4,
      icon: ArrowRight,
      title: " Post-Execution Feedback (τLayer)",
      description: "Execution metrics (latency, token usage, peak hours) are logged to improve prediction and guidance",
      status: "neutral"
    }
  ];

  const [currentSlide, setCurrentSlide] = useState(0);
  const [carouselApi, setCarouselApi] = useState<any>(null);

  useEffect(() => {
    if (!carouselApi) return;

    const interval = setInterval(() => {
      const nextSlide = (currentSlide + 1) % apiExamples.length;
      setCurrentSlide(nextSlide);
      carouselApi.scrollTo(nextSlide);
    }, 7000); // 7 seconds

    return () => clearInterval(interval);
  }, [currentSlide, carouselApi, apiExamples.length]);

  useEffect(() => {
    if (!carouselApi) return;
    carouselApi.on("select", () => setCurrentSlide(carouselApi.selectedScrollSnap()));
  }, [carouselApi]);

  return (
    <section className="py-20 bg-background">
      <div className="container px-4 mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <div className="inline-flex items-center px-4 py-2 bg-primary/10 rounded-full text-sm font-medium text-primary mb-4">
            <Code className="w-4 h-4 mr-2" />
            How It Works
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">Pre-Execution Request Orchestration & Optimization</h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            τLayer analyzes each request via a real-time POST API call (&lt;50ms)—evaluating complexity, latency, and cost before execution. If thresholds are met, it proceeds; if not, τLayer returns suggestions or clarification prompts. Execution metrics are logged to improve future predictions.
          </p>
        </div>

        {/* Flow Diagram */}
        <div className="mb-16">
          <div className="grid md:grid-cols-4 gap-4 mb-12">
            {flowSteps.map((step, index) => (
              <div key={index} className="text-center animate-slide-up" style={{ animationDelay: `${index * 200}ms` }}>
                <div
                  className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center text-white font-bold text-lg
                    ${step.status === 'success' ? 'bg-success' :
                    step.status === 'processing' ? 'bg-primary' : 'bg-muted-foreground'}`}
                >
                  {step.step}
                </div>
                <h3 className="font-semibold text-foreground mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* API Examples Carousel */}
        <div className="w-full px-4">
          <h3 className="text-2xl font-bold text-foreground text-center mb-8">API Workflow Scenarios (UI & Agent)</h3>
          <Carousel className="w-full" setApi={setCarouselApi} opts={{ watchDrag: false, dragFree: false }}>
            <CarouselContent>
              {apiExamples.map((example, index) => (
                <CarouselItem key={index} className="w-full">
                  <div className="w-full">
                    <div className="text-center mb-6">
                      <h4 className="text-lg font-semibold text-foreground mb-2">{example.title}</h4>
                      <p className="text-muted-foreground">{example.description}</p>
                    </div>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
                      {/* Request */}
                      <Card className="p-6 animate-slide-up w-full">
                        <div className="flex items-center gap-3 mb-4">
                          <Badge variant={example.request.method === 'POST' ? 'default' : 'secondary'} className="font-mono">
                            {example.request.method}
                          </Badge>
                          <span className="font-mono text-sm text-muted-foreground">{example.request.endpoint}</span>
                        </div>
                        <h5 className="font-semibold text-foreground mb-2">{example.request.name}</h5>
                        <p className="text-sm text-muted-foreground mb-4">{example.request.description}</p>
                        <div className="bg-muted/50 rounded-lg p-4 overflow-x-auto w-full">
                          <pre className="text-sm font-mono text-foreground whitespace-pre-wrap w-full">
                            {example.request.code}
                          </pre>
                        </div>
                      </Card>

                      {/* Response */}
                      <Card className="p-6 animate-slide-up w-full" style={{ animationDelay: '200ms' }}>
                        <div className="flex items-center gap-3 mb-4">
                          <Badge variant="secondary" className="font-mono">
                            {example.response.method}
                          </Badge>
                          <span className="font-mono text-sm text-muted-foreground">{example.response.endpoint}</span>
                        </div>
                        <h5 className="font-semibold text-foreground mb-2">{example.response.name}</h5>
                        <p className="text-sm text-muted-foreground mb-4">{example.response.description}</p>
                        <div className="bg-muted/50 rounded-lg p-4 overflow-x-auto w-full">
                          <pre className="text-sm font-mono text-foreground whitespace-pre-wrap w-full">
                            {example.response.code}
                          </pre>
                        </div>
                      </Card>
                    </div>
                    <div className="text-center mt-4">
                      <div className="text-sm text-muted-foreground">
                        {index + 1} of {apiExamples.length}
                      </div>
                    </div>
                  </div>
                </CarouselItem>
              ))}
            </CarouselContent>
            <CarouselPrevious className="left-4" />
            <CarouselNext className="right-4" />
          </Carousel>
        </div>

        {/* Response Types */}
        <div className="bg-gradient-secondary rounded-2xl p-8 border mt-16">
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
