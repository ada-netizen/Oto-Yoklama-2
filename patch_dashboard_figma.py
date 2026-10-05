import re

# 1. UPDATE index.html (Dashboard Styles)
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_dash_styles = '''<style>
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        .kpi-card { background: var(--bg-main); border-radius: var(--rounded-lg); padding: 20px; border: 2px solid var(--fg-main); display: flex; align-items: center; gap: 15px; box-shadow: 4px 4px 0px var(--fg-main); transition: transform 0.2s, box-shadow 0.2s; cursor: default; }
        .kpi-card:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0px var(--fg-main); }
        .kpi-icon { width: 56px; height: 56px; border-radius: var(--rounded-pill); display: flex; align-items: center; justify-content: center; font-size: 24px; color: var(--fg-main); border: 2px solid var(--fg-main); }
        .kpi-info h4 { margin: 0; font-size: 13px; color: var(--fg-main); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-info h2 { margin: 5px 0 0 0; font-size: 32px; color: var(--fg-main); font-weight: 800; line-height: 1; }
        
        .dash-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; margin-bottom: 30px; }
        .dash-card { background: var(--bg-main); border-radius: var(--rounded-lg); padding: 0; border: 2px solid var(--fg-main); box-shadow: 6px 6px 0px var(--fg-main); display: flex; flex-direction: column; overflow: hidden; }
        .dash-card.span-2 { grid-column: span 2; }
        .dash-card-header { display: flex; align-items: center; gap: 10px; border-bottom: 2px solid var(--fg-main); padding: 15px 20px; background-color: var(--block-cream); margin-bottom: 0; }
        .dash-card-header h3 { margin: 0; font-size: 16px; color: var(--fg-main); font-weight: 700; letter-spacing: -0.3px; }
        .dash-card-body { padding: 20px; flex: 1; display: flex; flex-direction: column; position: relative; }
        
        .modern-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
        .modern-table th { text-align: left; padding: 12px; color: var(--fg-main); border-bottom: 2px solid var(--fg-main); font-weight: 700; background-color: var(--bg-main); }
        .modern-table td { padding: 12px; color: var(--fg-main); border-bottom: 1px solid var(--border); font-weight: 500; }
        .modern-table tr:last-child td { border-bottom: none; }
        .modern-table tr:hover td { background-color: rgba(0,0,0,0.02); }
        
        .badge { padding: 4px 12px; border-radius: var(--rounded-pill); font-weight: 700; font-size: 11px; border: 1px solid var(--fg-main); color: var(--fg-main) !important; text-transform: uppercase; box-shadow: 2px 2px 0px var(--fg-main); }
        
        .top-bar-dashboard { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; background: var(--block-lilac); padding: 20px 25px; border-radius: var(--rounded-lg); border: 2px solid var(--fg-main); box-shadow: 4px 4px 0px var(--fg-main); }
    </style>'''

# Replace the existing dashboard style block
html = re.sub(r'<style>.*?\.top-bar-dashboard\s*\{.*?\}.*?</style>', new_dash_styles, html, flags=re.DOTALL)

# Wrap canvas/tables in .dash-card-body
html = html.replace('<div style="flex:1; position: relative;"><canvas', '<div class="dash-card-body"><canvas')
html = html.replace('</canvas></div>', '</canvas></div>') # Handled implicitly since closing tag is same, but let's do a more robust replace:
html = re.sub(r'<div style="flex:1; position: relative;">(.*?</canvas>)</div>', r'<div class="dash-card-body">\1</div>', html, flags=re.DOTALL)
html = re.sub(r'<table class="modern-table">(.*?)</table>', r'<div class="dash-card-body" style="padding:0; overflow-y:auto;"><table class="modern-table">\1</table></div>', html, flags=re.DOTALL)

# Add pastel block colors to specific card headers
html = html.replace('<div class="dash-card-header"><i data-lucide="trending-up" style="color: #3b82f6;"></i>', '<div class="dash-card-header" style="background-color: var(--block-mint);"><i data-lucide="trending-up" style="color: var(--fg-main);"></i>')
html = html.replace('<div class="dash-card-header"><i data-lucide="calendar" style="color: #f59e0b;"></i>', '<div class="dash-card-header" style="background-color: var(--block-cream);"><i data-lucide="calendar" style="color: var(--fg-main);"></i>')
html = html.replace('<div class="dash-card-header"><i data-lucide="pie-chart" style="color: #8b5cf6;"></i>', '<div class="dash-card-header" style="background-color: var(--block-lilac);"><i data-lucide="pie-chart" style="color: var(--fg-main);"></i>')
html = html.replace('<div class="dash-card-header"><i data-lucide="bar-chart" style="color: #10b981;"></i>', '<div class="dash-card-header" style="background-color: var(--block-lime);"><i data-lucide="bar-chart" style="color: var(--fg-main);"></i>')
html = html.replace('<div class="dash-card-header"><i data-lucide="users" style="color: #06b6d4;"></i>', '<div class="dash-card-header" style="background-color: var(--block-pink);"><i data-lucide="users" style="color: var(--fg-main);"></i>')

