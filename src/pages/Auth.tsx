import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
// import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';

export const Auth = () => {
  const { user, signIn, userRole, loading /* signUp */ } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  
  // Wait for both user authentication AND role loading to complete
  // This prevents the race condition where we redirect before userRole is loaded
  if (user && !loading && userRole) {
    // Redirect based on user role, not hardcoded
    if (userRole === 'CGDC') {
      return <Navigate to="/scouting" replace />;
    } else if (userRole === 'PARTNER') {
      return <Navigate to="/hub" replace />;
    }
  }

  // Show loading state while user is authenticated but role is still loading
  if (user && (loading || !userRole)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-guild-brand-bg p-4">
        <Card className="w-full max-w-md text-center">
          <CardHeader>
            <CardTitle className="text-xl">Loading Your Account</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground mb-4">
              Please wait while we load your permissions...
            </p>
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-guild-brand-fg"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleSignIn = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;

    const { error } = await signIn(email, password);
    
    if (error) {
      toast({
        title: 'Sign In Failed',
        description: error.message,
        variant: 'destructive',
      });
    } else {
      toast({
        title: 'Welcome back!',
        description: 'Successfully signed in.',
      });
    }
    
    setIsLoading(false);
  };

  // const handleSignUp = async (e: React.FormEvent<HTMLFormElement>) => {
  //   e.preventDefault();
  //   setIsLoading(true);
  //   
  //   const formData = new FormData(e.currentTarget);
  //   const email = formData.get('email') as string;
  //   const password = formData.get('password') as string;

  //   const { error } = await signUp(email, password);
  //   
  //   if (error) {
  //     toast({
  //       title: 'Sign Up Failed',
  //       description: error.message,
  //       variant: 'destructive',
  //     });
  //   } else {
  //     toast({
  //       title: 'Account created!',
  //       description: 'Please check your email to verify your account.',
  //     });
  //   }
  //   
  //   setIsLoading(false);
  // };

  return (
    <div className="min-h-screen flex items-center justify-center bg-guild-brand-bg p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center gap-3 mb-2">
            <img 
              src="/CGDC-logo.png" 
              alt="CGDC Logo" 
              className="h-10 w-auto"
            />
            <CardTitle className="text-2xl font-bold text-guild-brand-fg">GUILD</CardTitle>
          </div>
          <CardDescription>Defense contracting platform</CardDescription>
        </CardHeader>
        
        <CardContent>
          {/* <Tabs defaultValue="signin" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="signin">Sign In</TabsTrigger>
              <TabsTrigger value="signup">Sign Up</TabsTrigger>
            </TabsList>
            
            <TabsContent value="signin"> */}
              <form onSubmit={handleSignIn} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="signin-email">Email</Label>
                  <Input
                    id="signin-email"
                    name="email"
                    type="email"
                    placeholder="you@company.com"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="signin-password">Password</Label>
                  <Input
                    id="signin-password"
                    name="password"
                    type="password"
                    required
                  />
                </div>
                
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? 'Signing in...' : 'Sign In'}
                </Button>
              </form>
            {/* </TabsContent>
            
            <TabsContent value="signup">
              <form onSubmit={handleSignUp} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="signup-email">Email</Label>
                  <Input
                    id="signup-email"
                    name="email"
                    type="email"
                    placeholder="you@company.com"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="signup-password">Password</Label>
                  <Input
                    id="signup-password"
                    name="password"
                    type="password"
                    required
                  />
                </div>
                
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? 'Creating account...' : 'Sign Up'}
                </Button>
              </form>
            </TabsContent>
          </Tabs> */}
        </CardContent>
      </Card>
    </div>
  );
};

export default Auth;