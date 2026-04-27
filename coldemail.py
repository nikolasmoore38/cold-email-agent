import streamlit as st
import anthropic
import pandas as pd
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

from dotenv import load_dotenv
import os
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))

# ── EMAIL SENDER ─────────────────────────────────────────
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

# ── RESEARCH COMPANY ─────────────────────────────────────
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

Be specific and realistic. If you don't know the company, make reasonable assumptions based on the name.
Keep it under 100 words total.
"""}]
        )
        return response.content[0].text
    except:
        return f"{company_name} is a business that could benefit from automation and efficiency tools."

# ── WRITE EMAIL ──────────────────────────────────────────
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
- Max 67 words total including greeting and sign off
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

# ── UI ───────────────────────────────────────────────────
st.set_page_config(page_title="AI Cold Email Agent", page_icon="📧", layout="wide")
st.title("📧 AI Cold Email Agent")
st.caption("Research, write, and send personalized cold emails automatically.")

# ── STEP 1: YOUR SAAS INFO ───────────────────────────────
st.header("Step 1 — Tell me about your SaaS product")
col1, col2 = st.columns(2)
with col1:
    saas_name        = st.text_input("Product Name", placeholder="e.g. SalesFlow")
    saas_description = st.text_area("What does it do?",
                                     placeholder="e.g. Automates lead generation for B2B sales teams using AI",
                                     height=100)
with col2:
    saas_target   = st.text_input("Who is it for?",
                                   placeholder="e.g. Sales teams at SaaS companies with 10-100 employees")
    saas_benefits = st.text_area("Why should they use it? What makes it great?",
                                  placeholder="e.g. Saves 10 hours/week, increases reply rates by 3x, integrates with HubSpot...",
                                  height=100)

st.divider()

# ── STEP 2: GMAIL SETUP ──────────────────────────────────
st.header("Step 2 — Connect your Gmail")
col1, col2, col3 = st.columns(3)
with col1:
    gmail_user  = st.text_input("Your Gmail address", placeholder="you@gmail.com")
with col2:
    gmail_pass  = st.text_input("App Password", type="password",
                                 help="Use a Gmail App Password, not your regular password.")
with col3:
    sender_name = st.text_input("Your Name", placeholder="e.g. John Smith")

st.caption("⚠️ Use a Gmail App Password — not your regular password. Go to myaccount.google.com → Security → 2-Step Verification → App Passwords")

st.divider()

# ── STEP 3: UPLOAD CSV ───────────────────────────────────
st.header("Step 3 — Upload your prospect list")
st.caption("CSV must have columns: **name**, **email**, **company**")

sample = pd.DataFrame({
    "name":    ["John Smith", "Sarah Johnson"],
    "email":   ["john@acme.com", "sarah@techcorp.com"],
    "company": ["Acme Inc", "TechCorp"]
})
st.download_button("📥 Download sample CSV", sample.to_csv(index=False),
                   "sample_prospects.csv", "text/csv")

uploaded = st.file_uploader("Upload your CSV", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    df.columns = df.columns.str.strip().str.lower()
    st.success(f"✅ Loaded {len(df)} prospects")
    st.dataframe(df, use_container_width=True)

    st.divider()

    # ── STEP 4: PREVIEW ──────────────────────────────────
    st.header("Step 4 — Preview & Send")

    if st.button("🔍 Preview first email"):
        if not all([saas_name, saas_description, saas_target, saas_benefits]):
            st.error("Please fill in all product info first!")
        elif not sender_name:
            st.error("Please enter your name!")
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
            st.subheader(f"Preview — Email to {row['name']} at {row['company']}")
            st.info(email)
            st.subheader("Company Research Used:")
            st.caption(research)

    st.divider()

    # ── STEP 5: SEND ALL ─────────────────────────────────
    st.header("Step 5 — Send all emails")
    count = len(df)
    st.warning(f"This will send **{count} {'email' if count == 1 else 'emails'}** — one to each person in your CSV.")

    if st.button("🚀 Send all emails now", type="primary"):
        if not all([saas_name, saas_description, saas_target, saas_benefits]):
            st.error("Please fill in all product info first!")
        elif not gmail_user or not gmail_pass:
            st.error("Please enter your Gmail credentials!")
        elif not sender_name:
            st.error("Please enter your name!")
        else:
            progress = st.progress(0)
            status   = st.empty()
            results  = []

            for i, row in df.iterrows():
                status.write(f"Processing {row['name']} at {row['company']}...")

                research = research_company(row["company"])

                email_content = write_email(
                    row["name"], row["company"], research,
                    saas_name, saas_description,
                    saas_target, saas_benefits, sender_name
                )

                lines   = email_content.strip().split("\n")
                subject = lines[0].replace("Subject: ", "").strip()
                body    = "\n".join(lines[2:]).strip()

                result = send_email(gmail_user, gmail_pass, row["email"], subject, body)

                results.append({
                    "Name":    row["name"],
                    "Company": row["company"],
                    "Email":   row["email"],
                    "Status":  "✅ Sent" if result is True else f"❌ {result}"
                })

                progress.progress((i + 1) / len(df))
                time.sleep(1)

            status.write("Done!")
            results_df = pd.DataFrame(results)
            st.subheader("Results")
            st.dataframe(results_df, use_container_width=True)

            sent   = len([r for r in results if "✅" in r["Status"]])
            failed = len([r for r in results if "❌" in r["Status"]])
            col1, col2 = st.columns(2)
            col1.metric("✅ Sent",   sent)
            col2.metric("❌ Failed", failed)