# SHE Water Assistance CRM

## Setup (one time)

1. Copy `.env.example` to `.env`
   ```
   copy .env.example .env
   ```

2. Open `.env` in Notepad and replace the DATABASE_URL with your actual Neon connection string
   - Go to Neon Dashboard → Your Project → Connection Details
   - Copy the connection string (starts with postgresql://)
   - Paste it as the DATABASE_URL value

3. Install dependencies
   ```
   npm install
   ```

## Run

```
npm start
```

Then open your browser to: http://localhost:3000

## That's it.
