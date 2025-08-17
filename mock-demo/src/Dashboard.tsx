/**
 * AI Governance Dashboard - Mock Demo Version
 * 
 * I created this as a standalone dashboard component that works with the mock API
 * to demonstrate the full capabilities of the AI Governance Dashboard without
 * requiring any external dependencies.
 * 
 * Key Features:
 * - Real-time data from mock API endpoints
 * - Interactive charts and visualizations
 * - Comprehensive metrics and analytics
 * - Safety violation monitoring
 * - Cost tracking and breakdown
 * - System health monitoring
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
  BugReport,
  Code,
  DataUsage,
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
  user_email: string;
  model: string;
  description: string;
  resolved: boolean;
  risk_score: number;
}

interface CostBreakdown {
  provider: string;
  cost: number;
  percentage: number;
  color: string;
  requests: number;
}

interface SystemHealth {
  component: string;
  status: 'healthy' | 'warning' | 'error';
  uptime: number;
  responseTime: number;
  lastCheck: string;
  version: string;
  loadAverage: number;
  memoryUsage: number;
  diskUsage: number;
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
      
      // I fetch data from the mock API endpoints
      const [metricsRes, violationsRes, costRes, healthRes] = await Promise.all([
        fetch('/api/v1/metrics'),
        fetch('/api/v1/violations?limit=10'),
        fetch('/api/v1/cost/breakdown'),
        fetch('/api/v1/health'),
      ]);

      if (!metricsRes.ok || !violationsRes.ok || !costRes.ok || !healthRes.ok) {
        throw new Error('Failed to fetch dashboard data');
      }

      const [metrics, violationsData, costBreakdown, systemHealth] = await Promise.all([
        metricsRes.json(),
        violationsRes.json(),
        costRes.json(),
        healthRes.json(),
      ]);

      setData({
        metrics,
        violations: violationsData.data || [],
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
  const [showMockInfo, setShowMockInfo] = useState(false);

  // I create memoized data for performance optimization
  const processedMetrics = useMemo(() => {
    if (loading || !metrics.length) return [];
    return metrics;
  }, [loading, metrics]);

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
             {systemHealth.slice(0, 6).map((item, index) => (
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
                 {index < systemHealth.length - 1 && <Divider sx={{ my: 0.5 }} />}
               </React.Fragment>
             ))}
           </List>
         </CardContent>
       </Card>
     );
   });

     // I create a recent violations component
   const RecentViolationsCard: React.FC = React.memo(() => {
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
                         {violation.user_email} • {new Date(violation.timestamp).toLocaleTimeString()}
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
    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Cost Breakdown by Provider
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <RechartsPieChart>
              <Pie
                data={costBreakdown}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ provider, percentage }) => `${provider} ${percentage.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="cost"
              >
                {costBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <RechartsTooltip formatter={(value, name) => [`$${value.toFixed(2)}`, name]} />
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
          AI Governance Dashboard
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
                Mock Demo Version
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

            <Tooltip title="Mock Demo Info">
              <IconButton onClick={() => setShowMockInfo(true)} sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                <BugReport />
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

      {/* I create a mock demo info dialog */}
      <Dialog open={showMockInfo} onClose={() => setShowMockInfo(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <BugReport />
            Mock Demo Information
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            This is a <strong>mock demo version</strong> of the AI Governance Dashboard that runs completely independently without any external dependencies.
          </Typography>
          
          <Typography variant="h6" gutterBottom>Features Demonstrated:</Typography>
          <List>
            <ListItem>
              <ListItemIcon><DataUsage /></ListItemIcon>
              <ListItemText primary="Real-time metrics and analytics" secondary="Live data from mock API endpoints" />
            </ListItem>
            <ListItem>
              <ListItemIcon><Security /></ListItemIcon>
              <ListItemText primary="Safety violation monitoring" secondary="PII detection, toxicity filtering, jailbreak prevention" />
            </ListItem>
            <ListItem>
              <ListItemIcon><AttachMoney /></ListItemIcon>
              <ListItemText primary="Cost tracking and management" secondary="Provider cost breakdown and budget monitoring" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle /></ListItemIcon>
              <ListItemText primary="System health monitoring" secondary="Component status and performance metrics" />
            </ListItem>
          </List>

          <Typography variant="h6" gutterBottom>Mock Data:</Typography>
          <Typography variant="body2" paragraph>
            • <strong>100+ LLM requests</strong> with realistic costs and timestamps<br/>
            • <strong>50+ safety violations</strong> with different types and severities<br/>
            • <strong>50+ users</strong> across various organizations and roles<br/>
            • <strong>20+ projects</strong> with budgets and spending data<br/>
            • <strong>Real-time updates</strong> every 30 seconds
          </Typography>

          <Alert severity="info">
            <Typography variant="body2">
              <strong>No external dependencies required!</strong> This demo runs entirely on mock data and can be used for demonstrations, development, and testing.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowMockInfo(false)} variant="contained">
            Got it!
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard;
