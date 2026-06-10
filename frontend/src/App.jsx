import React, { useState, useEffect } from 'react';
import { 
  Activity, Clock, BarChart3, AlertCircle, RefreshCcw, 
  LayoutDashboard, Filter, CheckCircle2, Calendar, Users, 
  Bug, TrendingUp, Briefcase, Target, Zap
} from 'lucide-react';
import { MetricCard } from './components/MetricCard';
import { HealthGauge } from './components/HealthGauge';
import { metricsApi } from './api';
import { 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, Legend, PieChart, Pie, Cell,
  ComposedChart, Line
} from 'recharts';
import { motion } from 'framer-motion';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f43f5e'];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

function App() {
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  
  const [period, setPeriod] = useState('month'); 
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadInitialData();
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  const loadInitialData = async () => {
    try {
      const projectsList = await metricsApi.getProjects();
      setProjects(projectsList);
      await fetchDashboardData(null, period);
    } catch (err) {
      console.error('Failed to load initial data:', err);
      setError('Ошибка при загрузке проектов');
    } finally {
      setLoading(false);
    }
  };

  const getEffectivePeriod = (p) => {
    if (p === 'custom' && customStart && customEnd) {
      return `${customStart}|${customEnd}`;
    }
    return p === 'custom' ? 'month' : p;
  };

  const fetchDashboardData = async (projectId, currentPeriod) => {
    setLoading(true);
    setError(null);
    try {
      const effectivePeriod = getEffectivePeriod(currentPeriod);
      const dashboardData = await metricsApi.getDashboard(projectId, effectivePeriod);
      setData(dashboardData);
    } catch (err) {
      console.error('Failed to fetch dashboard:', err);
      setError(err.response?.data?.detail || err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleProjectChange = (id) => {
    const projectId = id === "" ? null : Number(id);
    setSelectedProject(projectId);
    fetchDashboardData(projectId, period);
  };

  const handlePeriodChange = (p) => {
    setPeriod(p);
    if (p !== 'custom') {
      fetchDashboardData(selectedProject, p);
    }
  };

  const handleCustomDateApply = () => {
    if (customStart && customEnd) {
      fetchDashboardData(selectedProject, 'custom');
    }
  };

  if (loading && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-4">
          <RefreshCcw className="w-8 h-8 text-primary animate-spin" />
          <p className="text-slate-400">Загрузка аналитики...</p>
        </div>
      </div>
    );
  }

  const workloadData = data?.planning?.workload_distribution?.workload || [];
  const timeTracking = data?.planning?.time_tracking || {};
  const estimationData = data?.planning?.estimation_accuracy || {};
  const quality = data?.quality || {};
  const deadlines = data?.deadlines || {};
  const workload = data?.workload || {};

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-[1400px] mx-auto bg-slate-950 text-slate-200 overflow-x-hidden">
      {/* Header */}
      <header className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3 text-white">
            <LayoutDashboard className="w-8 h-8 text-primary" />
            Дашборд Аналитики
          </h1>
          <p className="text-slate-400 text-sm mt-1">Продвинутая статистика проектов Redmine</p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full xl:w-auto">
          {/* Project Selector */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 w-full md:w-auto shadow-sm">
            <Filter className="w-4 h-4 text-slate-500" />
            <select 
              className="bg-transparent text-sm outline-none w-full text-slate-200"
              value={selectedProject || ""}
              onChange={(e) => handleProjectChange(e.target.value)}
            >
              <option value="" className="bg-slate-900">Все проекты</option>
              {projects.map(p => (
                <option key={p.id} value={p.id} className="bg-slate-900">{p.name}</option>
              ))}
            </select>
          </div>

          {/* Period Selector */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1 overflow-x-auto shadow-sm">
            {['week', 'month', 'quarter', 'year', 'custom'].map((p) => (
              <button
                key={p}
                onClick={() => handlePeriodChange(p)}
                className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all whitespace-nowrap ${
                  period === p ? 'bg-primary text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {p === 'week' ? 'Неделя' : 
                 p === 'month' ? 'Месяц' : 
                 p === 'quarter' ? 'Квартал' : 
                 p === 'year' ? 'Год' : 'Свой период'}
              </button>
            ))}
          </div>

          {/* Custom Date Pickers */}
          {period === 'custom' && (
            <motion.div 
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5"
            >
              <Calendar className="w-4 h-4 text-slate-500" />
              <input 
                type="date" 
                className="bg-transparent text-sm outline-none text-slate-200 [color-scheme:dark]"
                value={customStart}
                onChange={e => setCustomStart(e.target.value)}
              />
              <span className="text-slate-500">-</span>
              <input 
                type="date" 
                className="bg-transparent text-sm outline-none text-slate-200 [color-scheme:dark]"
                value={customEnd}
                onChange={e => setCustomEnd(e.target.value)}
              />
              <button 
                onClick={handleCustomDateApply}
                className="ml-2 bg-primary/20 text-primary px-3 py-1 rounded-md text-xs hover:bg-primary/30 font-medium transition-colors"
              >
                Применить
              </button>
            </motion.div>
          )}
          
          <button 
            onClick={() => fetchDashboardData(selectedProject, period)}
            className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg hover:bg-slate-800 transition-colors shadow-sm"
          >
            <RefreshCcw className={`w-4 h-4 text-slate-300 ${loading ? 'animate-spin text-primary' : ''}`} />
          </button>
        </div>
      </header>

      {error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-rose-500/10 border border-rose-500/50 rounded-xl p-4 mb-8 flex items-center gap-3 text-rose-400">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm font-medium">{error}</p>
        </motion.div>
      )}

      {data ? (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
          
          {/* Row 1: Health & Top Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <motion.div variants={fadeUp} className="lg:col-span-2 glass-card p-6 flex flex-col md:flex-row items-center gap-8 border-t-4 border-t-primary shadow-lg shadow-primary/5">
              <div className="w-full md:w-1/2">
                <h2 className="text-xl font-bold mb-2 flex items-center gap-2 text-white">
                  <Activity className="w-6 h-6 text-primary" />
                  Здоровье проекта
                </h2>
                <HealthGauge score={data.health_score?.score || 0} statusText={data.health_score?.status_text || ''} />
              </div>
              <div className="w-full md:w-1/2">
                <h3 className="text-sm font-medium text-slate-400 mb-3">Рекомендации и Факторы:</h3>
                <div className="space-y-3 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                  {data.health_score?.factors?.length > 0 && (
                    <ul className="space-y-2">
                      {data.health_score.factors.map((f, i) => (
                        <li key={i} className="text-xs flex items-start gap-2 text-rose-400 bg-rose-500/10 p-2 rounded-md">
                          <AlertCircle className="w-4 h-4 shrink-0" />
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  <ul className="space-y-2">
                    {data.health_score?.recommendations?.map((rec, i) => (
                      <li key={i} className="text-xs flex items-start gap-2 text-emerald-300 bg-emerald-500/10 p-2 rounded-md">
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </motion.div>

            <motion.div variants={fadeUp} className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6">
              <MetricCard 
                title="Бэклог (Открыто)"
                value={workload.backlog?.total || 0}
                icon={BarChart3}
                subtitle={`${workload.backlog?.open || 0} к выполнению, ${workload.backlog?.in_progress || 0} в работе`}
                trend={workload.backlog_change?.change ? {
                  value: Math.abs(workload.backlog_change.change),
                  label: 'задач за период',
                  isPercent: false,
                  isPositive: workload.backlog_change.change < 0
                } : null}
                loading={loading}
              />
              <MetricCard 
                title="Качество (Bugs)"
                value={`${quality.bug_rate?.bug_rate_percent || 0}%`}
                icon={Bug}
                subtitle={`${quality.bug_metrics?.open_bugs || 0} открытых багов`}
                loading={loading}
                className={quality.bug_rate?.bug_rate_percent > 15 ? "border-rose-500/50 shadow-[0_0_15px_rgba(244,63,94,0.1)]" : ""}
              />
            </motion.div>
          </div>

          {/* Row 2: Personnel & Time Analytics */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            
            {/* Personnel Analytics */}
            <motion.div variants={fadeUp} className="glass-card p-6 flex flex-col h-full">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold flex items-center gap-2 text-white">
                  <Briefcase className="w-5 h-5 text-indigo-400" />
                  Аналитика по персоналу (Загрузка)
                </h2>
              </div>
              
              {workloadData.length > 0 ? (
                <>
                  <div className="h-[250px] md:h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={workloadData.slice(0, 8)} margin={{ top: 20, right: 10, bottom: 20, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                        <XAxis dataKey="user" stroke="#64748b" fontSize={10} tickFormatter={(val) => val.split(' ')[0]} tick={{fill: '#94a3b8'}} tickMargin={10} />
                        <YAxis yAxisId="left" stroke="#64748b" fontSize={10} orientation="left" tick={{fill: '#94a3b8'}} />
                        <YAxis yAxisId="right" stroke="#64748b" fontSize={10} orientation="right" tick={{fill: '#94a3b8'}} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc', backdropFilter: 'blur(4px)' }}
                          itemStyle={{ fontSize: '12px' }}
                        />
                        <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                        <Bar yAxisId="left" dataKey="active_tasks" name="Задач в работе" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={24} />
                        <Line yAxisId="right" type="monotone" dataKey="estimated_hours" name="Оценка (часы)" stroke="#10b981" strokeWidth={3} dot={{ r: 4, fill: '#10b981', strokeWidth: 2, stroke: '#0f172a' }} activeDot={{ r: 6 }} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                  {/* Mobile-friendly textual summary */}
                  <div className="mt-4 space-y-2 lg:hidden">
                    {workloadData.slice(0, 8).map((user, i) => (
                      <div key={i} className="flex justify-between items-center text-sm bg-slate-800/30 p-2.5 rounded-lg border border-slate-700/30">
                        <span className="text-slate-200 font-medium truncate pr-2">{user.user}</span>
                        <div className="flex items-center gap-3 text-xs shrink-0">
                          <span className="text-indigo-400 font-medium bg-indigo-500/10 px-2 py-1 rounded-md">{user.active_tasks} задач</span>
                          <span className="text-emerald-400 font-medium bg-emerald-500/10 px-2 py-1 rounded-md">{user.estimated_hours} ч</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-[250px] md:h-[300px] text-slate-500">Нет данных о нагрузке</div>
              )}
            </motion.div>

            {/* Time Tracking Details */}
            <motion.div variants={fadeUp} className="glass-card p-6 flex flex-col h-full">
              <h2 className="text-lg font-semibold mb-6 flex items-center gap-2 text-white">
                <Clock className="w-5 h-5 text-sky-400" />
                Затраченное время
              </h2>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col items-center justify-center">
                  <span className="text-sm text-slate-400 mb-1">Всего за период</span>
                  <span className="text-3xl font-bold text-sky-400">{timeTracking?.total_hours?.toFixed(1) || '0.0'}<span className="text-lg text-slate-500 ml-1">ч</span></span>
                </div>
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col items-center justify-center">
                  <span className="text-sm text-slate-400 mb-1">В среднем в день</span>
                  <span className="text-3xl font-bold text-white">{timeTracking?.avg_hours_per_day?.toFixed(1) || '0.0'}<span className="text-lg text-slate-500 ml-1">ч</span></span>
                </div>
              </div>

              <div className="flex-1 min-h-0 flex flex-col">
                <h3 className="text-sm font-medium text-slate-400 mb-3">Распределение по видам работ</h3>
                {Object.keys(timeTracking?.by_activity || {}).length > 0 ? (
                  <div className="h-[180px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={Object.entries(timeTracking.by_activity).map(([name, value]) => ({ name, value }))}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={75}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {Object.entries(timeTracking.by_activity).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid #334155', borderRadius: '8px' }}
                          itemStyle={{ fontSize: '12px' }}
                          formatter={(value) => [`${Number(value).toFixed(1)} ч`, 'Время']}
                        />
                        <Legend layout="vertical" verticalAlign="middle" align="right" wrapperStyle={{ fontSize: '12px', color: '#cbd5e1' }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="flex items-center justify-center flex-1 text-slate-500 text-sm">Нет записей времени за период</div>
                )}
              </div>
            </motion.div>
          </div>

          {/* Row 3: Time Tracking Details (New) */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            
            {/* Time by Priority (Pie Chart) */}
            <motion.div variants={fadeUp} className="glass-card p-6 xl:col-span-1 flex flex-col">
              <h2 className="text-lg font-semibold mb-6 flex items-center gap-2 text-white">
                <Target className="w-5 h-5 text-fuchsia-400" />
                Время по приоритетам задач
              </h2>
              <div className="flex-1 min-h-0 flex flex-col justify-center">
                {Object.keys(timeTracking?.by_priority || {}).length > 0 ? (
                  <div className="h-[250px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={Object.entries(timeTracking.by_priority).map(([name, value]) => ({ name, value }))}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={85}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {Object.entries(timeTracking.by_priority).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid #334155', borderRadius: '8px' }}
                          itemStyle={{ fontSize: '12px' }}
                          formatter={(value) => [`${Number(value).toFixed(1)} ч`, 'Время']}
                        />
                        <Legend layout="horizontal" verticalAlign="bottom" align="center" wrapperStyle={{ paddingTop: '20px', fontSize: '12px', color: '#cbd5e1' }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="flex items-center justify-center flex-1 text-slate-500 text-sm">Нет данных по приоритетам задач</div>
                )}
              </div>
            </motion.div>

            {/* Time Detailed by Assignee & Activity (Stacked Bar) */}
            <motion.div variants={fadeUp} className="glass-card p-6 xl:col-span-2 flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold flex items-center gap-2 text-white">
                  <Users className="w-5 h-5 text-sky-400" />
                  Детализация времени по исполнителям
                </h2>
              </div>
              
              {timeTracking?.user_detailed?.length > 0 ? (
                <>
                  <div className="h-[250px] md:h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={timeTracking.user_detailed.slice(0, 8)} margin={{ top: 20, right: 10, left: -20, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                        <XAxis dataKey="name" stroke="#64748b" fontSize={10} tickFormatter={(val) => val.split(' ')[0]} tick={{fill: '#94a3b8'}} tickMargin={10} />
                        <YAxis stroke="#64748b" fontSize={10} tick={{fill: '#94a3b8'}} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc', backdropFilter: 'blur(4px)' }}
                          itemStyle={{ fontSize: '12px' }}
                          cursor={{ fill: 'rgba(51, 65, 85, 0.4)' }}
                        />
                        <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                        {Array.from(new Set(timeTracking.user_detailed.flatMap(u => Object.keys(u).filter(k => k !== 'name' && k !== 'total')))).map((activity, index) => (
                          <Bar key={activity} dataKey={activity} stackId="a" fill={COLORS[index % COLORS.length]} />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  {/* Mobile-friendly textual summary */}
                  <div className="mt-4 space-y-2 lg:hidden">
                    {timeTracking.user_detailed.slice(0, 8).map((u, i) => (
                      <div key={i} className="flex flex-col text-sm bg-slate-800/30 p-3 rounded-lg border border-slate-700/30">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-slate-200 font-medium truncate">{u.name}</span>
                          <span className="text-sky-400 font-bold bg-sky-500/10 px-2 py-1 rounded-md shrink-0">{u.total} ч</span>
                        </div>
                        <div className="flex flex-wrap gap-2 text-[10px] text-slate-400">
                          {Object.entries(u).filter(([k]) => k !== 'name' && k !== 'total').map(([k, v]) => (
                            <span key={k} className="bg-slate-900/80 px-2 py-1 rounded">{k}: <span className="text-slate-300">{v}ч</span></span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-[250px] md:h-[300px] text-slate-500">Нет данных о списании времени</div>
              )}
            </motion.div>

          </div>

          {/* Row 4: Tasks & Execution */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Velocity */}
            <motion.div variants={fadeUp} className="glass-card p-6 lg:col-span-2">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold flex items-center gap-2 text-white">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  Velocity (Динамика закрытия)
                </h2>
                <div className="px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-sm font-medium border border-emerald-500/20">
                  Всего: {workload.velocity?.total_closed || workload.velocity?.closed_count || 0}
                </div>
              </div>
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={Object.entries(workload.velocity?.by_week || workload.velocity?.closed_per_day || {}).map(([date, count]) => ({ date, count }))} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis 
                      dataKey="date" 
                      stroke="#64748b" 
                      fontSize={11}
                      tickFormatter={(val) => {
                        const parts = val.split('-');
                        return parts.length >= 3 ? `${parts[2]}/${parts[1]}` : val;
                      }}
                      tickMargin={10}
                    />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid #334155', borderRadius: '8px' }}
                      itemStyle={{ color: '#10b981' }}
                    />
                    <Area type="monotone" dataKey="count" name="Закрыто задач" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            {/* Estimation Accuracy & Deadlines */}
            <motion.div variants={fadeUp} className="glass-card p-6 flex flex-col gap-6">
              <div>
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-white">
                  <Target className="w-5 h-5 text-amber-400" />
                  Точность оценок
                </h2>
                {estimationData && estimationData.total_analyzed > 0 ? (
                  <div className="space-y-4">
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-sm text-slate-400">Точность попадания</p>
                        <p className="text-2xl font-bold text-amber-400">{estimationData.accuracy_rate}%</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-slate-400">Ср. отклонение</p>
                        <p className="text-lg font-semibold text-white">{estimationData.avg_deviation_percent}%</p>
                      </div>
                    </div>
                    <div className="flex w-full h-3 rounded-full overflow-hidden">
                      <div style={{ width: `${(estimationData.underestimated / estimationData.total_analyzed) * 100}%` }} className="bg-rose-500" title={`Недооценено: ${estimationData.underestimated}`}></div>
                      <div style={{ width: `${(estimationData.accurate / estimationData.total_analyzed) * 100}%` }} className="bg-emerald-500" title={`Точно: ${estimationData.accurate}`}></div>
                      <div style={{ width: `${(estimationData.overestimated / estimationData.total_analyzed) * 100}%` }} className="bg-blue-500" title={`Переоценено: ${estimationData.overestimated}`}></div>
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-400 mt-1 px-1">
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500"></span> Недооценено</span>
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> Точно</span>
                      <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"></span> Переоценено</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 italic">Недостаточно данных для анализа оценок (нужно логировать время в оцененных задачах).</p>
                )}
              </div>

              <div className="border-t border-slate-800 pt-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-white">
                  <Zap className="w-5 h-5 text-purple-400" />
                  Статусы задач (Бэклог)
                </h2>
                <div className="space-y-3">
                  {Object.entries(workload.backlog?.by_status || {})
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 4)
                    .map(([status, count], i) => (
                      <div key={i} className="flex justify-between items-center text-sm">
                        <span className="text-slate-300 truncate pr-4">{status}</span>
                        <div className="flex items-center gap-3">
                          <span className="font-medium text-white">{count}</span>
                          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 rounded-full" style={{ width: `${(count / (workload.backlog?.total || 1)) * 100}%` }}></div>
                          </div>
                        </div>
                      </div>
                  ))}
                </div>
              </div>
            </motion.div>
            
          </div>

          {/* Row 5: Deadlines & Backlog Composition (Restored) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Deadlines & Execution */}
            <motion.div variants={fadeUp} className="glass-card p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-white">
                <Clock className="w-5 h-5 text-emerald-500" />
                Исполнение сроков
              </h2>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-400">В срок ({deadlines?.on_time_completion?.on_time || 0})</span>
                    <span className="font-medium text-emerald-500">{deadlines?.on_time_completion?.on_time_percent?.toFixed(1) || 0}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${deadlines?.on_time_completion?.on_time_percent || 0}%` }}></div>
                  </div>
                </div>
                
                <div className="pt-4 border-t border-slate-800">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-slate-400">Среднее время (Lead Time)</span>
                    <span className="text-lg font-bold text-white">{deadlines?.lead_time?.avg_lead_time_days || 0} <span className="text-sm font-normal text-slate-500">дн</span></span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">Задач без оценки</span>
                    <span className="text-lg font-bold text-amber-500">{data.planning?.tasks_without_due_date?.total || 0}</span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Backlog Composition */}
            <motion.div variants={fadeUp} className="glass-card p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-white">
                <BarChart3 className="w-5 h-5 text-amber-500" />
                Состав бэклога
              </h2>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={Object.entries(workload.backlog?.by_tracker || {}).map(([name, value]) => ({ name, value }))} layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                    <XAxis type="number" stroke="#64748b" fontSize={11} />
                    <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={11} width={80} />
                    <Tooltip contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid #334155', borderRadius: '8px' }} />
                    <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

          </div>

        </motion.div>
      ) : !loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center h-[400px] glass-card">
          <AlertCircle className="w-16 h-16 text-slate-700 mb-4" />
          <p className="text-lg text-slate-400 mb-2">Нет данных для отображения</p>
          <p className="text-sm text-slate-500 mb-6 max-w-md text-center">Проверьте правильность выбранного периода и наличие доступа к проектам.</p>
          <button 
            onClick={() => loadInitialData()}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-600 transition-colors shadow-lg shadow-primary/20"
          >
            Попробовать снова
          </button>
        </motion.div>
      )}
    </div>
  );
}

export default App;
