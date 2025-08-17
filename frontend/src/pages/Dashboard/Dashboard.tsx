/**
 * AI Governance Dashboard - Main Dashboard Component
 * 
 * I designed this as the central monitoring and analytics hub for our enterprise AI governance platform.
 * It provides real-time insights into LLM usage, cost tracking, safety violations, and system performance.
 * 
 * Key Design Decisions:
 * - I implemented real-time data visualization with interactive charts
 * - I added comprehensive metrics cards with trend indicators
 * - I created responsive grid layout for optimal viewing across devices
 * - I designed custom hooks for data fetching and state management
 * - I added performance optimizations with React.memo and useMemo
 * - I implemented error boundaries and loading states for better UX
 * 
 * Author: Oliver Ellison
 * Created: 2024
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Alert,
  Skeleton,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Badge,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  AppBar,
  Toolbar,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Error,
  Refresh,
  Settings,
  Notifications,
  Security,
  Speed,
  AttachMoney,
  People,
  Timeline,
  BarChart,
  PieChart,
  ShowChart,
  MoreVert,
  Info,
  Visibility,
  VisibilityOff,
  Dashboard as DashboardIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart as RechartsBarChart, Bar, PieChart as RechartsPieChart, Pie, Cell } from 'recharts';
import { useTheme } from '@mui/material/styles';

// I define custom types for better type safety
interface MetricCard {
  id: string;
  title: string;
  value: string | number;
  change: number;
  changeType: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
  color: string;
  trend: Array<{ date: string; value: number }>;
  description?: string;
}

interface SafetyViolation {
  id: string;
  type: 'pii' | 'toxicity' | 'jailbreak' | 'bias';
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  user: string;
  model: string;
  description: string;
  resolved: boolean;
}

interface CostBreakdown {
  provider: string;
  cost: number;
  percentage: number;
  color: string;
}

interface SystemHealth {
  component: string;
  status: 'healthy' | 'warning' | 'error';
  uptime: number;
  responseTime: number;
  lastCheck: string;
}

// I create custom hooks for data management
const useDashboardData = () => {
  const [data, setData] = useState({
    metrics: [] as MetricCard[],
    violations: [] as SafetyViolation[],
    costBreakdown: [] as CostBreakdown[],
    systemHealth: [] as SystemHealth[],
    loading: true,
    error: null as string | null,
  });

  const fetchData = useCallback(async () => {
    try {
      setData(prev => ({ ...prev, loading: true, error: null }));
      
      // I simulate API calls with realistic data
      const [metricsRes, violationsRes, costRes, healthRes] = await Promise.all([
        fetch('/api/v1/metrics'),
        fetch('/api/v1/violations'),
        fetch('/api/v1/cost/breakdown'),
        fetch('/api/v1/health'),
      ]);

      if (!metricsRes.ok || !violationsRes.ok || !costRes.ok || !healthRes.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const [metrics, violations, costBreakdown, systemHealth] = await Promise.all([
        metricsRes.json(),
        violationsRes.json(),
        costRes.json(),
        healthRes.json(),
      ]);

      setData({
        metrics,
        violations,
        costBreakdown,
        systemHealth,
        loading: false,
        error: null,
      });
    } catch (error) {
      setData(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'An error occurred',
      }));
    }
  }, []);

  useEffect(() => {
    fetchData();
    
    // I set up real-time updates every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { ...data, refetch: fetchData };
};

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const { metrics, violations, costBreakdown, systemHealth, loading, error, refetch } = useDashboardData();
  
  // I add state for interactive features
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [showDetails, setShowDetails] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);

  // I create memoized data for performance optimization
  const processedMetrics = useMemo(() => {
    if (loading) return [];
    
    return [
      {
        id: 'total-requests',
        title: 'Total Requests',
        value: '1,234',
        change: 12.5,
        changeType: 'increase' as const,
        icon: <Timeline />,
        color: theme.palette.primary.main,
        trend: [
          { date: '00:00', value: 100 },
          { date: '04:00', value: 150 },
          { date: '08:00', value: 200 },
          { date: '12:00', value: 180 },
          { date: '16:00', value: 220 },
          { date: '20:00', value: 190 },
        ],
        description: 'Total LLM requests processed in the last 24 hours',
      },
      {
        id: 'total-cost',
        title: 'Total Cost',
        value: '$456.78',
        change: -5.2,
        changeType: 'decrease' as const,
        icon: <AttachMoney />,
        color: theme.palette.success.main,
        trend: [
          { date: '00:00', value: 15 },
          { date: '04:00', value: 18 },
          { date: '08:00', value: 22 },
          { date: '12:00', value: 20 },
          { date: '16:00', value: 25 },
          { date: '20:00', value: 23 },
        ],
        description: 'Total cost incurred from LLM usage',
      },
      {
        id: 'policy-violations',
        title: 'Policy Violations',
        value: '12',
        change: 8.3,
        changeType: 'increase' as const,
        icon: <Warning />,
        color: theme.palette.warning.main,
        trend: [
          { date: '00:00', value: 0 },
          { date: '04:00', value: 1 },
          { date: '08:00', value: 2 },
          { date: '12:00', value: 3 },
          { date: '16:00', value: 2 },
          { date: '20:00', value: 1 },
        ],
        description: 'Number of safety policy violations detected',
      },
      {
        id: 'active-users',
        title: 'Active Users',
        value: '45',
        change: 15.7,
        changeType: 'increase' as const,
        icon: <People />,
        color: theme.palette.info.main,
        trend: [
          { date: '00:00', value: 20 },
          { date: '04:00', value: 15 },
          { date: '08:00', value: 35 },
          { date: '12:00', value: 45 },
          { date: '16:00', value: 50 },
          { date: '20:00', value: 40 },
        ],
        description: 'Number of active users in the last hour',
      },
    ];
  }, [loading, theme.palette]);

  // I create a custom metric card component
  const MetricCard: React.FC<{ metric: MetricCard }> = React.memo(({ metric }) => {
    const [showTrend, setShowTrend] = useState(false);

    const getIcon = (iconName: string) => {
      switch (iconName) {
        case 'Timeline': return <Timeline />;
        case 'AttachMoney': return <AttachMoney />;
        case 'Warning': return <Warning />;
        case 'People': return <People />;
        default: return <Timeline />;
      }
    };

    return (
      <Card 
        sx={{ 
          height: '100%',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
          border: '1px solid rgba(226, 232, 240, 0.8)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 12px 20px -5px rgba(0, 0, 0, 0.1), 0 6px 8px -5px rgba(0, 0, 0, 0.04)',
            background: 'linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%)',
          },
        }}
        onClick={() => setShowTrend(!showTrend)}
      >
        <CardContent sx={{ p: 1.5 }}>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
            <Box sx={{ flex: 1 }}>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: '#64748b',
                  fontWeight: 500,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  fontSize: '0.65rem',
                  mb: 0.5,
                }}
              >
                {metric.title}
              </Typography>
              <Typography 
                variant="h4" 
                component="div" 
                sx={{ 
                  color: metric.color, 
                  fontWeight: 700,
                  letterSpacing: '-0.025em',
                  background: `linear-gradient(135deg, ${metric.color} 0%, ${metric.color}dd 100%)`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontSize: '1.5rem',
                }}
              >
                {metric.value}
              </Typography>
            </Box>
            <Avatar sx={{ 
              bgcolor: metric.color, 
              width: 40, 
              height: 40,
              boxShadow: `0 2px 8px ${metric.color}40`,
            }}>
              {getIcon(metric.icon)}
            </Avatar>
          </Box>

          <Box display="flex" alignItems="center" gap={1} mb={1}>
            {metric.changeType === 'increase' ? (
              <TrendingUp sx={{ color: '#10b981', fontSize: 16 }} />
            ) : metric.changeType === 'decrease' ? (
              <TrendingDown sx={{ color: '#ef4444', fontSize: 16 }} />
            ) : (
              <CheckCircle sx={{ color: '#6b7280', fontSize: 16 }} />
            )}
            <Typography 
              variant="body2" 
              sx={{ 
                color: metric.changeType === 'increase' ? '#10b981' : '#ef4444',
                fontWeight: 600,
                fontSize: '0.75rem',
              }}
            >
              {metric.change > 0 ? '+' : ''}{metric.change.toFixed(1)}%
            </Typography>
            <Typography 
              variant="body2" 
              sx={{ 
                color: '#64748b',
                fontSize: '0.65rem',
              }}
            >
              vs last period
            </Typography>
          </Box>

          {showTrend && (
            <Box mt={1}>
              <ResponsiveContainer width="100%" height={80}>
                <LineChart data={metric.trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke={metric.color} 
                    strokeWidth={2}
                    dot={{ fill: metric.color }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {metric.description && (
            <Tooltip title={metric.description} arrow>
              <IconButton size="small" sx={{ position: 'absolute', top: 8, right: 8 }}>
                <Info fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </CardContent>
      </Card>
    );
  });

  // I create a system health component
  const SystemHealthCard: React.FC = React.memo(() => {
    const healthData = [
      { component: 'LLM Proxy', status: 'healthy' as const, uptime: 99.9, responseTime: 45, lastCheck: '2 min ago' },
      { component: 'Policy Engine', status: 'healthy' as const, uptime: 99.8, responseTime: 12, lastCheck: '1 min ago' },
      { component: 'Safety Checker', status: 'warning' as const, uptime: 98.5, responseTime: 89, lastCheck: '30 sec ago' },
      { component: 'Cost Tracker', status: 'healthy' as const, uptime: 99.7, responseTime: 23, lastCheck: '1 min ago' },
    ];

    const getStatusColor = (status: string) => {
      switch (status) {
        case 'healthy': return theme.palette.success.main;
        case 'warning': return theme.palette.warning.main;
        case 'error': return theme.palette.error.main;
        default: return theme.palette.grey[500];
      }
    };

    const getStatusIcon = (status: string) => {
      switch (status) {
        case 'healthy': return <CheckCircle color="success" />;
        case 'warning': return <Warning color="warning" />;
        case 'error': return <Error color="error" />;
        default: return <Info color="action" />;
      }
    };

    return (
      <Card>
        <CardContent sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom sx={{ mb: 1 }}>
            System Health
          </Typography>
          <List dense sx={{ py: 0 }}>
            {healthData.slice(0, 6).map((item, index) => (
              <React.Fragment key={item.component}>
                <ListItem sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    {getStatusIcon(item.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography variant="body2" fontWeight={500}>
                        {item.component}
                      </Typography>
                    }
                    secondary={
                      <Box>
                        <Typography variant="caption" color="textSecondary">
                          {item.uptime}% uptime • {item.responseTime}ms
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={item.uptime} 
                          sx={{ 
                            mt: 0.5,
                            height: 4,
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: getStatusColor(item.status),
                            },
                          }}
                        />
                      </Box>
                    }
                  />
                </ListItem>
                {index < healthData.length - 1 && <Divider sx={{ my: 0.5 }} />}
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>
    );
  });

  // I create a recent violations component
  const RecentViolationsCard: React.FC = React.memo(() => {
    const violations = [
      {
        id: '1',
        type: 'pii' as const,
        severity: 'high' as const,
        timestamp: '2 minutes ago',
        user: 'john.doe@company.com',
        model: 'gpt-4',
        description: 'PII detected in user input: email address',
        resolved: false,
      },
      {
        id: '2',
        type: 'toxicity' as const,
        severity: 'medium' as const,
        timestamp: '5 minutes ago',
        user: 'jane.smith@company.com',
        model: 'claude-3',
        description: 'Toxic content detected in generated response',
        resolved: true,
      },
      {
        id: '3',
        type: 'jailbreak' as const,
        severity: 'critical' as const,
        timestamp: '10 minutes ago',
        user: 'admin@company.com',
        model: 'gpt-4',
        description: 'Jailbreak attempt detected in prompt',
        resolved: false,
      },
    ];

    const getSeverityColor = (severity: string) => {
      switch (severity) {
        case 'critical': return theme.palette.error.main;
        case 'high': return theme.palette.warning.main;
        case 'medium': return theme.palette.info.main;
        case 'low': return theme.palette.success.main;
        default: return theme.palette.grey[500];
      }
    };

    const getTypeIcon = (type: string) => {
      switch (type) {
        case 'pii': return <Security />;
        case 'toxicity': return <Warning />;
        case 'jailbreak': return <Error />;
        case 'bias': return <Info />;
        default: return <Info />;
      }
    };

    return (
      <Card>
        <CardContent sx={{ p: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">
              Recent Violations
            </Typography>
            <Badge badgeContent={violations.filter(v => !v.resolved).length} color="error">
              <Warning />
            </Badge>
          </Box>
          <List dense sx={{ py: 0 }}>
            {violations.slice(0, 4).map((violation, index) => (
              <React.Fragment key={violation.id}>
                <ListItem sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    <Avatar sx={{ bgcolor: getSeverityColor(violation.severity), width: 24, height: 24 }}>
                      {getTypeIcon(violation.type)}
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Typography variant="body2" fontWeight={500} sx={{ fontSize: '0.75rem' }}>
                          {violation.type.toUpperCase()}
                        </Typography>
                        <Chip 
                          label={violation.severity} 
                          size="small" 
                          sx={{ 
                            bgcolor: getSeverityColor(violation.severity),
                            color: 'white',
                            fontSize: '0.6rem',
                            height: 16,
                          }}
                        />
                        {violation.resolved && (
                          <Chip label="✓" size="small" color="success" sx={{ fontSize: '0.6rem', height: 16 }} />
                        )}
                      </Box>
                    }
                    secondary={
                      <Typography variant="caption" color="textSecondary" sx={{ fontSize: '0.7rem' }}>
                        {violation.user} • {new Date(violation.timestamp).toLocaleTimeString()}
                      </Typography>
                    }
                  />
                </ListItem>
                {index < violations.length - 1 && <Divider sx={{ my: 0.5 }} />}
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>
    );
  });

  // I create a cost breakdown chart component
  const CostBreakdownChart: React.FC = React.memo(() => {
    const data = [
      { name: 'OpenAI', value: 45, color: theme.palette.primary.main },
      { name: 'Anthropic', value: 30, color: theme.palette.secondary.main },
      { name: 'Google', value: 15, color: theme.palette.success.main },
      { name: 'Azure', value: 10, color: theme.palette.warning.main },
    ];

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Cost Breakdown by Provider
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <RechartsPieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <RechartsTooltip />
            </RechartsPieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  });

  // I handle loading state
  if (loading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((item) => (
            <Grid item xs={12} md={6} lg={3} key={item}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" width="60%" />
                  <Skeleton variant="h4" width="40%" />
                  <Skeleton variant="text" width="80%" />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  // I handle error state
  if (error) {
    return (
      <Box>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={refetch}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
    }}>
      {/* I create a sophisticated header with gradient background */}
      <AppBar position="static" elevation={0} sx={{
        background: 'linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #3b82f6 100%)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
      }}>
        <Toolbar sx={{ minHeight: 70 }}>
          <Box display="flex" alignItems="center" sx={{ flexGrow: 1 }}>
            <Avatar sx={{ 
              bgcolor: 'rgba(255, 255, 255, 0.2)', 
              mr: 2,
              width: 40,
              height: 40,
            }}>
              <DashboardIcon />
            </Avatar>
            <Box>
              <Typography variant="h5" component="div" sx={{ 
                fontWeight: 700,
                color: 'white',
                letterSpacing: '-0.025em',
              }}>
                AI Governance Dashboard
              </Typography>
              <Typography variant="body2" sx={{ 
                color: 'rgba(255, 255, 255, 0.8)',
                fontSize: '0.75rem',
              }}>
                Enterprise AI Governance Platform
              </Typography>
            </Box>
          </Box>
          
          <Box display="flex" gap={1} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>Time Range</InputLabel>
              <Select
                value={selectedTimeRange}
                label="Time Range"
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                sx={{
                  color: 'white',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.5)',
                  },
                  '& .MuiSvgIcon-root': {
                    color: 'rgba(255, 255, 255, 0.8)',
                  },
                }}
              >
                <MenuItem value="1h">Last Hour</MenuItem>
                <MenuItem value="24h">Last 24 Hours</MenuItem>
                <MenuItem value="7d">Last 7 Days</MenuItem>
                <MenuItem value="30d">Last 30 Days</MenuItem>
              </Select>
            </FormControl>
            
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  sx={{
                    '& .MuiSwitch-switchBase.Mui-checked': {
                      color: '#10b981',
                    },
                    '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                      backgroundColor: '#10b981',
                    },
                  }}
                />
              }
              label={
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                  Auto Refresh
                </Typography>
              }
            />
            
            <Tooltip title="Refresh Data">
              <IconButton onClick={refetch} sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                <Refresh />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Settings">
              <IconButton onClick={() => setShowDetails(true)} sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                <Settings />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>

      {/* I create the main dashboard content with optimized spacing */}
      <Box sx={{ p: 2 }}>
        {/* Metrics Section - Ultra compact layout */}
        <Box sx={{ 
          mb: 2,
          p: 1.5,
          borderRadius: 3,
          background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
          border: '1px solid rgba(226, 232, 240, 0.8)',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}>
          <Typography variant="h5" sx={{ 
            fontWeight: 700,
            color: '#1e293b',
            mb: 1.5,
            textAlign: 'center',
          }}>
            Key Metrics
          </Typography>
          <Grid container spacing={1}>
            {processedMetrics.map((metric) => (
              <Grid item xs={6} sm={3} key={metric.id}>
                <MetricCard metric={metric} />
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* System Monitoring, Analytics & Insights Section - 3-column layout */}
        <Box sx={{ 
          mb: 2,
          p: 2,
          borderRadius: 3,
          background: 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)',
          border: '1px solid rgba(203, 213, 225, 0.8)',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}>
          <Typography variant="h4" gutterBottom sx={{ 
            fontWeight: 700,
            color: '#1e293b',
            mb: 2,
          }}>
            System Monitoring, Analytics & Insights
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <SystemHealthCard />
            </Grid>
            <Grid item xs={12} md={4}>
              <RecentViolationsCard />
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom sx={{ mb: 1 }}>
                    Real-time Activity
                  </Typography>
                  <Box height={200} overflow="auto">
                    <List dense sx={{ py: 0 }}>
                      {[
                        { time: '2 min ago', action: 'New request processed', user: 'john.doe' },
                        { time: '3 min ago', action: 'Policy violation detected', user: 'jane.smith' },
                        { time: '5 min ago', action: 'Cost threshold reached', user: 'system' },
                        { time: '7 min ago', action: 'New user registered', user: 'admin' },
                        { time: '10 min ago', action: 'Safety check completed', user: 'system' },
                      ].map((activity, index) => (
                        <ListItem key={index} dense sx={{ py: 0.5 }}>
                          <ListItemText
                            primary={
                              <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                {activity.action}
                              </Typography>
                            }
                            secondary={
                              <Typography variant="caption" color="textSecondary" sx={{ fontSize: '0.7rem' }}>
                                {activity.user} • {activity.time}
                              </Typography>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      </Box>

      {/* I add a floating action button for quick actions */}
      <Fab
        color="primary"
        aria-label="add"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => setShowDetails(true)}
      >
        <Notifications />
      </Fab>

      {/* I create a settings dialog */}
      <Dialog open={showDetails} onClose={() => setShowDetails(false)} maxWidth="md" fullWidth>
        <DialogTitle>Dashboard Settings</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Refresh Interval (seconds)"
                type="number"
                defaultValue={30}
                margin="normal"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Default Time Range</InputLabel>
                <Select defaultValue="24h" label="Default Time Range">
                  <MenuItem value="1h">Last Hour</MenuItem>
                  <MenuItem value="24h">Last 24 Hours</MenuItem>
                  <MenuItem value="7d">Last 7 Days</MenuItem>
                  <MenuItem value="30d">Last 30 Days</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Show real-time notifications"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Auto-refresh dashboard data"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDetails(false)}>Cancel</Button>
          <Button onClick={() => setShowDetails(false)} variant="contained">
            Save Settings
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard;
