# GemVision - AI-Powered Jewellery Platform

Complete AI-powered platform for jewellery design, virtual try-on, and quality inspection.

## Features

### 1. AI Jewellery Designer
Transform text prompts into stunning jewellery designs using DALL-E 3 and Claude AI.

**Key Features:**
- Text-to-image generation with natural language prompts
- Category-specific templates (Ring, Necklace, Earring, Bracelet)
- Style presets (Bridal, Minimalist, Traditional, Antique, Heavy-stone)
- Multiple realism modes (Realistic, Photoreal, CAD, Sketch)
- AI-powered design analysis with Claude Vision
- Save designs as ideas and favorites
- Generate up to 4 variations per prompt

**Technical Stack:**
- OpenAI DALL-E 3 for image generation
- Anthropic Claude for prompt enhancement and image analysis
- Smart prompt engineering for jewelry-specific results

### 2. Virtual Try-On Demo
Let customers visualize jewellery on their own hands with interactive placement controls.

**Key Features:**
- Upload hand photos or use device camera
- Interactive overlay placement with drag, scale, rotate
- Finger-specific positioning (Index, Middle, Ring, Little)
- Adjustable opacity, hue, and color filters
- Save snapshots for approval
- Share try-on sessions with customers
- Before/after comparison mode

**Technical Stack:**
- HTML5 Canvas for image manipulation
- CSS transforms for smooth interactions
- Touch-friendly controls for mobile

### 3. AI Quality Inspector
Automated defect detection for quality control with simulated and ML-based inspection.

**Key Features:**
- Automated defect detection (scratches, misalignment, discoloration, etc.)
- Confidence scoring and severity levels
- Image quality analysis (lighting, contrast, glare detection)
- Operator triage workflow (Accept / Rework / Escalate)
- Rework job creation and tracking
- Full lifecycle audit trail
- Defect heatmaps and visualization
- False positive flagging for model improvement

**Technical Stack:**
- Simulated detection for instant demo (customizable)
- TensorFlow/ML model support for production
- OpenCV for image analysis

## Project Structure

```
gemvision/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI app entry point
│   │   └── config.py       # Configuration management
│   ├── models/
│   │   └── database.py     # SQLAlchemy models
│   ├── services/
│   │   ├── ai_designer_service.py      # AI design generation
│   │   ├── qc_inspector_service.py     # Quality inspection
│   │   └── s3_service.py               # AWS S3 integration
│   ├── routers/
│   │   ├── designer.py     # Designer API endpoints
│   │   ├── tryon.py        # Try-on API endpoints
│   │   ├── qc_inspector.py # QC API endpoints
│   │   └── analytics.py    # Analytics endpoints
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Next.js 14 frontend (App Router)
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   │   ├── page.tsx   # Home page
│   │   │   ├── layout.tsx # Root layout
│   │   │   └── providers.tsx # React Query provider
│   │   ├── components/    # React components
│   │   ├── lib/
│   │   │   └── api.ts     # API client
│   │   ├── types/
│   │   │   └── index.ts   # TypeScript types
│   │   └── styles/
│   │       └── globals.css # Global styles
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── next.config.js
│
├── .env.example           # Environment variables template
├── .gitignore
└── README.md
```

## Installation & Setup

### Prerequisites

- **Python 3.9+**
- **Node.js 18+** and npm/yarn
- **PostgreSQL** (or use SQLite for development)
- **Redis** (optional, for caching)

### API Keys Required

You'll need the following API keys:

1. **Anthropic Claude API Key** - Get from https://console.anthropic.com/
2. **OpenAI API Key** - Get from https://platform.openai.com/
3. **Google Gemini Pro API Key** - Get from https://makersuite.google.com/
4. **AWS Credentials** - For S3 image storage

### Step 1: Clone and Setup Environment

```bash
# Navigate to project directory
cd gemvision

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
# Use any text editor to fill in:
# - ANTHROPIC_API_KEY
# - OPENAI_API_KEY
# - GEMINI_API_KEY
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - AWS_S3_BUCKET
# And other configuration
```

### Step 2: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m backend.models.database

# Run backend server
python -m backend.app.main

# Backend will run on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Step 3: Frontend Setup

```bash
# Open new terminal
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Run development server
npm run dev

# Frontend will run on http://localhost:3000
```

### Step 4: Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Configuration

### Environment Variables

#### Backend (.env)

```env
# AI API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# AWS
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# Database
DATABASE_URL=sqlite:///./gemvision.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/gemvision

# Image Generation
DEFAULT_IMAGE_MODEL=dall-e-3
IMAGE_QUALITY=hd
IMAGE_SIZE=1024x1024
MAX_IMAGES_PER_GENERATION=4

# QC Inspector
QC_MODE=simulated  # or 'ml' for ML model
QC_CONFIDENCE_THRESHOLD=0.7
```

#### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Usage Guide

### AI Jewellery Designer

1. Navigate to **Designer** from home page
2. Select jewellery **category** (Ring, Necklace, etc.)
3. Choose **style preset** (Bridal, Minimalist, etc.)
4. Enter your **text prompt** or use a template
5. Select **realism mode** (Realistic, CAD, Sketch)
6. Click **Generate** and wait 5-10 seconds
7. View 4 generated variations
8. **Actions**:
   - Expand images for full view
   - Save as "Idea" for later
   - Mark as favorite
   - Download images
   - Refine by modifying prompt

