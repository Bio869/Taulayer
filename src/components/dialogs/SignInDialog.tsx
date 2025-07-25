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

const signInSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
});

type SignInFormData = z.infer<typeof signInSchema>;
type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

interface SignInDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const SignInDialog = ({ open, onOpenChange }: SignInDialogProps) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const { toast } = useToast();

  const form = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  const forgotPasswordForm = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = async (data: SignInFormData) => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast({
        title: "Sign In Submitted",
        description: "Your credentials have been submitted successfully.",
      });
      
      onOpenChange(false);
      form.reset();
    } catch (error) {
      toast({
        title: "Error",
        description: "Something went wrong. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const onForgotPasswordSubmit = async (data: ForgotPasswordFormData) => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast({
        title: "Password Reset Email Sent",
        description: `Password reset instructions have been sent to ${data.email}.`,
      });
      
      onOpenChange(false);
      setIsForgotPassword(false);
      forgotPasswordForm.reset();
    } catch (error) {
      toast({
        title: "Error",
        description: "Something went wrong. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = () => {
    setIsForgotPassword(true);
  };

  const handleBackToSignIn = () => {
    setIsForgotPassword(false);
  };

  return (
    <Dialog 
      open={open} 
      onOpenChange={(open) => {
        onOpenChange(open);
        if (!open) {
          setIsForgotPassword(false);
        }
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-center text-2xl font-bold">
            {isForgotPassword ? "Reset Your Password" : "Sign In to OptimizeAI"}
          </DialogTitle>
        </DialogHeader>
        
        {isForgotPassword ? (
          <Form {...forgotPasswordForm}>
            <form onSubmit={forgotPasswordForm.handleSubmit(onForgotPasswordSubmit)} className="space-y-6">
              <FormField
                control={forgotPasswordForm.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email Address</FormLabel>
                    <FormControl>
                      <Input type="email" placeholder="Enter your email address" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <div className="flex flex-col space-y-4">
                <Button type="submit" disabled={isLoading} className="w-full">
                  {isLoading ? "Sending..." : "Send Reset Instructions"}
                </Button>
                
                <Button
                  type="button"
                  variant="ghost"
                  onClick={handleBackToSignIn}
                  className="text-sm text-muted-foreground hover:text-foreground"
                >
                  Back to Sign In
                </Button>
              </div>
            </form>
          </Form>
        ) : (
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Username or Email</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter your username or email" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="Enter your password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <div className="flex flex-col space-y-4">
                <Button type="submit" disabled={isLoading} className="w-full">
                  {isLoading ? "Signing In..." : "Sign In"}
                </Button>
                
                <Button
                  type="button"
                  variant="ghost"
                  onClick={handleForgotPassword}
                  className="text-sm text-muted-foreground hover:text-foreground"
                >
                  Forgot your password?
                </Button>
              </div>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
};