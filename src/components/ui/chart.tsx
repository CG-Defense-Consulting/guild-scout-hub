import React from 'react';

// Simple fallback chart components
export const SimpleLineChart = ({ data, height = 300 }: { data: any[], height?: number }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        No data available
      </div>
    );
  }

  return (
    <div className="w-full h-full flex items-end justify-between gap-1 p-4">
      {data.map((item, index) => (
        <div key={index} className="flex flex-col items-center gap-1">
          <div 
            className="w-8 bg-blue-500 rounded-t"
            style={{ 
              height: `${Math.max(10, (item.rfqs / Math.max(...data.map(d => d.rfqs))) * 200)}px` 
            }}
          />
          <div className="text-xs text-muted-foreground rotate-45 origin-left">
            {new Date(item.date).toLocaleDateString()}
          </div>
        </div>
      ))}
    </div>
  );
};

export const SimplePieChart = ({ data, height = 300 }: { data: any[], height?: number }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        No data available
      </div>
    );
  }

  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  return (
    <div className="w-full h-full flex items-center justify-center">
      <div className="relative w-48 h-48">
        {data.map((item, index) => {
          const percentage = (item.value / total) * 100;
          const rotation = data.slice(0, index).reduce((sum, d) => sum + (d.value / total) * 360, 0);
          
          return (
            <div
              key={index}
              className="absolute inset-0 rounded-full border-8 border-transparent"
              style={{
                borderTopColor: item.fill,
                transform: `rotate(${rotation}deg)`,
                clipPath: `polygon(50% 50%, 50% 0%, ${50 + Math.cos((percentage * Math.PI) / 180) * 50}% ${50 - Math.sin((percentage * Math.PI) / 180) * 50}%, 50% 50%)`
              }}
            />
          );
        })}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold">{total}</div>
            <div className="text-sm text-muted-foreground">Total</div>
          </div>
        </div>
      </div>
    </div>
  );
};
