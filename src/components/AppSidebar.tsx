import { NavLink, useLocation } from 'react-router-dom';
import { Search, BarChart3, Users, Shield } from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import { useAuth } from '@/hooks/use-auth';

const cgdcItems = [
  { title: 'Contract Scouting', url: '/scouting', icon: Search },
  { title: 'Contract Tracker', url: '/tracker', icon: BarChart3 },
  { title: 'Partner Hub', url: '/hub', icon: Users },
];

const partnerItems = [
  { title: 'Partner Hub', url: '/hub', icon: Users },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const { userRole } = useAuth();
  const location = useLocation();
  const currentPath = location.pathname;

  const items = userRole === 'CGDC' ? cgdcItems : partnerItems;
  const collapsed = state === 'collapsed';
  
  const isActive = (path: string) => currentPath === path;
  const getNavCls = ({ isActive }: { isActive: boolean }) =>
    isActive ? 'bg-guild-accent-1/20 text-guild-accent-1 font-medium' : 'hover:bg-muted/50';

  return (
    <Sidebar className={collapsed ? 'w-14' : 'w-60'}>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            {!collapsed && <span>Navigation</span>}
          </SidebarGroupLabel>
          
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink to={item.url} className={getNavCls}>
                      <item.icon className="mr-2 h-4 w-4" />
                      {!collapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}