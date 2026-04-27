import streamlit as st
import anthropic
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))

st.set_page_config(page_title="Scoutreach", page_icon="✉️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: #D2B48C !important; }
    .block-container { max-width: 100% !important; padding: 4rem 6rem !important; }
    .hero { text-align: center; padding: 4rem 0 3rem 0; }
    .hero-title { font-size: 5rem; font-weight: 900; color: #1a1a1a; letter-spacing: -3px; line-height: 1; }
    .hero-sub { font-size: 1.4rem; color: #1a1a1a; margin-top: 1rem; font-weight: 400; }
    .step-label { font-size: 0.7rem; font-weight: 800; color: #1a1a1a; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 0.3rem; }
    h2 { font-size: 1.8rem !important; font-weight: 800 !important; color: #1a1a1a !important; letter-spacing: -0.5px !important; }
    p, label, caption { color: #1a1a1a !important; }
    .stTextInput input, .stTextArea textarea { border: 2px solid #1a1a1a !important; border-radius: 12px !important; font-size: 1rem !important; padding: 0.8rem !important; background: #ffffff !important; color: #1a1a1a !important; }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #999999 !important; }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color: #1a1a1a !important; background: #ffffff !important; box-shadow: 0 0 0 3px rgba(0,0,0,0.1) !important; }
    .stTextInput label, .stTextArea label { color: #1a1a1a !important; font-weight: 700 !important; font-size: 0.95rem !important; }
    .stButton button { background: #1a1a1a !important; color: #ffffff !important; border-radius: 12px !important; padding: 0.8rem 2rem !important; font-weight: 800 !important; font-size: 1.1rem !important; border: none !important; width: 100% !important; box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important; }
    .stButton button p { color: #ffffff !important; font-weight: 800 !important; }
    .stButton button:hover { background: #333333 !important; box-shadow: 0 8px 30px rgba(0,0,0,0.3) !important; }
    .stDownloadButton button { background: #ffffff !important; color: #1a1a1a !important; border: 2px solid #1a1a1a !important; border-radius: 12px !important; font-weight: 700 !important; }
    .stDownloadButton button p { color: #1a1a1a !important; font-weight: 700 !important; }
    .stAlert { border-radius: 12px !important; background: #ffffff !important; border: 2px solid #1a1a1a !important; color: #1a1a1a !important; }
    .stSuccess { background: #ffffff !important; color: #1a1a1a !important; border: 2px solid #1a1a1a !important; border-radius: 12px !important; }
    .stError { background: #ffffff !important; color: #1a1a1a !important; border: 2px solid #1a1a1a !important; border-radius: 12px !important; }
    .stProgress > div > div { background: #1a1a1a !important; border-radius: 99px !important; }
    div[data-testid="metric-container"] { background: #ffffff !important; border-radius: 16px !important; padding: 1.5rem !important; border: 2px solid #1a1a1a !important; text-align: center !important; }
    div[data-testid="metric-container"] label { color: #1a1a1a !important; font-size: 0.85rem !important; font-weight: 700 !important; }
    div[data-testid="metric-container"] div { color: #1a1a1a !important; font-size: 2rem !important; font-weight: 800 !important; }
    hr { border: none !important; border-top: 2px solid rgba(0,0,0,0.15) !important; margin: 3rem 0 !important; }
    .stFileUploader { border: 2px dashed #1a1a1a !important; border-radius: 16px !important; padding: 2rem !important; background: #ffffff !important; }
    .stFileUploader label { color: #1a1a1a !important; font-weight: 700 !important; }
    .stDataFrame { border-radius: 12px !important; border: 2px solid #1a1a1a !important; }
</style>
""", unsafe_allow_html=True)

# ── FUNCTIONS ────────────────────────────────────────────
def send_email(gmail_user, gmail_password, to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"]    = gmail_user
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        return str(e)

def research_company(company_name):
    try:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=300,
            messages=[{"role": "user", "content": f"""
Research this company and give me:
1. What they do (1 sentence)
2. Their likely pain points (2 bullet points)
3. Why a SaaS tool would help them (1 sentence)
Company: {company_name}
Keep it under 100 words total.
"""}]
        )
        return response.content[0].text
    except:
        return f"{company_name} is a business that could benefit from automation and efficiency tools."

def write_email(recipient_name, company_name, company_research,
                saas_name, saas_description, saas_target, saas_benefits, sender_name):
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=500,
        messages=[{"role": "user", "content": f"""
Write a cold email from a SaaS company to a potential customer.

SENDER'S PRODUCT:
- Name: {saas_name}
- What it does: {saas_description}
- Who it's for: {saas_target}
- Why it's great: {saas_benefits}

RECIPIENT:
- Name: {recipient_name}
- Company: {company_name}
- Research: {company_research}

Rules:
- Subject line first (start with "Subject: ") — must be 3 words max, title case, professional
- Then blank line
- Then email body
- Always start with "Good afternoon {recipient_name}, I hope you're having a great day!"
- Max 70 words total including greeting and sign off
- Correct punctuation and grammar throughout
- Sound like a real human, not a robot
- Reference something specific about their company
- One clear call to action (book a 15 min call)
- Short and concise — no fluff, no buzzwords
- Professional but warm tone
- Always end with "Best," on one line then "{sender_name}" on the next line
- Never write "Your Name" or any placeholder anywhere
"""}]
    )
    return response.content[0].text

# ── HEADER ───────────────────────────────────────────────
st.markdown("""
<div class='hero'>
    <div class='hero-title'>✉️ Scoutreach</div>
    <div class='hero-sub'>AI-powered cold emails that actually get replies.</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── STEP 1 ───────────────────────────────────────────────
st.markdown("<div class='step-label'>Step 1 — Your Product</div>", unsafe_allow_html=True)
st.markdown("## Tell us about your product")

col1, col2 = st.columns(2)
with col1:
    saas_name        = st.text_input("Product name",    placeholder="e.g. SalesFlow")
    saas_description = st.text_area("What does it do?", placeholder="e.g. Automates lead generation using AI", height=100)
with col2:
    saas_target   = st.text_input("Who is it for?",  placeholder="e.g. B2B sales teams")
    saas_benefits = st.text_area("Why is it great?", placeholder="e.g. Saves 10 hours/week, 3x reply rates", height=100)

st.divider()

# ── STEP 2 ───────────────────────────────────────────────
st.markdown("<div class='step-label'>Step 2 — Your Gmail</div>", unsafe_allow_html=True)
st.markdown("## Connect your email")

col1, col2, col3 = st.columns(3)
with col1:
    gmail_user  = st.text_input("Gmail address", placeholder="you@gmail.com")
with col2:
    gmail_pass  = st.text_input("App password",  type="password")
with col3:
    sender_name = st.text_input("Your name",     placeholder="John Smith")

st.caption("Need an app password? Go to myaccount.google.com → Security → App Passwords")

st.divider()

# ── STEP 3 ───────────────────────────────────────────────
st.markdown("<div class='step-label'>Step 3 — Your Prospects</div>", unsafe_allow_html=True)
st.markdown("## Upload your list")
st.caption("CSV must have 3 columns: name, email, company")

sample = pd.DataFrame({
    "name":    ["John Smith", "Sarah Johnson"],
    "email":   ["john@acme.com", "sarah@techcorp.com"],
    "company": ["Acme Inc", "TechCorp"]
})
st.download_button("Download sample CSV", sample.to_csv(index=False), "sample.csv", "text/csv")

uploaded = st.file_uploader("", type=["csv"])

df = None
if uploaded:
    df = pd.read_csv(uploaded)
    df.columns = df.columns.str.strip().str.lower()
    st.success(f"✅ {len(df)} prospects loaded")
    st.dataframe(df, use_container_width=True)

st.divider()

# ── STEP 4 ───────────────────────────────────────────────
st.markdown("<div class='step-label'>Step 4 — Preview</div>", unsafe_allow_html=True)
st.markdown("## Preview your email")

if st.button("Generate preview"):
    if df is None:
        st.error("Please upload a CSV first.")
    elif not all([saas_name, saas_description, saas_target, saas_benefits]):
        st.error("Please fill in all product info first.")
    elif not sender_name:
        st.error("Please enter your name.")
    else:
        row = df.iloc[0]
        with st.spinner(f"Researching {row['company']}..."):
            research = research_company(row["company"])
        with st.spinner("Writing email..."):
            email = write_email(
                row["name"], row["company"], research,
                saas_name, saas_description,
                saas_target, saas_benefits, sender_name
            )
        st.info(email)

st.divider()

# ── STEP 5 ───────────────────────────────────────────────
st.markdown("<div class='step-label'>Step 5 — Send</div>", unsafe_allow_html=True)
count = len(df) if df is not None else 0
st.markdown("## Send all emails")
st.caption(f"This will send {count} {'email' if count == 1 else 'emails'} — one per person." if count > 0 else "Upload a CSV to see how many emails will be sent.")

if st.button("🚀 Send now", type="primary"):
    if df is None:
        st.error("Please upload a CSV first.")
    elif not all([saas_name, saas_description, saas_target, saas_benefits]):
        st.error("Please fill in all product info first.")
    elif not gmail_user or not gmail_pass:
        st.error("Please enter your Gmail credentials.")
    elif not sender_name:
        st.error("Please enter your name.")
    else:
        progress = st.progress(0)
        status   = st.empty()
        results  = []

        for i, row in df.iterrows():
            status.caption(f"Sending to {row['name']} at {row['company']}...")
            research      = research_company(row["company"])
            email_content = write_email(
                row["name"], row["company"], research,
                saas_name, saas_description,
                saas_target, saas_benefits, sender_name
            )
            lines   = email_content.strip().split("\n")
            subject = lines[0].replace("Subject: ", "").strip()
            body    = "\n".join(lines[2:]).strip()
            result  = send_email(gmail_user, gmail_pass, row["email"], subject, body)
            results.append({
                "Name":    row["name"],
                "Company": row["company"],
                "Email":   row["email"],
                "Status":  "✅ Sent" if result is True else "❌ Failed"
            })
            progress.progress((i + 1) / len(df))
            time.sleep(1)

        status.empty()
        results_df = pd.DataFrame(results)
        sent   = len([r for r in results if "✅" in r["Status"]])
        failed = len([r for r in results if "❌" in r["Status"]])

        col1, col2 = st.columns(2)
        col1.metric("✅ Sent",   sent)
        col2.metric("❌ Failed", failed)
        st.dataframe(results_df, use_container_width=True)
