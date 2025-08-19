import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Shield, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Unauthorized = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-guild-brand-bg p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="mx-auto w-12 h-12 rounded-full bg-guild-danger/20 flex items-center justify-center mb-4">
            <Shield className="w-6 h-6 text-guild-danger" />
          </div>
          <CardTitle className="text-xl">Access Denied</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            You don't have permission to access this page. Please contact your administrator if you believe this is an error.
          </p>
          
          <Button asChild variant="outline">
            <Link to="/hub">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default Unauthorized;