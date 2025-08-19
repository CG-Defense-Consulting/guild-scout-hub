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
      console.log('=== fetchUserRole Debug ===');
      console.log('Fetching user role for userId:', userId);
      console.log('User ID type:', typeof userId);
      console.log('User ID length:', userId.length);
      
      const { data, error } = await supabase
        .from('user_page_entitlements')
        .select('page_index')
        .eq('user_id', userId)
        .single();

      if (error) {
        console.error('Supabase query error:', error);
        console.error('Error details:', {
          message: error.message,
          details: error.details,
          hint: error.hint,
          code: error.code
        });
        throw error;
      }

      console.log('Query result:', data);
      console.log('Data type:', typeof data);
      console.log('Data keys:', data ? Object.keys(data) : 'null');

      if (data?.page_index) {
        console.log('Page index value:', data.page_index);
        console.log('Page index type:', typeof data.page_index);
        
        // Parse "0,1,2,4" into [0, 1, 2, 4]
        const pageIndices = data.page_index.split(',').map(Number);
        console.log('Parsed page indices:', pageIndices);
        
        // Map indices to page routes: 0=scouting, 1=tracker, 2=hub
        const accessiblePages = pageIndices.map(index => {
          switch (index) {
            case 0: return '/scouting';
            case 1: return '/tracker';
            case 2: return '/hub';
            default: return null;
          }
        }).filter(Boolean);
        
        console.log('Accessible pages:', accessiblePages);
        
        // Determine role based on accessible pages
        if (accessiblePages.includes('/scouting') || accessiblePages.includes('/tracker')) {
          console.log('Setting user role to: CGDC');
          setUserRole('CGDC');
        } else if (accessiblePages.includes('/hub')) {
          console.log('Setting user role to: PARTNER');
          setUserRole('PARTNER');
        } else {
          console.log('No role determined from accessible pages');
        }
      } else {
        console.log('No page_index found for user');
        console.log('Full data object:', data);
      }
      
      console.log('=== End fetchUserRole Debug ===');
    } catch (error) {
      console.error('=== fetchUserRole Error ===');
      console.error('Error fetching user role:', error);
      console.error('Error stack:', error.stack);
      console.error('=== End Error ===');
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