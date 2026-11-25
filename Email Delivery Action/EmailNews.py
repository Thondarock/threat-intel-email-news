import feedparser
import google.generativeai as genai
import time
import os
import sys
import socket
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. CONFIGURATION
# ==========================================

# Secrets come from environment variables (see README / .env.example)
MY_SECRET_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")

# 📧 EMAIL SETTINGS
EMAIL_SETTINGS = {
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    "sender_email": os.environ.get("SENDER_EMAIL", ""),
    "sender_password": os.environ.get("SENDER_APP_PASSWORD", ""),  # Gmail 16-char app password
    "recipients": [r.strip() for r in os.environ.get("RECIPIENTS", "").split(",") if r.strip()],
    "subject_prefix": "🛡️ Daily Threat Intelligence Brief - "
}

# 🏢 ORG PROFILE
ORG_PROFILE = """
CONTEXT: US Healthcare & Insurance Organization (HIPAA/PHI Critical).
TECH STACK:
- Identity: Microsoft Entra ID (Critical), Active Directory.
- Cloud/SaaS: Microsoft 365 E5, Azure, AWS (Web/WAF), Salesforce.
- Endpoints: Windows 10/11, Microsoft Defender for Endpoint.
- Network: Cisco Firewalls, VPNs.
- Storage: SharePoint Online, Zoho Workdrive.
"""

# 📡 SOURCES
SOURCES = [
    "https://www.bleepingcomputer.com/feed/",
    "https://cybersecuritynews.com/feed/",
    "https://feeds.feedburner.com/TheHackersNews",
    "https://gbhackers.com/feed/",
    "https://www.securityweek.com/feed/"
]

socket.setdefaulttimeout(20)

# ==========================================
# 2. SYSTEM CHECKS
# ==========================================

def system_check():
    print("\n🔍 SYSTEM CHECK INITIATED...")
    if not MY_SECRET_KEY:
        sys.exit("❌ Set GOOGLE_AI_API_KEY first (see README).")
    try:
        genai.configure(api_key=MY_SECRET_KEY)
        
        # CHANGE THIS LINE: Use gemma-4-31b instead of gemma-4-34b-it
        model = genai.GenerativeModel('gemma-4-31b-it')
        
        print(f"    Connecting to Google AI...", end=" ")
        if model.generate_content("Hi").text:
            print("✅ ONLINE")
            return model
    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {e}")
        sys.exit()

# ==========================================
# 3. FILE NAMING LOGIC (NEW FEATURE)
# ==========================================
def get_unique_filename(base_name):
    """
    Checks if a file exists. If it does, adds _v1, _v2, etc.
    Returns a unique filename.
    """
    if not os.path.exists(base_name):
        return base_name
    
    filename, extension = os.path.splitext(base_name)
    counter = 1
    
    while True:
        new_name = f"{filename}_v{counter}{extension}"
        if not os.path.exists(new_name):
            return new_name
        counter += 1

# ==========================================
# 4. CORE LOGIC
# ==========================================
def analyze_threat(model, title, content):
    prompt = f"""
    You are a cyber security analyst preparing a daily cyber awareness summary.

    Analyze the article using simple and clear language.
    Do not use complex technical terms unless required.

    NEWS TITLE: {title}
    CONTENT Snippet: {content}

    TASK:
    Generate an HTML snippet (NO markdown, NO ``` blocks).
    You must use the exact headers and HTML structure below.
    Do not change or remove any HTML tags.

    Structure:
    <div class='risk-level'>LEVEL_HERE</div>
    
    <div class='section'>
        <h3>Summary of Article</h3>
        <ul>
            <li>3 to 4 short points explaining what the article is about.</li>
            <li>Explain what happened in simple language.</li>
            <li>Mention the reason or main detail.</li>
            <li>Mention the current status if available.</li>
        </ul>
    </div>

    <div class='section'>
        <h3>Impact</h3>
        <p>
        Write 2 to 3 short lines.
        Clearly state whether this article describes a direct attack, a product or server issue, or no direct security impact.
        If it is a service issue (for example Microsoft service disruption), state that clearly.
        If there is no direct risk, write "No direct impact to the organization."
        </p>
    </div>

    <div class='section'>
        <h3>Mitigation</h3>
        <ul class='mitigation-list'>
            <li>2 to 3 simple and practical actions based only on the article.</li>
            <li>If no action is required, clearly say "No immediate action required."</li>
        </ul>
    </div>

    RULES:
    - LEVEL_HERE must be one of: CRITICAL, HIGH, MEDIUM, or LOW.
    - CRITICAL: Active attack or confirmed exploitation.
    - MEDIUM: Known issue, vulnerability, or service problem.
    - LOW: No attack, informational update, or general awareness.
    - Do not exaggerate risk.
    - Do not assume attacks if not mentioned.
    - Avoid naming threat actors or countries unless clearly stated.
    - Keep sentences short, clear, and easy to read.
    """
    
    try:
        time.sleep(1.5)
        response = model.generate_content(prompt)
        return response.text.replace("```html", "").replace("```", "").strip()
    except:
        return "<p style='color:red'>⚠️ Analysis Failed</p>"

