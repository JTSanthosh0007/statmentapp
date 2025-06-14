# Deployment Guide

## Project Structure
```
├── frontend/           # Next.js frontend application
│   ├── app/           # Next.js app directory
│   ├── components/    # React components
│   ├── lib/          # Utility functions
│   └── vercel.json   # Vercel configuration
│
├── backend/           # Python backend application
│   ├── app.py        # Main Streamlit application
│   ├── requirements.txt
│   └── render.yaml   # Render configuration
```

## Initial Setup

1. Install dependencies:
   ```bash
   # Frontend
   cd frontend
   npm install

   # Backend
   cd backend
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. Configure Git:
   ```bash
   git config --global core.autocrlf true
   ```

## Backend Deployment (Render)

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. Go to [Render](https://render.com) and:
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - Name: statement-parser-backend
     - Environment: Python
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `streamlit run app.py --server.port=$PORT`
   - Add Environment Variables:
     - JWT_SECRET (Render will generate this)
     - PYTHON_VERSION: 3.9.0
   - Click "Create Web Service"

3. Wait for deployment to complete and copy the provided URL (e.g., https://your-backend.onrender.com)

## Frontend Deployment (Vercel)

1. Update the backend URL:
   - Edit `frontend/vercel.json`
   - Replace `https://your-backend.onrender.com` with your actual Render backend URL

2. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Update backend URL"
   git push origin main
   ```

3. Go to [Vercel](https://vercel.com) and:
   - Click "New Project"
   - Import your GitHub repository
   - Configure the project:
     - Framework Preset: Next.js
     - Root Directory: frontend
   - Add Environment Variables:
     - NEXT_PUBLIC_API_BASE_URL: Your Render backend URL
   - Click "Deploy"

## Post-Deployment

1. Test the connection:
   - Open your Vercel frontend URL
   - Try uploading a file
   - Check if the backend processes it correctly

2. Monitor the applications:
   - Check Render logs for backend issues
   - Check Vercel logs for frontend issues

## Troubleshooting

1. CORS Issues:
   - Verify the backend URL is correct in frontend environment variables
   - Check if streamlit-cors is properly installed
   - Ensure the backend is accessible from the frontend domain

2. File Upload Issues:
   - Check if the backend URL is correctly set in the frontend
   - Verify the upload endpoint is working
   - Check file size limits

3. Performance Issues:
   - Monitor Render's resource usage
   - Check Vercel's performance metrics
   - Optimize file processing if needed

4. Common Errors:
   - If you see "Module not found" errors, check if all dependencies are installed
   - If you see CORS errors, verify the backend URL and CORS configuration
   - If you see deployment failures, check the build logs in both Vercel and Render 