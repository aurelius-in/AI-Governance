/**
 * Mock API Server for AI Governance Dashboard Demo
 * 
 * I created this server to provide realistic API endpoints that serve mock data
 * from CSV files, simulating the behavior of the real backend without requiring
 * any external dependencies like databases or external APIs.
 * 
 * Key Features:
 * - Serves data from CSV files for realistic datasets
 * - Simulates API delays and error conditions
 * - Provides filtering and pagination
 * - Implements realistic response formats
 * - Supports real-time data updates
 * 
 * Author: Oliver Ellison
 * Created: 2024
 */

const express = require('express');
const cors = require('cors');
const csv = require('csv-parser');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3001;

// I configure middleware for realistic API behavior
app.use(cors());
app.use(express.json());

// I add request logging for debugging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// I create a data store to hold parsed CSV data
const dataStore = {
  requests: [],
  violations: [],
  users: [],
  projects: [],
  costBreakdown: [],
  systemHealth: []
};

// I load all CSV data on startup
function loadCSVData() {
  const csvFiles = [
    { name: 'requests', file: 'requests.csv' },
    { name: 'violations', file: 'violations.csv' },
    { name: 'users', file: 'users.csv' },
    { name: 'projects', file: 'projects.csv' },
    { name: 'costBreakdown', file: 'cost-breakdown.csv' },
    { name: 'systemHealth', file: 'system-health.csv' }
  ];

  csvFiles.forEach(({ name, file }) => {
    const results = [];
    fs.createReadStream(path.join(__dirname, '../mock-data', file))
      .pipe(csv())
      .on('data', (data) => results.push(data))
      .on('end', () => {
        dataStore[name] = results;
        console.log(`Loaded ${results.length} records from ${file}`);
      });
  });
}

// I implement realistic API delay simulation
function simulateDelay(min = 50, max = 300) {
  return new Promise(resolve => {
    setTimeout(resolve, Math.random() * (max - min) + min);
  });
}

// I implement error simulation for testing
function simulateError(probability = 0.05) {
  if (Math.random() < probability) {
    throw new Error('Simulated API error for testing');
  }
}

// I create helper functions for data processing
function filterByTimeRange(data, timeRange = '24h') {
  const now = new Date();
  let cutoff;
  
  switch (timeRange) {
    case '1h':
      cutoff = new Date(now.getTime() - 60 * 60 * 1000);
      break;
    case '24h':
      cutoff = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      break;
    case '7d':
      cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      break;
    case '30d':
      cutoff = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      break;
    default:
      cutoff = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  }
  
  return data.filter(item => new Date(item.timestamp) >= cutoff);
}

function paginateData(data, page = 1, limit = 20) {
  const start = (page - 1) * limit;
  const end = start + limit;
  return {
    data: data.slice(start, end),
    pagination: {
      page,
      limit,
      total: data.length,
      pages: Math.ceil(data.length / limit)
    }
  };
}

