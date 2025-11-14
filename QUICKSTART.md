# GemVision Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

Before you begin, ensure you have:

- [ ] Python 3.9 or higher installed
- [ ] Node.js 18 or higher installed
- [ ] API keys ready (see below)

Check versions:
```bash
python --version  # Should be 3.9+
node --version    # Should be 18+
npm --version
```

## Step 1: Get Your API Keys (5 minutes)

### Required API Keys:

1. **OpenAI API Key** (Primary - for DALL-E image generation)
   - Go to: https://platform.openai.com/api-keys
   - Sign up/login
   - Create new API key
   - Copy and save it

2. **Anthropic Claude API Key** (for AI analysis)
   - Go to: https://console.anthropic.com/
   - Sign up/login
   - Create API key
   - Copy and save it

3. **Google Gemini API Key** (optional, for backup)
   - Go to: https://makersuite.google.com/
   - Get API key
   - Copy and save it

4. **AWS S3 Credentials** (for image storage)
   - Go to AWS Console
   - Create S3 bucket
   - Create IAM user with S3 access
   - Copy Access Key ID and Secret

### Quick AWS S3 Setup:

```bash
1. Go to AWS Console → S3
2. Click "Create bucket"
3. Name it: gemvision-images (or your choice)
4. Region: us-east-1 (or your choice)
5. Uncheck "Block all public access" (for demo purposes)
6. Create bucket

7. Go to IAM → Users → Create user
8. Attach policy: AmazonS3FullAccess
9. Create access key → Download credentials
```

## Step 2: Configure Environment (2 minutes)

```bash
# Navigate to project
cd gemvision

# Copy environment template
cp .env.example .env

# Edit .env file and add your keys
# Windows: use notepad .env
# Mac/Linux: use nano .env or any editor
```

**Fill in these values in .env:**

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
GEMINI_API_KEY=xxxxxxxxxxxxx

AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxx
AWS_REGION=us-east-1
AWS_S3_BUCKET=gemvision-images
```

Save and close the file.

## Step 3: Start Backend (2 minutes)

### Windows:
```bash
# Double-click start-backend.bat
# OR run in terminal:
start-backend.bat
```

### Mac/Linux:
```bash
chmod +x start-backend.sh
./start-backend.sh
```

Wait for:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test it:** Open http://localhost:8000/health in browser
Should see: `{"status": "healthy"}`

## Step 4: Start Frontend (2 minutes)

Open a **new terminal window** (keep backend running!)

### Windows:
```bash
# Double-click start-frontend.bat
# OR run in terminal:
start-frontend.bat
```

### Mac/Linux:
```bash
chmod +x start-frontend.sh
./start-frontend.sh
```

Wait for:
```
✓ Ready in XXXXms
○ Local:   http://localhost:3000
```

## Step 5: Access GemVision

Open your browser and go to:

**http://localhost:3000**

You should see the GemVision home page!

## Quick Test - Generate Your First Design

1. Click **"Start Designing"** or go to **Designer**
2. Select:
   - Category: **Ring**
   - Style: **Bridal**
3. Enter prompt: `"Elegant solitaire engagement ring with round diamond, platinum band"`
4. Click **Generate**
5. Wait 5-10 seconds
6. See your AI-generated jewellery designs!

## Troubleshooting

### Backend won't start

**Error: "Module not found"**
```bash
cd backend
pip install -r requirements.txt
```

**Error: "API key not found"**
- Check .env file exists
- Verify API keys are correct
- No extra spaces in .env

### Frontend won't start

**Error: "Cannot find module"**
```bash
cd frontend
rm -rf node_modules
npm install
```

**Error: "Port 3000 already in use"**
```bash
# Kill process on port 3000
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:3000 | xargs kill -9
```

### API Errors

**"API key invalid"**
- Verify key is correct in .env
- Check API has credits/quota
- Restart backend after changing .env

**"Cannot connect to API"**
- Ensure backend is running (http://localhost:8000/health)
- Check NEXT_PUBLIC_API_URL in frontend/.env.local
- Verify firewall not blocking

### S3 Upload Errors

**"Access Denied"**
- Check AWS credentials are correct
- Verify IAM user has S3 permissions
- Check bucket name matches

## What's Next?

### Try All Features:

1. **AI Designer** (http://localhost:3000/designer)
   - Generate jewellery designs from text
   - Try different categories and styles
   - Save your favorites

2. **Virtual Try-On** (http://localhost:3000/tryon)
   - Upload a hand photo
   - Place ring overlays
   - Save snapshots

3. **QC Inspector** (http://localhost:3000/qc)
   - Upload jewellery photos
   - See automated defect detection
   - Create rework jobs

4. **Analytics** (http://localhost:3000/analytics)
   - View usage statistics
   - Track trends
   - Monitor KPIs

### API Documentation

Full API docs available at:
**http://localhost:8000/docs**

Interactive API testing with Swagger UI!

## Production Deployment

When ready to deploy:

### Backend:
- **Recommended**: Railway, Render, or AWS EC2
- Set environment variables on platform
- Use PostgreSQL instead of SQLite
- Enable HTTPS

### Frontend:
- **Recommended**: Vercel (optimal for Next.js)
- One-click deployment
- Automatic HTTPS
- Global CDN

```bash
# Deploy to Vercel
cd frontend
npm i -g vercel
vercel
```

## Getting Help

- **API Docs**: http://localhost:8000/docs
- **README**: See full README.md
- **Check logs**: Backend and frontend terminals show detailed logs

## Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Health check passes (http://localhost:8000/health)
- [ ] Home page loads (http://localhost:3000)
- [ ] Successfully generated first design
- [ ] All API keys working

**Congratulations!** 🎉

GemVision is now running! Start designing amazing jewellery with AI.

---

**Need more help?** Check the full README.md for detailed documentation.
