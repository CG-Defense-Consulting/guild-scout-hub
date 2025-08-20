import { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  userRole: 'CGDC' | 'PARTNER' | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  // signUp: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [userRole, setUserRole] = useState<'CGDC' | 'PARTNER' | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUserRole = async (userId: string) => {
    try {
      const { data, error } = await supabase
        .from('user_page_entitlements')
        .select('page_index')
        .eq('user_id', userId)
        .single();

      if (error) {
        throw error;
      }

      if (data?.page_index) {
        // Parse "0,1,2,4" into [0, 1, 2, 4]
        const pageIndices = data.page_index.split(',').map(Number);
        
        // Map indices to page routes: 0=scouting, 1=tracker, 2=hub
        const accessiblePages = pageIndices.map(index => {
          switch (index) {
            case 0: return '/scouting';
            case 1: return '/tracker';
            case 2: return '/hub';
            default: return null;
          }
        }).filter(Boolean);
        
        // Determine role based on accessible pages
        if (accessiblePages.includes('/scouting') || accessiblePages.includes('/tracker')) {
          setUserRole('CGDC');
        } else if (accessiblePages.includes('/hub')) {
          setUserRole('PARTNER');
        }
      }
    } catch (error) {
      console.error('Error fetching user role:', error);
      setUserRole(null);
    }
  };

  useEffect(() => {
    // Set up auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        
        if (session?.user) {
          fetchUserRole(session.user.id);
        } else {
          setUserRole(null);
        }
        setLoading(false);
      }
    );

    // Check for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      
      if (session?.user) {
        fetchUserRole(session.user.id);
      }
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { error };
  };

  // const signUp = async (email: string, password: string) => {
  //   const redirectUrl = `${window.location.origin}/`;
  //   
  //   const { error } = await supabase.auth.signUp({
  //     email,
  //     password,
  //     options: {
  //       emailRedirectTo: redirectUrl
  //     }
  //   });
  //   return { error };
  // };

  const signOut = async () => {
    await supabase.auth.signOut();
    setUserRole(null);
  };

  const value: AuthContextType = {
    user,
    session,
    userRole,
    loading,
    signIn,
    // signUp,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};