// I implement the metrics endpoint
app.get('/api/v1/metrics', async (req, res) => {
  try {
    await simulateDelay();
    simulateError();
    
    // I use all requests for demo purposes since the timestamps are from 2024
    const allRequests = dataStore.requests;
    
    // I add debugging to see what's happening
    console.log('DataStore requests length:', dataStore.requests.length);
    console.log('DataStore violations length:', dataStore.violations.length);
    console.log('DataStore users length:', dataStore.users.length);
    
    // I calculate realistic metrics
    const totalRequests = allRequests.length;
    const totalCost = allRequests.reduce((sum, req) => sum + parseFloat(req.total_cost || 0), 0);
    const totalTokens = allRequests.reduce((sum, req) => sum + parseInt(req.prompt_tokens || 0) + parseInt(req.completion_tokens || 0), 0);
    
    // I calculate change percentages (simulated)
    const changePercentages = {
      requests: Math.random() * 20 - 10, // -10% to +10%
      cost: Math.random() * 15 - 5,      // -5% to +10%
      violations: Math.random() * 30 - 15, // -15% to +15%
      users: Math.random() * 25 - 10     // -10% to +15%
    };
    
         const metrics = [
       {
         id: 'total-requests',
         title: 'Total Requests',
         value: '1,247',
         change: changePercentages.requests,
         changeType: changePercentages.requests > 0 ? 'increase' : 'decrease',
         icon: 'Timeline',
         color: '#1976d2',
         trend: generateTrendData(1247, 6),
         description: `Total LLM requests processed in the last ${req.query.timeRange || '24h'}`
       },
       {
         id: 'total-cost',
         title: 'Total Cost',
         value: '$156.78',
         change: changePercentages.cost,
         changeType: changePercentages.cost > 0 ? 'increase' : 'decrease',
         icon: 'AttachMoney',
         color: '#2e7d32',
         trend: generateTrendData(15678, 6),
         description: 'Total cost incurred from LLM usage'
       },
       {
         id: 'policy-violations',
         title: 'Policy Violations',
         value: '12',
         change: changePercentages.violations,
         changeType: changePercentages.violations > 0 ? 'increase' : 'decrease',
         icon: 'Warning',
         color: '#ed6c02',
         trend: generateTrendData(12, 6),
         description: 'Number of safety policy violations detected'
       },
       {
         id: 'active-users',
         title: 'Active Users',
         value: '45',
         change: changePercentages.users,
         changeType: changePercentages.users > 0 ? 'increase' : 'decrease',
         icon: 'People',
         color: '#0288d1',
         trend: generateTrendData(45, 6),
         description: 'Number of active users in the last hour'
       }
     ];
    
    res.json(metrics);
  } catch (error) {
    console.error('Error in metrics endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// I implement the violations endpoint
app.get('/api/v1/violations', async (req, res) => {
  try {
    await simulateDelay();
    simulateError();
    
    const { page = 1, limit = 20, severity, type, resolved } = req.query;
    let filteredViolations = [...dataStore.violations];
    
    // I apply filters
    if (severity) {
      filteredViolations = filteredViolations.filter(v => v.severity === severity);
    }
    if (type) {
      filteredViolations = filteredViolations.filter(v => v.type === type);
    }
    if (resolved !== undefined) {
      filteredViolations = filteredViolations.filter(v => v.resolved === resolved);
    }
    
    // I sort by timestamp (newest first)
    filteredViolations.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    const result = paginateData(filteredViolations, parseInt(page), parseInt(limit));
    
    res.json(result);
  } catch (error) {
    console.error('Error in violations endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// I implement the cost breakdown endpoint
app.get('/api/v1/cost/breakdown', async (req, res) => {
  try {
    await simulateDelay();
    simulateError();
    
    const timeRange = req.query.timeRange || '24h';
    const filteredRequests = filterByTimeRange(dataStore.requests, timeRange);
    
    // I aggregate costs by provider
    const providerCosts = {};
    filteredRequests.forEach(request => {
      const provider = request.provider;
      const cost = parseFloat(request.total_cost);
      
      if (!providerCosts[provider]) {
        providerCosts[provider] = { cost: 0, requests: 0 };
      }
      
      providerCosts[provider].cost += cost;
      providerCosts[provider].requests += 1;
    });
    
    const totalCost = Object.values(providerCosts).reduce((sum, p) => sum + p.cost, 0);
    
    const breakdown = Object.entries(providerCosts).map(([provider, data]) => ({
      provider: provider.charAt(0).toUpperCase() + provider.slice(1),
      cost: data.cost,
      percentage: totalCost > 0 ? (data.cost / totalCost) * 100 : 0,
      requests: data.requests,
      color: getProviderColor(provider)
    }));
    
    res.json(breakdown);
  } catch (error) {
    console.error('Error in cost breakdown endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// I implement the health endpoint
app.get('/api/v1/health', async (req, res) => {
  try {
    await simulateDelay(20, 50);
    
    const health = dataStore.systemHealth.map(component => ({
      component: component.component,
      status: component.status,
      uptime: parseFloat(component.uptime),
      responseTime: parseInt(component.response_time),
      lastCheck: component.last_check,
      version: component.version,
      loadAverage: parseFloat(component.load_average),
      memoryUsage: parseFloat(component.memory_usage),
      diskUsage: parseFloat(component.disk_usage)
    }));
    
    res.json(health);
  } catch (error) {
    console.error('Error in health endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// I implement the requests endpoint
app.get('/api/v1/requests', async (req, res) => {
  try {
    await simulateDelay();
    simulateError();
    
    const { page = 1, limit = 20, provider, model, status } = req.query;
    let filteredRequests = [...dataStore.requests];
    
    // I apply filters
    if (provider) {
      filteredRequests = filteredRequests.filter(r => r.provider === provider);
    }
    if (model) {
      filteredRequests = filteredRequests.filter(r => r.model === model);
    }
    if (status) {
      filteredRequests = filteredRequests.filter(r => r.status === status);
    }
    
    // I sort by timestamp (newest first)
    filteredRequests.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    const result = paginateData(filteredRequests, parseInt(page), parseInt(limit));
    
    res.json(result);
  } catch (error) {
    console.error('Error in requests endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// I implement the users endpoint
app.get('/api/v1/users', async (req, res) => {
  try {
    await simulateDelay();
    simulateError();
    
    const { page = 1, limit = 20, role, organization } = req.query;
    let filteredUsers = [...dataStore.users];
    
    // I apply filters
    if (role) {
      filteredUsers = filteredUsers.filter(u => u.role === role);
    }
    if (organization) {
      filteredUsers = filteredUsers.filter(u => u.organization === organization);
    }
    
    const result = paginateData(filteredUsers, parseInt(page), parseInt(limit));
    
    res.json(result);
  } catch (error) {
    console.error('Error in users endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// I implement the projects endpoint
app.get('/api/v1/projects', async (req, res) => {
  try {
    await simulateDelay();
    simulateError();
    
    const { page = 1, limit = 20, status, organization } = req.query;
    let filteredProjects = [...dataStore.projects];
    
    // I apply filters
    if (status) {
      filteredProjects = filteredProjects.filter(p => p.status === status);
    }
    if (organization) {
      filteredProjects = filteredProjects.filter(p => p.organization === organization);
    }
    
    const result = paginateData(filteredProjects, parseInt(page), parseInt(limit));
    
    res.json(result);
  } catch (error) {
    console.error('Error in projects endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// I implement the providers endpoint
app.get('/api/v1/providers', async (req, res) => {
  try {
    await simulateDelay();
    simulateError();
    
    const providers = [
      {
        name: 'OpenAI',
        status: 'healthy',
        models: ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'],
        rateLimit: '3000 requests/minute',
        costPer1kTokens: { 'gpt-4': 0.03, 'gpt-3.5-turbo': 0.002 }
      },
      {
        name: 'Anthropic',
        status: 'healthy',
        models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
        rateLimit: '5000 requests/minute',
        costPer1kTokens: { 'claude-3-opus': 0.015, 'claude-3-sonnet': 0.003 }
      },
      {
        name: 'Google',
        status: 'healthy',
        models: ['gemini-pro', 'gemini-ultra'],
        rateLimit: '15000 requests/minute',
        costPer1kTokens: { 'gemini-pro': 0.0005, 'gemini-ultra': 0.005 }
      }
    ];
    
    res.json(providers);
  } catch (error) {
    console.error('Error in providers endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// I implement the models endpoint
app.get('/api/v1/models', async (req, res) => {
  try {
    await simulateDelay();
    simulateError();
    
    const models = [
      {
        name: 'gpt-4',
        provider: 'OpenAI',
        contextLength: 8192,
        costPer1kTokens: 0.03,
        capabilities: ['chat', 'completion', 'function-calling'],
        recommended: true
      },
      {
        name: 'gpt-3.5-turbo',
        provider: 'OpenAI',
        contextLength: 4096,
        costPer1kTokens: 0.002,
        capabilities: ['chat', 'completion'],
        recommended: false
      },
      {
        name: 'claude-3-opus',
        provider: 'Anthropic',
        contextLength: 200000,
        costPer1kTokens: 0.015,
        capabilities: ['chat', 'completion', 'vision'],
        recommended: true
      },
      {
        name: 'claude-3-sonnet',
        provider: 'Anthropic',
        contextLength: 200000,
        costPer1kTokens: 0.003,
        capabilities: ['chat', 'completion', 'vision'],
        recommended: false
      },
      {
        name: 'gemini-pro',
        provider: 'Google',
        contextLength: 32768,
        costPer1kTokens: 0.0005,
        capabilities: ['chat', 'completion'],
        recommended: false
      }
    ];
    
    res.json(models);
  } catch (error) {
    console.error('Error in models endpoint:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// I implement helper functions
function generateTrendData(currentValue, points) {
  const trend = [];
  const baseValue = currentValue * 0.8; // Start at 80% of current value
  
  for (let i = 0; i < points; i++) {
    const time = new Date();
    time.setHours(time.getHours() - (points - i) * 4); // Every 4 hours
    
    const value = baseValue + (currentValue - baseValue) * (i / points) + Math.random() * currentValue * 0.1;
    
    trend.push({
      date: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      value: Math.round(value)
    });
  }
  
  return trend;
}

function getProviderColor(provider) {
  const colors = {
    openai: '#10a37f',
    anthropic: '#d97706',
    google: '#4285f4',
    azure: '#0078d4',
    cohere: '#ff6b6b',
    mistral: '#6366f1'
  };
  
  return colors[provider] || '#6b7280';
}

// I implement a simple health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// I start the server
app.listen(PORT, () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
  console.log('Loading CSV data...');
  loadCSVData();
});

module.exports = app;
