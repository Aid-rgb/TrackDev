import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

export const HealthGauge = ({ score, statusText }) => {
  const data = [
    { value: score },
    { value: 100 - score },
  ];

  const getColor = (val) => {
    if (val >= 85) return '#10b981'; // emerald-500
    if (val >= 60) return '#f59e0b'; // amber-500
    return '#ef4444'; // red-500
  };

  return (
    <div className="flex flex-col items-center justify-center h-[240px] relative w-full mt-2">
      <div className="w-full h-[180px] relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={80}
              outerRadius={110}
              paddingAngle={0}
              dataKey="value"
              stroke="none"
              cornerRadius={4}
            >
              <Cell fill={getColor(score)} />
              <Cell fill="#1e293b" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        {/* Number inside the gauge center */}
        <div className="absolute bottom-0 left-0 w-full flex flex-col items-center justify-end pointer-events-none pb-1">
          <span className="text-5xl font-bold tracking-tight drop-shadow-md" style={{ color: getColor(score) }}>
            {score}
          </span>
        </div>
      </div>
      <div className="mt-4 z-10 text-center">
        <p className="text-sm font-medium text-slate-300 px-4 py-1.5 bg-slate-800/80 rounded-full border border-slate-700 shadow-sm">
          {statusText}
        </p>
      </div>
    </div>
  );
};