# ==========================================
# 5. EMAIL FUNCTION
# ==========================================
def send_email_report(html_content, date_str):
    print("\n📧 CONNECTING TO MAIL SERVER...")
    
    msg = MIMEMultipart('related')
    msg['Subject'] = f"{EMAIL_SETTINGS['subject_prefix']} {date_str}"
    msg['From'] = f"SOC Intel Bot <{EMAIL_SETTINGS['sender_email']}>"
    msg['To'] = ", ".join(EMAIL_SETTINGS['recipients'])

    body = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(body)

    try:
        server = smtplib.SMTP(EMAIL_SETTINGS['smtp_server'], EMAIL_SETTINGS['smtp_port'])
        server.starttls()
        server.login(EMAIL_SETTINGS['sender_email'], EMAIL_SETTINGS['sender_password'])
        server.sendmail(EMAIL_SETTINGS['sender_email'], EMAIL_SETTINGS['recipients'], msg.as_string())
        server.quit()
        print(f"✅ EMAIL SENT SUCCESSFULLY to: {len(EMAIL_SETTINGS['recipients'])} recipients.")
    except Exception as e:
        print(f"❌ EMAIL FAILED: {e}")

# ==========================================
# 6. DASHBOARD STYLING
# ==========================================
def get_html_header(date_str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; }}
            .container {{ max_width: 800px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ background-color: #0f172a; color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
            .header p {{ color: #94a3b8; margin: 5px 0 0 0; font-size: 14px; }}
            
            .card {{ background-color: #ffffff; padding: 25px; margin: 20px; border: 1px solid #e2e8f0; border-left-width: 6px; border-radius: 4px; }}
            .card.CRITICAL {{ border-left-color: #dc2626; }}
            .card.HIGH {{ border-left-color: #ea580c; }}
            .card.MEDIUM {{ border-left-color: #ca8a04; }}
            .card.LOW {{ border-left-color: #16a34a; }}
            
            .news-title {{ font-size: 18px; font-weight: 700; color: #1e293b; text-decoration: none; display: block; margin-bottom: 5px; }}
            .read-more {{ font-size: 12px; font-weight: 600; color: #2563eb; text-decoration: none; display: inline-block; margin-bottom: 15px; border-bottom: 1px dotted #2563eb; }}
            .risk-badge {{ float: right; font-size: 11px; font-weight: 800; background-color: #f1f5f9; padding: 4px 8px; border-radius: 4px; color: #475569; text-transform: uppercase; border: 1px solid #cbd5e1; }}
            
            h3 {{ font-size: 12px; color: #475569; margin-top: 20px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 800; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }}
            
            ul {{ padding-left: 20px; margin: 0; }}
            li {{ font-size: 14px; color: #334155; margin-bottom: 6px; line-height: 1.5; }}
            p {{ font-size: 14px; color: #334155; margin: 0; line-height: 1.5; }}
            .mitigation-list li {{ color: #0f766e; font-weight: 600; }}
            
            .footer {{ text-align: center; font-size: 12px; color: #94a3b8; padding: 20px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Daily Threat Intelligence Brief</h1>
                <p>{date_str} • US Healthcare Sector • Microsoft E5</p>
            </div>
    """

def get_html_footer():
    return """<div class="footer"> SOC Analyst • Powered by Google Gemma 3</div></div></body></html>"""

# ==========================================
# 7. MAIN EXECUTION
# ==========================================
def generate_report():
    model = system_check()
    today = datetime.now(timezone.utc).date()
    print(f"--- 🛡️  STARTING SCAN FOR: {today} ---")
    
    html_content = get_html_header(str(today))
    stats = {"relevant": 0}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    seen_titles = set()

    for url in SOURCES:
        try:
            feed = feedparser.parse(url, agent=headers['User-Agent'])
            if not feed.entries: continue
            
            print(f"📡 Scanning: {feed.feed.get('title', url)[:20]}...")
            for entry in feed.entries:
                if entry.title in seen_titles: continue
                seen_titles.add(entry.title)

                pub = entry.get('published_parsed')
                if pub:
                    date = datetime(*pub[:6], tzinfo=timezone.utc).date()
                    if date == today:
                        print(f"  -> Found: {entry.title[:35]}...")
                        
                        raw_html = analyze_threat(model, entry.title, entry.get('summary', '')[:2500])
                        
                        risk = "MEDIUM"
                        if "CRITICAL" in raw_html: risk = "CRITICAL"
                        elif "HIGH" in raw_html: risk = "HIGH"
                        elif "LOW" in raw_html: risk = "LOW"
                        
                        clean_body = raw_html.replace(f"<div class='risk-level'>{risk}</div>", "")
                        
                        card = f"""
                        <div class="card {risk}">
                            <span class="risk-badge">{risk}</span>
                            <a href="{entry.link}" target="_blank" class="news-title">{entry.title}</a>
                            <a href="{entry.link}" target="_blank" class="read-more">Read Full Article →</a>
                            {clean_body}
                        </div>
                        """
                        html_content += card
                        stats["relevant"] += 1
        except Exception:
            continue

    html_content += get_html_footer()
    
    if stats['relevant'] > 0:
        # 1. Generate Unique Filename
        base_filename = f"SOC_Brief_{today}.html"
        final_filename = get_unique_filename(base_filename)
        
        # 2. Save File
        with open(final_filename, "w", encoding='utf-8') as f: f.write(html_content)
        
        print("\n" + "="*45)
        print(f"✅ REPORT READY: {final_filename}")
        print(f"📊 Threats Found: {stats['relevant']}")
        print("="*45)
        
        print(f"\n❓ Send to email recipients?")
        if input("👉 Type 'yes' to send: ").strip().lower() in ['yes', 'y']:
            send_email_report(html_content, str(today))
        else:
            print("❌ Email cancelled.")
            
    else:
        print("\n✅ Clean Sweep: No high-priority threats found today.")

if __name__ == "__main__":
    generate_report()