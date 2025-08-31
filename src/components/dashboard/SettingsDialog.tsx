import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Settings } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const defaultConfig = `dataset: "SOC Events"
description: "Context for Security Operations Center events — used only for suggestions."

facets:
  region:
    values:
      - US West
      - US East
      - EU Central
      - EU West
      - Asia Pacific
    synonyms:
      US West: [us-west, us-west-1, us_west]
      US East: [us-east, us-east-1, us_east]
      EU Central: [eu-central, eu_central, eu-central-1]
      EU West: [eu-west, eu_west, eu-west-1]
      Asia Pacific: [apac, asia-pacific, ap-southeast-1]

  event_type:
    values:
      - Login Failed
      - Suspicious Login
      - Unauthorized Access
      - Privilege Escalation
      - Malware Detected
      - Phishing Attempt
      - Data Exfiltration
      - DDoS Attack
      - Policy Violation
      - Configuration Change
      - Insider Threat
      - Other
    synonyms:
      Login Failed: [login_failed, auth failure, authentication failure]
      Malware Detected: [malware, virus, trojan]
      Privilege Escalation: [priv_escalation, elevated rights]

  severity:
    values:
      - Low
      - Medium
      - High
      - Critical
      - Other
    synonyms:
      Low: [minor]
      Medium: [moderate]
      High: [severe]
      Critical: [crit, p1]
      Other: [unknown]

  alert_category:
    values:
      - Authentication
      - Network
      - Endpoint
      - Cloud
      - Application`;

export const SettingsDialog = () => {
  const [open, setOpen] = useState(false);
  const [config, setConfig] = useState(defaultConfig);
  const { toast } = useToast();

  const handleSaveConfig = () => {
    // Store config in localStorage for now
    localStorage.setItem("client-config", config);
    toast({
      title: "Configuration Saved",
      description: "Your configuration has been saved successfully.",
    });
  };

  const handleLoadConfig = () => {
    const savedConfig = localStorage.getItem("client-config");
    if (savedConfig) {
      setConfig(savedConfig);
      toast({
        title: "Configuration Loaded",
        description: "Your saved configuration has been loaded.",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>
        
        <Tabs defaultValue="user" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="user">User & Account</TabsTrigger>
            <TabsTrigger value="billing">Billing</TabsTrigger>
            <TabsTrigger value="config">Configuration</TabsTrigger>
          </TabsList>
          
          <TabsContent value="user" className="space-y-6 mt-0">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input id="username" defaultValue="john.doe" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" defaultValue="john.doe@company.com" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input id="firstName" defaultValue="John" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input id="lastName" defaultValue="Doe" />
                </div>
              </div>
            </div>
            <div className="flex justify-end pt-4">
              <Button onClick={() => toast({ title: "Profile Updated", description: "Your profile has been updated." })}>
                Save Changes
              </Button>
            </div>
          </TabsContent>
          
          <TabsContent value="billing" className="space-y-6 mt-0">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="plan">Current Plan</Label>
                  <Input id="plan" value="Professional" disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="usage">Monthly Usage</Label>
                  <Input id="usage" value="2,450 / 5,000 requests" disabled />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="billingEmail">Billing Email</Label>
                  <Input id="billingEmail" type="email" defaultValue="billing@company.com" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="nextBilling">Next Billing Date</Label>
                  <Input id="nextBilling" value="2024-09-15" disabled />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline">Download Invoice</Button>
              <Button>Upgrade Plan</Button>
            </div>
          </TabsContent>
          
          <TabsContent value="config" className="space-y-6 mt-0">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="config">Client Context Configuration (YAML)</Label>
                <div className="text-sm text-muted-foreground">
                  Define context-aware fields, scope, relations, and relevant database fields for your organization.
                </div>
              </div>
              <Textarea
                id="config"
                value={config}
                onChange={(e) => setConfig(e.target.value)}
                className="min-h-[400px] font-mono text-sm"
                placeholder="Enter your configuration in YAML format..."
              />
            </div>
            <div className="flex justify-between pt-4">
              <Button variant="outline" onClick={handleLoadConfig}>
                Load Saved
              </Button>
              <Button onClick={handleSaveConfig}>
                Save Configuration
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};