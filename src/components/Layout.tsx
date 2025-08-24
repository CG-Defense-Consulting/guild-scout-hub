import { Outlet, NavLink } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { LogOut, Search, BarChart3, Users, Menu, X, TrendingUp } from 'lucide-react';
import { useAuth } from '@/hooks/use-auth';
import { useState } from 'react';

export const Layout = () => {
  const { user, userRole, signOut } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSignOut = async () => {
    await signOut();
    // Navigation is handled by signOut function
  };

  // Navigation items based on user role
  const navigationItems = userRole === 'CGDC' ? [
    { title: 'Contract Scouting', url: '/scouting', icon: Search },
    { title: 'Contract Tracker', url: '/tracker', icon: BarChart3 },
    { title: 'Trends', url: '/trends', icon: TrendingUp },
    { title: 'Partner Hub', url: '/hub', icon: Users },
  ] : [
    { title: 'Partner Hub', url: '/hub', icon: Users },
  ];

  return (
    <div className="min-h-screen flex flex-col w-full">
      <header className="h-16 flex items-center justify-between px-4 md:px-6 border-b bg-guild-brand-bg">
        {/* Left side - Logo and Brand */}
        <div className="flex items-center gap-2 md:gap-4">
          <div className="flex items-center gap-2 md:gap-3">
            <img
              src="/CG-color.png"
              alt="CGDC Logo"
              className="h-8 md:h-10 w-auto"
            />
            <h1 className="text-base md:text-lg font-semibold text-guild-brand-fg">GUILD</h1>
          </div>
        </div>
        
        {/* Center - Navigation (Desktop) */}
        <nav className="hidden md:flex items-center gap-1">
          {navigationItems.map((item) => (
            <NavLink
              key={item.title}
              to={item.url}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-guild-accent-1/20 text-guild-accent-1'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              <span>{item.title}</span>
            </NavLink>
          ))}
        </nav>
        
        {/* Mobile Menu Button */}
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
        
        {/* Right side - User info and logout */}
        <div className="flex items-center gap-2 md:gap-3">
          <span className="hidden sm:block text-sm text-muted-foreground">{user?.email}</span>
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
      
      {/* Mobile Navigation Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b bg-guild-brand-bg">
          <nav className="flex flex-col p-4">
            {navigationItems.map((item) => (
              <NavLink
                key={item.title}
                to={item.url}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-guild-accent-1/20 text-guild-accent-1'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                  }`
                }
                onClick={() => setMobileMenuOpen(false)}
              >
                <item.icon className="h-4 w-4" />
                <span>{item.title}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      )}
      
      <main className="flex-1 p-4 md:p-6">
        <Outlet />
      </main>
    </div>
  );
};