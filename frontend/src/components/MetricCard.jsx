import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const MetricCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  className,
  loading
}) => {
  return (
    <div className={twMerge(clsx("glass-card p-6 flex flex-col gap-4", className))}>
      <div className="flex justify-between items-start">
        <div className="p-2 bg-primary/10 rounded-lg">
          {Icon && <Icon className="w-5 h-5 text-primary" />}
        </div>
        {trend && (
          <div className={clsx(
            "text-xs font-medium px-2 py-1 rounded-full",
            trend.isPositive ? "bg-emerald-500/10 text-emerald-500" : "bg-rose-500/10 text-rose-500"
          )}>
            {trend.isPositive ? '+' : ''}{trend.value}{trend.isPercent ? '%' : ''} {trend.label}
          </div>
        )}
      </div>
      
      <div>
        <p className="metric-label mb-1">{title}</p>
        {loading ? (
          <div className="h-9 w-24 bg-slate-800 animate-pulse rounded" />
        ) : (
          <h3 className="metric-value">{value}</h3>
        )}
        {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
      </div>
    </div>
  );
};
