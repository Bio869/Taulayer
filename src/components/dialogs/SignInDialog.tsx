// src/SignInDialog.tsx
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

import { supabase, getDashboardRedirect } from "@/supabaseClient";

// Email-only schema for magic link sign-in
const signInSchema = z.object({
  email: z.string().email("Please enter a valid email"),
});

type SignInFormData = z.infer<typeof signInSchema>;

interface SignInDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const SignInDialog = ({ open, onOpenChange }: SignInDialogProps) => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: "" },
    mode: "onSubmit",
  });

  const onSubmit = async ({ email }: SignInFormData) => {
    setIsLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: getDashboardRedirect() },
      });
      if (error) throw error;

      toast({
        title: "Magic link sent",
        description: "Check your inbox to finish signing in.",
      });

      // Close dialog and reset form after sending the link
      onOpenChange(false);
      form.reset();
    } catch (e: unknown) {
      const message =
        (e as { message?: string })?.message ?? "Something went wrong.";
      toast({
        title: "Sign-in failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        onOpenChange(isOpen);
        if (!isOpen) form.reset();
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-center text-2xl font-bold">
            Sign in to τLayer
          </DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="you@company.com"
                      autoComplete="email"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? "Sending link..." : "Send magic link"}
            </Button>

            {/* Optional helper text */}
            <p className="text-xs text-muted-foreground text-center">
              We’ll email you a secure, single-use sign-in link.
            </p>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};