html = html.replace('<div class="dash-card-header"><i data-lucide="user-x" style="color: #ef4444;"></i> <h3 style="color: #ef4444;">', '<div class="dash-card-header" style="background-color: var(--block-pink);"><i data-lucide="user-x" style="color: var(--fg-main);"></i> <h3 style="color: var(--fg-main);">')
html = html.replace('<div class="dash-card-header"><i data-lucide="user-minus" style="color: #f59e0b;"></i>', '<div class="dash-card-header" style="background-color: var(--block-cream);"><i data-lucide="user-minus" style="color: var(--fg-main);"></i>')
html = html.replace('<div class="dash-card-header"><i data-lucide="briefcase" style="color: #3b82f6;"></i>', '<div class="dash-card-header" style="background-color: var(--block-mint);"><i data-lucide="briefcase" style="color: var(--fg-main);"></i>')

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. UPDATE dashboard.js (Colors & Borders)
with open('frontend/js/dashboard.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the renderChart function to enforce Figma brutalist chart styles
new_render_chart = '''function renderChart(canvasId, type, label, labels, data, colors, isDual = false, data2 = null, label2 = null, color2 = null) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    
    // Figma Pastel Palette
    const figmaPalette = ['#c7f284', '#e0c9fa', '#b2f5d1', '#fecaca', '#fef9c3'];
    
    let datasets = [{
        label: label,
        data: data,
        backgroundColor: type === 'line' ? 'rgba(199, 242, 132, 0.5)' : (colors || figmaPalette),
        borderColor: '#000000',
        borderWidth: 2,
        tension: 0, // Sharp lines for brutalist feel
        fill: type === 'line' ? true : false,
        pointBackgroundColor: '#000000',
        pointBorderColor: '#000000',
        pointRadius: type === 'line' ? 4 : 0,
        pointHoverRadius: 6
    }];

    if(isDual && data2) {
        datasets.push({
            label: label2,
            data: data2,
            backgroundColor: 'rgba(224, 201, 250, 0.5)',
            borderColor: '#000000',
            borderWidth: 2,
            tension: 0,
            fill: true,
            pointBackgroundColor: '#000000',
            pointRadius: 4,
            pointHoverRadius: 6
        });
    }
    
    charts[canvasId] = new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: type === 'pie' || type === 'doughnut' ? 'right' : 'top',
                    labels: { color: '#000000', font: { family: 'Inter, sans-serif', weight: 'bold', size: 11 }, usePointStyle: true, pointStyle: 'rectRounded' }
                },
                tooltip: {
                    backgroundColor: '#000000',
                    titleFont: { family: 'Inter, sans-serif', size: 13 },
                    bodyFont: { family: 'Inter, sans-serif', size: 12 },
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: false
                }
            },
            scales: (type === 'pie' || type === 'doughnut' || type === 'radar') ? {} : {
                x: { 
                    ticks: { color: '#000000', font: { family: 'Inter, sans-serif', weight: '600' } }, 
                    grid: { color: '#e5e5e5', tickLength: 5, drawBorder: true, borderColor: '#000000', borderWidth: 2 } 
                },
                y: { 
                    ticks: { color: '#000000', font: { family: 'Inter, sans-serif', weight: '600' } }, 
                    grid: { color: '#e5e5e5', tickLength: 5, drawBorder: true, borderColor: '#000000', borderWidth: 2 } 
                }
            }
        }
    });
}'''

js = re.sub(r'function renderChart\(.*?options: \{.*?\}\s*\}\);\s*\}', new_render_chart, js, flags=re.DOTALL)

# Also fix the innerHTML of badges to use correct Figma variables (e.g. var(--block-pink))
js = js.replace('background: #fef3c7; color: #d97706;', 'background: var(--block-cream);')
js = js.replace('background: #fee2e2; color: #b91c1c;', 'background: var(--block-pink);')
js = js.replace('background: #dbeafe; color: #1d4ed8;', 'background: var(--block-mint);')

with open('frontend/js/dashboard.js', 'w', encoding='utf-8') as f:
    f.write(js)
