# 🚀 Deploy to Netlify & Render - Quick Guide

## Step 1: Deploy Backend to Render

1. **Go to [Render.com](https://render.com)** and sign up/login with GitHub
2. **Click "New +" → "Web Service"**
3. **Connect Repository**: `devansh054/PL2025_ML_Predictor`
4. **Configure Service:**
   - **Name**: `pl-predictor-backend`
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

5. **Environment Variables** (Add in Render dashboard):
   ```
   DATABASE_URL=sqlite:///./pl_predictor.db
   LOG_LEVEL=info
   CORS_ORIGINS=*
   ```

6. **Click "Create Web Service"** - Render will deploy automatically

## Step 2: Deploy Frontend to Netlify

1. **Go to [Netlify.com](https://netlify.com)** and sign up/login with GitHub
2. **Click "Add new site" → "Import an existing project"**
3. **Connect to Git provider**: GitHub
4. **Select Repository**: `devansh054/PL2025_ML_Predictor`
5. **Configure Build Settings:**
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `out`
   - **Production branch**: `main`

6. **Environment Variables** (Add in Netlify dashboard):
   ```
   NEXT_PUBLIC_API_URL=https://your-render-backend-url.onrender.com
   ```

7. **Click "Deploy site"** - Netlify will build and deploy

## Step 3: Update URLs

After both deployments:

1. **Copy your Render backend URL** (e.g., `https://pl-predictor-backend-xyz.onrender.com`)
2. **Copy your Netlify frontend URL** (e.g., `https://amazing-pl-predictor-123.netlify.app`)
3. **Update Render environment variables:**
   - Change `CORS_ORIGINS` to: `https://your-netlify-url.netlify.app,http://localhost:3000`
4. **Update Netlify environment variables:**
   - Set `NEXT_PUBLIC_API_URL` to your Render backend URL

## 🎉 You're Live!

- **Frontend**: Your Netlify URL
- **Backend API**: Your Render URL
- **API Docs**: `https://your-render-url.onrender.com/docs`

## 🔧 Troubleshooting

**If frontend can't connect to backend:**
1. Check CORS_ORIGINS includes your Netlify URL
2. Verify NEXT_PUBLIC_API_URL is correct
3. Check browser console for errors

**If backend won't start:**
1. Check Render logs for Python errors
2. Verify all dependencies in requirements.txt
3. Ensure start command is correct

## 💡 Pro Tips

- Render free tier sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- Netlify builds are triggered automatically on git push
- Both platforms offer custom domains in paid plans
