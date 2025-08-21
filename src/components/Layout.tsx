import { Outlet, useNavigate } from 'react-router-dom';
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/AppSidebar';
import { Button } from '@/components/ui/button';
import { LogOut, Shield } from 'lucide-react';
import { useAuth } from '@/hooks/use-auth';

export const Layout = () => {
  const { user, userRole, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await signOut();
    navigate('/auth');
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col">
          <header className="h-14 flex items-center justify-between px-4 border-b bg-guild-brand-bg">
            <div className="flex items-center gap-3">
              <SidebarTrigger />
              <div className="flex items-center gap-2">
                <img 
                  src="/CGDC-logo.png" 
                  alt="CGDC Logo" 
                  className="h-8 w-auto"
                />
                <h1 className="text-lg font-semibold text-guild-brand-fg">GUILD</h1>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {userRole && (
                <div className="flex items-center gap-1 px-2 py-1 rounded-md bg-guild-accent-1/10">
                  <Shield className="w-3 h-3" />
                  <span className="text-xs font-medium">{userRole}</span>
                </div>
              )}
              <span className="text-sm text-muted-foreground">{user?.email}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSignOut}
                className="text-muted-foreground hover:text-foreground"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </header>
          
          <main className="flex-1">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};