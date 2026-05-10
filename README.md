Math Teacher Telegram Bot (Vercel 
Deployment)
Deploy in 3 Steps:
Step 1: Push to GitHub
Create a new GitHub repository and push these ﬁles.
Step 2: Deploy on Vercel 
1.  Go to https://vercel.com
2.  Sign up with GitHub (FREE, no credit card ) 
3.  Click "Add New Project"
4.  Import your GitHub repository
5.  In "Environment Variables" section, add:
•    BOT_TOKEN  = your_bot_token
•    GROQ_API_KEY  = your_groq_key 
6.  Click "Deploy"
Step 3: Set Webhook
After deployment, open this URL in your browser (replace YOUR_APP_NAME):
Done! Your bot is live forever.
Plain Text
https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://YOUR_APP_NAME.vercel.app/webhook