**Example Prompts:**
- "Solitaire engagement ring with round brilliant diamond, thin pavé band, 18k white gold"
- "Halo engagement ring with cushion cut center diamond, rose gold band"
- "Minimalist solitaire ring with bezel setting, brushed finish"

### Virtual Try-On

1. Navigate to **Try-On** from home page
2. **Upload a hand photo** or use camera
3. Select or upload a **ring overlay** image
4. Use controls to:
   - **Drag** to move
   - **Pinch/Scroll** to scale
   - **Rotate** handle to rotate
   - Adjust **opacity** and **hue**
5. Use **anchor presets** for quick positioning
6. **Save snapshot** when satisfied
7. **Send for approval** to share with customer

**Tips:**
- Use well-lit hand photos
- Keep fingers straight for best results
- Try different finger positions

### AI Quality Inspector

1. Navigate to **QC Inspector** from home page
2. **Upload jewellery photo** for inspection
3. Wait for analysis (3-5 seconds)
4. Review **detected defects** with:
   - Bounding boxes
   - Confidence scores
   - Severity levels
5. **Triage** the inspection:
   - **Accept**: No action needed
   - **Rework**: Create rework job
   - **Escalate**: Manual review required
6. For rework:
   - Select specific defects
   - Add operator notes
   - Set priority
   - Assign to station
7. Track rework job through lifecycle

**Defect Types Detected:**
- Surface scratches
- Stone misalignment
- Surface discoloration
- Prong damage
- Polish defects
- Casting porosity

## API Documentation

### FastAPI Interactive Docs

Access full API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Designer API
- `POST /api/designer/generate` - Generate designs
- `GET /api/designer/designs` - List designs
- `POST /api/designer/templates` - Get template prompts
- `POST /api/designer/save-idea` - Save as idea

#### Try-On API
- `POST /api/tryon/upload-hand-photo` - Upload hand photo
- `POST /api/tryon/save` - Save try-on session
- `POST /api/tryon/save-snapshot` - Save snapshot
- `POST /api/tryon/send-for-approval` - Send for approval

#### QC Inspector API
- `POST /api/qc/inspect` - Inspect item
- `POST /api/qc/triage` - Triage inspection
- `POST /api/qc/rework` - Create rework job
- `PATCH /api/qc/rework/{id}` - Update rework status

#### Analytics API
- `GET /api/analytics/dashboard` - Dashboard stats
- `GET /api/analytics/trends` - Trend data
- `GET /api/analytics/kpis` - Key performance indicators

## Database Schema

The application uses SQLAlchemy ORM with the following main models:

- **User**: User accounts
- **Design**: AI-generated designs
- **TryOn**: Virtual try-on sessions
- **QCInspection**: Quality inspections
- **ReworkJob**: Rework tracking
- **Analytics**: Event logging

### Database Initialization

```bash
cd backend
python -m backend.models.database
```

## Deployment

### Backend Deployment

**Options:**
- **Railway / Render**: Easy Python deployment
- **AWS EC2**: Full control
- **Heroku**: Quick deployment
- **Docker**: Containerized deployment

**Steps:**
1. Set environment variables on hosting platform
2. Install dependencies: `pip install -r requirements.txt`
3. Initialize database
4. Run: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`

### Frontend Deployment

**Recommended: Vercel** (optimal for Next.js)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Set environment variables in Vercel dashboard
```

**Alternative: Netlify, Railway, or any Node.js host**

## Performance & Optimization

### Image Generation
- DALL-E 3: ~5-10 seconds per image
- DALL-E 2: ~3-5 seconds per image
- Caching: Store prompt → image mappings

### Try-On
- Client-side canvas rendering for instant feedback
- Optimize overlay images (use WebP/PNG)
- Compress snapshots before upload

### QC Inspector
- Simulated mode: Instant results
- ML mode: 2-5 seconds depending on model
- Pre-process images to standard resolution

## Troubleshooting

### Backend Issues

**"Module not found" errors:**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

**Database errors:**
```bash
# Reinitialize database
python -m backend.models.database
```

**API key errors:**
- Check `.env` file has all keys
- Verify keys are valid and active
- Check API quotas/limits

### Frontend Issues

**"Module not found":**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**API connection errors:**
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Ensure backend is running
- Check CORS settings

## Future Enhancements

### Potential Features
1. **3D Model Generation**: Convert 2D designs to 3D models
2. **AR Try-On**: Use ARCore/ARKit for real AR
3. **ML Model Training**: Train custom QC models
4. **Multi-user Collaboration**: Team workspaces
5. **Order Management**: Full e-commerce integration
6. **CAD File Export**: Export to manufacturing formats
7. **Customer Portal**: Self-service design portal
8. **Mobile Apps**: Native iOS/Android apps

### ML Model Training (QC)
For production QC inspection, train a custom model:

1. Collect labeled dataset of defects
2. Use TensorFlow/PyTorch for training
3. Export model to TensorFlow.js or ONNX
4. Update `qc_inspector_service.py` to load model
5. Set `QC_MODE=ml` in `.env`

## Support & Contributing

### Getting Help
- Check API docs: http://localhost:8000/docs
- Review this README
- Check environment variables

### Tech Stack Summary
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **AI**: OpenAI DALL-E, Anthropic Claude, Google Gemini
- **Storage**: AWS S3
- **Database**: PostgreSQL/SQLite

## License

Proprietary - All rights reserved

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [OpenAI](https://openai.com/)
- [Anthropic Claude](https://anthropic.com/)
- [Tailwind CSS](https://tailwindcss.com/)

---

**GemVision** - Transforming jewellery design with AI
