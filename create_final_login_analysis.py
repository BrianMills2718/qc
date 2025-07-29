#!/usr/bin/env python3
"""
Create final analysis with fake login page and complete theme-quote linking
"""

import re

def add_login_to_complete_analysis():
    """Add fake login page to the complete theme-quote analysis"""
    
    # Read the complete analysis
    with open('complete_theme_quote_analysis.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the title
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1) if title_match else "Complete Theme-Quote Analysis"
    
    # Update the title to include RAND branding
    content = re.sub(r'<title>.*?</title>', '<title>RAND Corporation - Secure Research Portal</title>', content)
    
    # Add login page styles to the existing CSS
    login_styles = """
        /* Login Page Styles */
        .login-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }

        .login-logo {
            width: 120px;
            height: 60px;
            background: var(--primary);
            border-radius: 8px;
            margin: 0 auto 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
        }

        .login-title {
            color: var(--dark);
            margin-bottom: 10px;
            font-size: 24px;
        }

        .login-subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: var(--dark);
        }

        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid var(--border);
            border-radius: 6px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        .form-group input:focus {
            outline: none;
            border-color: var(--primary);
        }

        .login-btn {
            width: 100%;
            padding: 12px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.3s;
        }

        .login-btn:hover {
            background: #1d4ed8;
        }

        .login-footer {
            margin-top: 20px;
            font-size: 12px;
            color: #666;
        }

        .demo-note {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            padding: 10px;
            margin-top: 15px;
            font-size: 12px;
            color: #1e40af;
        }

        /* Main Application Styles (hidden initially) */
        .main-app {
            display: none;
        }

        /* Logout Button */
        .logout-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--danger);
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            z-index: 1000;
        }

        .logout-btn:hover {
            background: #dc2626;
        }
    """
    
    # Add login styles before the closing </style> tag
    content = content.replace('</style>', login_styles + '\n    </style>')
    
    # Wrap the existing body content in main-app div
    body_start = content.find('<body>')
    body_end = content.find('</body>')
    
    if body_start != -1 and body_end != -1:
        existing_body = content[body_start + 6:body_end]
        
        login_html = '''
    <!-- Login Page -->
    <div id="loginPage" class="login-container">
        <div class="login-box">
            <div class="login-logo">
                <i class="fas fa-shield-alt"></i>
            </div>
            <h2 class="login-title">RAND Corporation</h2>
            <p class="login-subtitle">Secure Research Portal - Complete Theme-Quote Analysis</p>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="login-btn">
                    <i class="fas fa-sign-in-alt"></i> Sign In
                </button>
            </form>
            
            <div class="demo-note">
                <i class="fas fa-info-circle"></i>
                <strong>Demo Access:</strong> Any username/password combination will work for this demonstration.
            </div>
            
            <div class="login-footer">
                © 2025 RAND Corporation. All rights reserved.<br>
                Secure research data portal - Authorized users only
            </div>
        </div>
    </div>

    <!-- Main Application (Hidden Initially) -->
    <div id="mainApp" class="main-app">
        <button id="logoutBtn" class="logout-btn">
            <i class="fas fa-sign-out-alt"></i> Logout
        </button>
''' + existing_body + '''
    </div>'''
        
        # Replace the body content
        new_content = content[:body_start + 6] + login_html + content[body_end:]
        content = new_content
    
    # Add login/logout JavaScript before closing </script> tag
    login_js = '''
        // Login functionality
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            // Hide login page and show main app
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('mainApp').style.display = 'block';
        });

        // Logout functionality
        document.getElementById('logoutBtn').addEventListener('click', function() {
            document.getElementById('loginPage').style.display = 'flex';
            document.getElementById('mainApp').style.display = 'none';
        });

        '''
    
    # Add login JavaScript before the existing DOMContentLoaded event
    content = content.replace("document.addEventListener('DOMContentLoaded'", 
                             login_js + "\n        document.addEventListener('DOMContentLoaded'")
    
    # Write the final version
    with open('final_complete_analysis_with_login.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Generated final complete analysis with login: final_complete_analysis_with_login.html")
    print("Features:")
    print("- Fake RAND Corporation login page")
    print("- ALL 5 themes linked to quotes (21 total quotes)")
    print("- Exemplar quotes from theme analysis (T1, T2, T3)")
    print("- Formal extracted quotes (T4, T5)")
    print("- Interactive filtering and search")
    print("- Professional security appearance")

if __name__ == "__main__":
    add_login_to_complete_analysis()