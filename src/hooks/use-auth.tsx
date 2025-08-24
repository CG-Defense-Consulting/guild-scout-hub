import { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  userRole: 'CGDC' | 'PARTNER' | null;
  loading: boolean;
  isSessionFresh: boolean;
  intendedPath: string | null;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  // signUp: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<void>;
  setIntendedPath: (path: string) => void;
  clearIntendedPath: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [userRole, setUserRole] = useState<'CGDC' | 'PARTNER' | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSessionFresh, setIsSessionFresh] = useState(false);
  const [intendedPath, setIntendedPath] = useState<string | null>(null);

  const checkSessionFreshness = () => {
    const now = Date.now();
    // Use localStorage timestamp for last activity
    const lastActivity = localStorage.getItem('lastActivity');
    
    if (!lastActivity) {
      // If no activity recorded, consider session fresh for now
      // This handles the case where user just logged in or page was reloaded
      setIsSessionFresh(true);
      // Set current time as last activity to start the timer
      try {
        localStorage.setItem('lastActivity', now.toString());
      } catch (error) {
        console.warn('Could not set localStorage on mobile:', error);
        // On mobile, if localStorage fails, assume session is fresh
        setIsSessionFresh(true);
        return;
      }
      return;
    }
    
    const lastActivityTime = parseInt(lastActivity);
    const sessionAge = now - lastActivityTime;
    
    // Session is fresh if less than 1 hour old
    const isFresh = sessionAge < 60 * 60 * 1000; // 1 hour in milliseconds
    setIsSessionFresh(isFresh);
  };

    // Track user activity to keep session fresh
  const updateSessionActivity = () => {
    // Store last activity timestamp in localStorage
    try {
      localStorage.setItem('lastActivity', Date.now().toString());
    } catch (error) {
      console.warn('Could not update localStorage on mobile:', error);
      // On mobile, if localStorage fails, assume session is fresh
      setIsSessionFresh(true);
      return;
    }
    checkSessionFreshness();
  };

  // Track user activity to keep session fresh
  useEffect(() => {
    if (!user) return;

    const handleUserActivity = () => {
      updateSessionActivity();
    };

    // Track various user activities
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    events.forEach(event => {
      document.addEventListener(event, handleUserActivity, { passive: true });
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleUserActivity);
      });
    };
  }, [user]);

  // Set intended path for post-login redirect
  const setIntendedPathHandler = (path: string) => {
    setIntendedPath(path);
  };

  // Clear intended path after successful redirect
  const clearIntendedPathHandler = () => {
    setIntendedPath(null);
  };

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
        } else {
          // If user has access to pages but doesn't match specific roles, default to CGDC
          // This prevents the user from being stuck in a loading state
          setUserRole('CGDC');
        }
      } else {
        setUserRole('CGDC');
      }
    } catch (error) {
      console.error('Error fetching user role:', error);
      // On error, default to CGDC to prevent unauthorized redirects
      setUserRole('CGDC');
    }
  };

  useEffect(() => {
    // Set up auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        // Check if user is forcing a logout
        const forceLogout = localStorage.getItem('forceLogout');
        
        if (forceLogout === 'true') {
          // User is forcing logout, don't process auth state changes
          console.log('Force logout detected, ignoring auth state change');
          localStorage.removeItem('forceLogout');
          return;
        }
        
        setSession(session);
        setUser(session?.user ?? null);
        
        if (session?.user) {
          fetchUserRole(session.user.id);
          // For auth state changes, check session freshness
          checkSessionFreshness();
        } else {
          setUserRole(null);
          setIsSessionFresh(false);
        }
        setLoading(false);
      }
    );

    // Check for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      // Check if user is forcing a logout
      const forceLogout = localStorage.getItem('forceLogout');
      
      if (forceLogout === 'true') {
        // User is forcing logout, don't restore session
        console.log('Force logout detected, not restoring session');
        localStorage.removeItem('forceLogout');
        setSession(null);
        setUser(null);
        setUserRole(null);
        setIsSessionFresh(false);
        setLoading(false);
        return;
      }
      
      setSession(session);
      setUser(session?.user ?? null);
      
      if (session?.user) {
        fetchUserRole(session.user.id);
        // For initial page load, be more lenient with session freshness
        // This prevents immediate redirects on page reload
        const now = Date.now();
        let lastActivity;
        
        try {
          lastActivity = localStorage.getItem('lastActivity');
        } catch (error) {
          console.warn('Could not read localStorage on mobile:', error);
          // On mobile, if localStorage fails, assume session is fresh
          setIsSessionFresh(true);
          setLoading(false);
          return;
        }
        
        if (!lastActivity) {
          // First time or fresh page load - set as fresh
          setIsSessionFresh(true);
          try {
            localStorage.setItem('lastActivity', now.toString());
          } catch (error) {
            console.warn('Could not set localStorage on mobile:', error);
            // Continue with fresh session assumption
          }
        } else {
          // Check if session is actually stale
          const lastActivityTime = parseInt(lastActivity);
          const sessionAge = now - lastActivityTime;
          const isFresh = sessionAge < 60 * 60 * 1000; // 1 hour
          setIsSessionFresh(isFresh);
        }
      } else {
        setIsSessionFresh(false);
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
    
    if (!error) {
      // Update session activity on successful sign in
      updateSessionActivity();
    }
    
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
    // Add a flag to prevent automatic re-login
    localStorage.setItem('forceLogout', 'true');
    
    // Immediately clear local state to prevent auth state listener interference
    setUser(null);
    setSession(null);
    setUserRole(null);
    setIsSessionFresh(false);
    clearIntendedPathHandler();
    localStorage.removeItem('lastActivity');
    
    // Clear any stored Supabase session data
    try {
      // Clear the session from localStorage/sessionStorage
      try {
        localStorage.removeItem('sb-cdyfnojqbtgpsriykkbx-auth-token');
        sessionStorage.removeItem('sb-cdyfnojqbtgpsriykkbx-auth-token');
        localStorage.removeItem('lastActivity');
      } catch (storageError) {
        console.warn('Could not clear localStorage/sessionStorage on mobile:', storageError);
      }
      
      // Try to sign out from server, but don't wait for it
      supabase.auth.signOut().catch(error => {
        console.log('Sign out error (session may already be invalid):', error);
      });
    } catch (error) {
      console.log('Sign out error (session may already be invalid):', error);
    }
    
    // Force immediate redirect to prevent any auth state listener interference
    setTimeout(() => {
      window.location.href = '/auth';
    }, 100);
  };

  const value: AuthContextType = {
    user,
    session,
    userRole,
    loading,
    isSessionFresh,
    intendedPath,
    signIn,
    // signUp,
    signOut,
    setIntendedPath: setIntendedPathHandler,
    clearIntendedPath: clearIntendedPathHandler,
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