// Simple dashboard.js with minimal functionality
console.log("Dashboard.js loaded");

// Function to load all dashboard data
function loadDashboardData() {
    console.log("Loading dashboard data...");
    
    // Show loading message
    document.getElementById('dashboard-container').innerHTML = `
        <div class="loading">Loading dashboard data...</div>
        
        <section id="summary-section" class="dashboard-section" style="display: none;">
            <h2>Dashboard Summary</h2>
            <div class="summary-cards">
                <div class="summary-card">
                    <h3>Total Screen Time</h3>
                    <p id="total-screen-time">0 min</p>
                </div>
                <div class="summary-card">
                    <h3>Productive Time</h3>
                    <p id="productive-time">0 min</p>
                </div>
                <div class="summary-card">
                    <h3>Active Alerts</h3>
                    <p id="active-alerts">0</p>
                </div>
            </div>
        </section>
        
        <section id="children-section" class="dashboard-section" style="display: none;">
            <h2>Children</h2>
            <div id="children-container" class="card-container">
                <!-- Children cards will be added here dynamically -->
            </div>
        </section>
        
        <section id="alerts-section" class="dashboard-section" style="display: none;">
            <h2>Alerts</h2>
            <div id="alerts-container" class="card-container">
                <!-- Alert cards will be added here dynamically -->
            </div>
        </section>
    `;
    
    // Load data from API endpoints
    Promise.all([
        fetch('/api/dashboard/summary').then(res => res.json()),
        fetch('/api/children').then(res => res.json()),
        fetch('/api/alerts').then(res => res.json())
    ])
    .then(([summaryData, childrenData, alertsData]) => {
        console.log("Data loaded successfully");
        console.log("Summary:", summaryData);
        console.log("Children:", childrenData);
        console.log("Alerts:", alertsData);
        
        // Update the dashboard with the data
        updateDashboard(summaryData, childrenData, alertsData);
    })
    .catch(error => {
        console.error("Error loading data:", error);
        document.getElementById('dashboard-container').innerHTML = `
            <div class="error">
                <h2>Error Loading Dashboard</h2>
                <p>${error.message}</p>
                <button onclick="loadDashboardData()">Retry</button>
            </div>
        `;
    });
}

// Function to update the dashboard with data
function updateDashboard(summary, children, alerts) {
    // Show all sections
    document.getElementById('summary-section').style.display = 'block';
    document.getElementById('children-section').style.display = 'block';
    document.getElementById('alerts-section').style.display = 'block';
    
    // Update summary
    document.getElementById('total-screen-time').textContent = `${summary.total_screen_time || 0} min`;
    document.getElementById('productive-time').textContent = `${summary.productive_time || 0} min`;
    document.getElementById('active-alerts').textContent = summary.active_alerts || 0;
    
    // Update children
    const childrenContainer = document.getElementById('children-container');
    childrenContainer.innerHTML = '';
    
    if (children.length === 0) {
        childrenContainer.innerHTML = '<p>No children found.</p>';
    } else {
        children.forEach(child => {
            const childCard = document.createElement('div');
            childCard.className = 'child-card';
            
            // Create session info
            let sessionInfo = '<p>Current Session: None</p>';
            if (child.current_session && child.current_session.app) {
                sessionInfo = `<p>Current Session: ${child.current_session.app} (${child.current_session.duration} min)</p>`;
            }
            
            childCard.innerHTML = `
                <h3>${child.name || 'Unknown'}</h3>
                <div class="status ${(child.status || 'unknown').toLowerCase()}">${child.status || 'Unknown'}</div>
                <p>Age: ${child.age || 'N/A'}</p>
                <p>Device: ${child.device_type || 'N/A'}</p>
                <p>Current App: ${child.current_app || 'None'}</p>
                ${sessionInfo}
            `;
            
            childrenContainer.appendChild(childCard);
        });
    }
    
    // Update alerts
    const alertsContainer = document.getElementById('alerts-container');
    alertsContainer.innerHTML = '';
    
    if (alerts.length === 0) {
        alertsContainer.innerHTML = '<p>No active alerts.</p>';
    } else {
        alerts.forEach(alert => {
            const alertCard = document.createElement('div');
            alertCard.className = `alert-card ${(alert.severity || 'medium').toLowerCase()}`;
            
            alertCard.innerHTML = `
                <div class="alert-header">
                    <span class="severity">${(alert.severity || 'MEDIUM').toUpperCase()}</span>
                    <span class="timestamp">${alert.timestamp || 'Unknown time'}</span>
                </div>
                <p class="child-name">${alert.child_name || 'Unknown child'}</p>
                <p class="app-name">${alert.app_name || 'Unknown app'}</p>
                <p class="message">${alert.message || 'No details available'}</p>
                <button class="resolve-btn" data-alert-id="${alert.id || 0}">Resolve</button>
            `;
            
            alertsContainer.appendChild(alertCard);
        });
        
        // Add event listeners to resolve buttons
        document.querySelectorAll('.resolve-btn').forEach(button => {
            button.addEventListener('click', function() {
                const alertId = this.getAttribute('data-alert-id');
                resolveAlert(alertId);
            });
        });
    }
    
    // Hide loading message
    const loadingElement = document.querySelector('.loading');
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

// Function to resolve an alert
function resolveAlert(alertId) {
    console.log(`Resolving alert ${alertId}`);
    
    fetch(`/api/alerts/${alertId}/resolve`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('Alert resolved:', data);
        // Reload dashboard data
        loadDashboardData();
    })
    .catch(error => {
        console.error('Error resolving alert:', error);
        alert(`Failed to resolve alert: ${error.message}`);
    });
}

// Load dashboard data when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing dashboard...");
    loadDashboardData();
    
    // Set up refresh button
    const refreshButton = document.getElementById('refresh-btn');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            console.log("Refresh button clicked");
            loadDashboardData();
        });
    }
});
