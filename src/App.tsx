import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/hooks/use-auth";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Layout } from "@/components/Layout";
import Auth from "./pages/Auth";
import Scouting from "./pages/Scouting";
import Tracker from "./pages/Tracker";
import Trends from "./pages/Trends";
import Hub from "./pages/Hub";
import Unauthorized from "./pages/Unauthorized";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/scouting" replace />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/unauthorized" element={<Unauthorized />} />
            
            <Route element={<Layout />}>
              <Route 
                path="/scouting" 
                element={
                  <ProtectedRoute allowedRoles={['CGDC']}>
                    <Scouting />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/tracker" 
                element={
                  <ProtectedRoute allowedRoles={['CGDC']}>
                    <Tracker />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/trends" 
                element={
                  <ProtectedRoute allowedRoles={['CGDC']}>
                    <Trends />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/hub" 
                element={
                  <ProtectedRoute allowedRoles={['CGDC', 'PARTNER']}>
                    <Hub />
                  </ProtectedRoute>
                } 
              />
            </Route>
            
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
