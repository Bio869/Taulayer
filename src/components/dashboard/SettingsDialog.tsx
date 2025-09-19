// src/components/dashboard/SettingsDialog.tsx
import { useEffect, useState } from "react";
import { useIsMobile } from "@/hooks/use-mobile";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import {
  Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter,
} from "@/components/ui/sheet";
import {
  Tabs, TabsContent, TabsList, TabsTrigger,
} from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Settings } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { getClientProfile, updateClientSettings, updateClientBilling } from "@/lib/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

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

type OptimizeFor = "latency" | "cost" | "quality" | "clarity";
type Plan = "free" | "starter" | "professional" | "enterprise";

function SettingsBody({
  config, setConfig,
  optimizeFor, setOptimizeFor,
  billingEmail, setBillingEmail,
  plan, setPlan,
  monthlyQuota, setMonthlyQuota,
  monthlyUsage,
  nextBillingDate, setNextBillingDate,
  onSaveConfig, onLoadConfig, onSaveBilling,
}: {
  config: string;
  setConfig: (v: string) => void;

  optimizeFor: OptimizeFor;
  setOptimizeFor: (v: OptimizeFor) => void;

  billingEmail: string;
  setBillingEmail: (v: string) => void;

  plan: Plan;
  setPlan: (v: Plan) => void;

  monthlyQuota: number;
  setMonthlyQuota: (v: number) => void;

  monthlyUsage: number;

  nextBillingDate: string;
  setNextBillingDate: (v: string) => void;

  onSaveConfig: () => void;
  onLoadConfig: () => void;
  onSaveBilling: () => void;
}) {
  return (
    <Tabs defaultValue="user" className="w-full">
      {/* Mobile: horizontal scroll; Desktop: 3 fixed triggers */}
      <TabsList className="mb-6 w-full overflow-x-auto whitespace-nowrap flex sm:grid sm:grid-cols-3">
        <TabsTrigger className="flex-1 sm:flex-none" value="user">User &amp; Account</TabsTrigger>
        <TabsTrigger className="flex-1 sm:flex-none" value="billing">Billing</TabsTrigger>
        <TabsTrigger className="flex-1 sm:flex-none" value="config">Configuration</TabsTrigger>
      </TabsList>

      {/* User tab (placeholder profile fields) */}
      <TabsContent value="user" className="space-y-6 mt-0">
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input id="username" defaultValue="john.doe" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" defaultValue="john.doe@company.com" />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
          <Button>Save Changes</Button>
        </div>
      </TabsContent>

      {/* Billing tab */}
      <TabsContent value="billing" className="space-y-6 mt-0">
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="plan">Current Plan</Label>
              <Select value={plan} onValueChange={(v) => setPlan(v as Plan)}>
                <SelectTrigger id="plan">
                  <SelectValue placeholder="Select plan" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="free">Free</SelectItem>
                  <SelectItem value="starter">Starter</SelectItem>
                  <SelectItem value="professional">Professional</SelectItem>
                  <SelectItem value="enterprise">Enterprise</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="usage">Monthly Usage</Label>
              <Input
                id="usage"
                value={`${monthlyUsage.toLocaleString()} / ${monthlyQuota.toLocaleString()} requests`}
                disabled
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="billingEmail">Billing Email</Label>
              <Input
                id="billingEmail"
                type="email"
                value={billingEmail}
                onChange={(e) => setBillingEmail(e.target.value)}
                placeholder="billing@company.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="nextBilling">Next Billing Date</Label>
              <Input
                id="nextBilling"
                type="date"
                value={nextBillingDate}
                onChange={(e) => setNextBillingDate(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="monthlyQuota">Monthly Quota</Label>
              <Input
                id="monthlyQuota"
                type="number"
                min={0}
                value={monthlyQuota}
                onChange={(e) => setMonthlyQuota(Number(e.target.value || 0))}
              />
            </div>
            <div className="space-y-2">
              <Label>&nbsp;</Label>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1">Download Invoice</Button>
                <Button className="flex-1" onClick={onSaveBilling}>Save Billing</Button>
              </div>
            </div>
          </div>
        </div>
      </TabsContent>

      {/* Config tab */}
      <TabsContent value="config" className="space-y-6 mt-0">
        <div className="space-y-2">
          <Label htmlFor="config">Client Context Configuration (YAML)</Label>
          <div className="text-sm text-muted-foreground">
            Define context-aware fields, scope, relations, and relevant database fields for your organization.
          </div>
        </div>

        {/* Optimize For selector */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="optimizeFor">Optimize For</Label>
            <Select value={optimizeFor} onValueChange={(v) => setOptimizeFor(v as OptimizeFor)}>
              <SelectTrigger id="optimizeFor">
                <SelectValue placeholder="Select preference" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="latency">Latency (speed)</SelectItem>
                <SelectItem value="cost">Cost</SelectItem>
                <SelectItem value="quality">Quality</SelectItem>
                <SelectItem value="clarity">Clarity</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Textarea
          id="config"
          value={config}
          onChange={(e) => setConfig(e.target.value)}
          className="min-h-[50vh] sm:min-h-[400px] font-mono text-sm"
          placeholder="Enter your configuration in YAML format..."
        />

        <div className="flex justify-between flex-col sm:flex-row gap-2 pt-4">
          <Button variant="outline" onClick={onLoadConfig}>Load Saved</Button>
          <Button onClick={onSaveConfig}>Save Configuration</Button>
        </div>
      </TabsContent>
    </Tabs>
  );
}

export const SettingsDialog = () => {
  const [open, setOpen] = useState(false);

  // Config + preferences
  const [config, setConfig] = useState(defaultConfig);
  const [optimizeFor, setOptimizeFor] = useState<OptimizeFor>("latency");

  // Billing + usage
  const [billingEmail, setBillingEmail] = useState("");
  const [plan, setPlan] = useState<Plan>("free");
  const [monthlyQuota, setMonthlyQuota] = useState<number>(1000);
  const [monthlyUsage, setMonthlyUsage] = useState<number>(0);
  const [nextBillingDate, setNextBillingDate] = useState<string>("");

  const { toast } = useToast();
  const isMobile = useIsMobile();

  // Load from backend once dialog first opens (or on mount if you prefer)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const me = await getClientProfile();
        if (cancelled) return;
        setConfig(me?.settings?.config_yaml ?? defaultConfig);
        setOptimizeFor((me?.settings?.optimize_for ?? "latency") as OptimizeFor);

        setBillingEmail(me?.billing?.billing_email ?? "");
        setPlan((me?.billing?.plan ?? "free") as Plan);
        setMonthlyQuota(me?.billing?.monthly_quota ?? 1000);
        setMonthlyUsage(me?.usage?.requests_this_month ?? 0);
        setNextBillingDate(me?.billing?.next_billing_date ?? "");
      } catch (e: any) {
        toast({ title: "Failed to load settings", description: e?.message ?? "Unknown error", variant: "destructive" });
      }
    })();
    return () => { cancelled = true; };
  }, [toast]);

  const handleSaveConfig = async () => {
    try {
      await updateClientSettings({ config_yaml: config, optimize_for: optimizeFor });
      toast({ title: "Configuration Saved", description: "Your configuration has been saved successfully." });
    } catch (e: any) {
      toast({ title: "Save failed", description: e?.message ?? "Unknown error", variant: "destructive" });
    }
  };

  const handleLoadConfig = async () => {
    try {
      const me = await getClientProfile();
      setConfig(me?.settings?.config_yaml ?? defaultConfig);
      setOptimizeFor((me?.settings?.optimize_for ?? "latency") as OptimizeFor);
      toast({ title: "Configuration Loaded", description: "Your saved configuration has been loaded." });
    } catch (e: any) {
      toast({ title: "Load failed", description: e?.message ?? "Unknown error", variant: "destructive" });
    }
  };

  const handleSaveBilling = async () => {
    try {
      await updateClientBilling({
        billing_email: billingEmail,
        plan,
        monthly_quota: monthlyQuota,
        next_billing_date: nextBillingDate || undefined,
      });
      toast({ title: "Billing Saved", description: "Your billing details have been updated." });
    } catch (e: any) {
      toast({ title: "Save failed", description: e?.message ?? "Unknown error", variant: "destructive" });
    }
  };

  // Mobile → bottom sheet; Desktop → centered dialog
  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <Button variant="outline" size="icon" title="Settings">
            <Settings className="h-4 w-4" />
          </Button>
        </SheetTrigger>
        <SheetContent side="bottom" className="h-[90dvh] p-0">
          <div className="flex h-full flex-col">
            <SheetHeader className="px-5 py-4 border-b">
              <SheetTitle>Settings</SheetTitle>
              <SheetDescription>Account, billing, and client preferences</SheetDescription>
            </SheetHeader>
            <div className="flex-1 overflow-y-auto px-5 py-4">
              <SettingsBody
                config={config}
                setConfig={setConfig}
                optimizeFor={optimizeFor}
                setOptimizeFor={setOptimizeFor}
                billingEmail={billingEmail}
                setBillingEmail={setBillingEmail}
                plan={plan}
                setPlan={setPlan}
                monthlyQuota={monthlyQuota}
                setMonthlyQuota={setMonthlyQuota}
                monthlyUsage={monthlyUsage}
                nextBillingDate={nextBillingDate}
                setNextBillingDate={setNextBillingDate}
                onSaveConfig={handleSaveConfig}
                onLoadConfig={handleLoadConfig}
                onSaveBilling={handleSaveBilling}
              />
            </div>
            <SheetFooter className="px-5 py-3 border-t">
              <Button type="button" onClick={() => setOpen(false)}>Close</Button>
            </SheetFooter>
          </div>
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon" title="Settings">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent
        className="
          z-50 p-0 overflow-y-auto
          /* mobile: full-screen */
          inset-0 w-screen h-[100dvh] rounded-none translate-x-0 translate-y-0
          /* desktop+: centered & wider */
          sm:inset-auto sm:left-1/2 sm:top-1/2 sm:h-auto sm:rounded-xl
          sm:-translate-x-1/2 sm:-translate-y-1/2
          sm:!max-w-none sm:!w-[40rem] md:!w-[48rem] lg:!w-[56rem]
        "
      >
        <DialogHeader className="px-5 py-4 border-b">
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>
        <div className="px-5 py-4">
          <SettingsBody
            config={config}
            setConfig={setConfig}
            optimizeFor={optimizeFor}
            setOptimizeFor={setOptimizeFor}
            billingEmail={billingEmail}
            setBillingEmail={setBillingEmail}
            plan={plan}
            setPlan={setPlan}
            monthlyQuota={monthlyQuota}
            setMonthlyQuota={setMonthlyQuota}
            monthlyUsage={monthlyUsage}
            nextBillingDate={nextBillingDate}
            setNextBillingDate={setNextBillingDate}
            onSaveConfig={handleSaveConfig}
            onLoadConfig={handleLoadConfig}
            onSaveBilling={handleSaveBilling}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SettingsDialog;
