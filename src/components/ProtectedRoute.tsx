import { Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuth } from '@/hooks/use-auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: ('CGDC' | 'PARTNER')[];
}

export const ProtectedRoute = ({ children, allowedRoles }: ProtectedRouteProps) => {
  const { user, userRole, loading, isSessionFresh, setIntendedPath } = useAuth();
  const currentPath = window.location.pathname;

  // Set intended path when component mounts
  useEffect(() => {
    if (user && currentPath !== '/auth' && currentPath !== '/unauthorized') {
      setIntendedPath(currentPath);
    }
  }, [user, currentPath, setIntendedPath]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!user) {
    // Store the current path as intended destination
    setIntendedPath(currentPath);
    return <Navigate to="/auth" replace />;
  }

  // If user is authenticated but session is not fresh, redirect to login
  // Only do this if we're not in a loading state and the session check has completed
  if (!loading && !isSessionFresh) {
    setIntendedPath(currentPath);
    return <Navigate to="/auth" replace />;
  }

  // Wait for userRole to be fetched before checking role permissions
  // This prevents redirecting to unauthorized when role is still being fetched
  if (allowedRoles && userRole === null) {
    // Still loading the role, show loading state
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading user permissions...</div>
      </div>
    );
  }

  if (allowedRoles && !allowedRoles.includes(userRole!)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};