# 🚀 AI Governance Dashboard - Mock Demo Version

## 🎯 **What This Is**

I created this standalone mock demo version to showcase the AI Governance Dashboard UI and features **without requiring any external dependencies** (databases, APIs, or external services). This allows you to see and interact with the platform immediately.

## 🔍 **Analysis: What Was Needed and Why**

### **Current App Dependencies:**
The original app requires:
- **PostgreSQL Database** (for user data, requests, projects)
- **Redis** (for caching and rate limiting)
- **OPA Policy Engine** (for governance rules)
- **OpenTelemetry Collector** (for tracing)
- **Jaeger** (for trace visualization)
- **Prometheus** (for metrics)
- **Grafana** (for dashboards)
- **LLM Provider APIs** (OpenAI, Anthropic, Google)

### **Why Mock Data Was Needed:**
1. **Demo Purposes**: To showcase the UI and features without complex setup
2. **No External Dependencies**: Can run on any machine without databases or APIs
3. **Realistic Data**: Large, realistic datasets to demonstrate all features
4. **Immediate Interaction**: No setup time, just run and explore

### **What I Created:**

#### **1. Mock Data Files (CSV Format)**
- **`mock-data/requests.csv`**: 1,000+ realistic LLM requests with timestamps, costs, providers
- **`mock-data/violations.csv`**: 200+ safety violations with different types and severities
- **`mock-data/users.csv`**: 50+ users with roles and organizations
- **`mock-data/projects.csv`**: 20+ projects with budgets and settings
- **`mock-data/cost-breakdown.csv`**: Provider cost data for charts
- **`mock-data/system-health.csv`**: Component health status data

#### **2. Mock API Service**
- **`mock-api/server.js`**: Express.js server that serves mock data
- **Realistic API endpoints** that match the original backend
- **Simulated delays** to mimic real API behavior
- **Error simulation** for testing error states

#### **3. Enhanced Frontend**
- **Modified Dashboard** to work with mock API
- **Real-time data updates** using mock data
- **Interactive features** that work with simulated data
- **Error handling** for demo scenarios

## 🚀 **Quick Start (No Dependencies Required)**

```bash
# 1. Navigate to mock demo
cd mock-demo

# 2. Install dependencies (only Node.js needed)
npm install

# 3. Start the mock API server
npm run mock-api

# 4. In another terminal, start the frontend
npm run dev

# 5. Open http://localhost:5173
```

## 📊 **Mock Data Structure**

### **Requests Data** (`mock-data/requests.csv`)
```csv
id,user_id,project_id,provider,model,request_type,prompt_tokens,completion_tokens,total_cost,status,duration_ms,timestamp,user_email,project_name
1,1,1,openai,gpt-4,chat,150,75,0.00675,completed,1250,2024-01-15T10:30:00Z,john.doe@company.com,AI Research Project
2,2,1,anthropic,claude-3-sonnet,chat,200,120,0.0048,completed,980,2024-01-15T10:32:00Z,jane.smith@company.com,AI Research Project
```

### **Violations Data** (`mock-data/violations.csv`)
```csv
id,type,severity,user_email,model,description,timestamp,resolved,risk_score
1,pii,high,john.doe@company.com,gpt-4,Email address detected in input,2024-01-15T10:30:00Z,false,0.85
2,toxicity,medium,jane.smith@company.com,claude-3-sonnet,Hate speech detected in output,2024-01-15T10:32:00Z,true,0.65
```

### **Users Data** (`mock-data/users.csv`)
```csv
id,email,username,role,organization,created_at,last_login
1,john.doe@company.com,john.doe,developer,Acme Corp,2024-01-01T00:00:00Z,2024-01-15T10:30:00Z
2,jane.smith@company.com,jane.smith,admin,Acme Corp,2024-01-01T00:00:00Z,2024-01-15T10:32:00Z
```

## 🎨 **Features Demonstrated**

### **Real-time Dashboard**
- **Live metrics** with auto-refreshing data
- **Interactive charts** with clickable elements
- **System health monitoring** with status indicators
- **Cost breakdown** by provider and model

### **Safety Monitoring**
- **Violation tracking** with severity levels
- **Real-time alerts** for safety issues
- **Resolution status** tracking
- **Risk score visualization**

### **Cost Management**
- **Spending analytics** with trend analysis
- **Budget tracking** with limit enforcement
- **Provider cost comparison**
- **User spending breakdowns**

### **User Management**
- **Role-based access** demonstration
- **Organization isolation**
- **User activity tracking**
- **Project management**

## 🔧 **Technical Implementation**

### **Mock API Server** (`mock-api/server.js`)
```javascript
// I created a realistic API server that serves mock data
const express = require('express');
const cors = require('cors');
const csv = require('csv-parser');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());

// I implemented realistic API endpoints
app.get('/api/v1/metrics', (req, res) => {
  // I serve processed metrics data
  res.json(generateMetrics());
});

app.get('/api/v1/violations', (req, res) => {
  // I serve safety violations with filtering
  res.json(generateViolations());
});
```

### **Data Processing**
- **CSV parsing** for easy data management
- **Realistic data generation** with proper relationships
- **Time-based filtering** for different time ranges
- **Aggregation functions** for metrics calculation

### **Frontend Integration**
- **Same UI components** as the real app
- **Mock API integration** with error handling
- **Real-time updates** using simulated data
- **Interactive features** that work with mock data

## 📈 **Data Volume and Realism**

### **Dataset Sizes:**
- **1,000+ LLM requests** over 30 days
- **200+ safety violations** with various types
- **50+ users** across 5 organizations
- **20+ projects** with different budgets
- **Realistic timestamps** and relationships

### **Data Realism:**
- **Realistic costs** based on actual LLM pricing
- **Proper relationships** between users, projects, and requests
- **Time-based patterns** (business hours, weekends)
- **Realistic violation types** (PII, toxicity, jailbreak attempts)
- **Varied user roles** and permissions

## 🎯 **Benefits of This Approach**

### **For Demo Purposes:**
1. **Immediate Setup**: No complex infrastructure needed
2. **Realistic Experience**: Large, realistic datasets
3. **Full Feature Demo**: All UI features work
4. **Interactive**: Users can explore and interact
5. **Portable**: Can run on any machine

### **For Development:**
1. **Frontend Testing**: Test UI without backend
2. **Data Visualization**: Test charts with real data
3. **User Experience**: Validate UX flows
4. **Performance**: Test with large datasets
5. **Offline Development**: Work without internet

## 🚀 **Next Steps**

### **To Use the Real App:**
1. Set up the full infrastructure (Docker Compose)
2. Configure external APIs (OpenAI, Anthropic, etc.)
3. Replace mock API with real backend
4. Connect to real databases

### **To Extend the Mock Demo:**
1. Add more mock data types
2. Implement more interactive features
3. Add simulated real-time updates
4. Create more realistic scenarios

---

**This mock demo provides a complete, interactive experience of the AI Governance Dashboard without any external dependencies, making it perfect for demonstrations, development, and testing.**
