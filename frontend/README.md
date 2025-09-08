# RecallGuard Frontend

Next.js 14 frontend for RecallGuard - Product recall alert system.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` file:
```
NEXT_PUBLIC_API_URL=https://recallguard-production.up.railway.app
```

For local development, use:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Features

- **Landing Page** - Marketing page with CTA to get started
- **Registration** - User signup with dynamic product form
- **Dashboard** - View registered products and account info
- **Responsive Design** - Works on desktop and mobile
- **Toast Notifications** - Success/error feedback
- **Simple Auth** - localStorage-based user sessions

## Project Structure

```
frontend/
├── app/
│   ├── dashboard/
│   │   └── page.tsx          # Dashboard page
│   ├── register/
│   │   └── page.tsx          # Registration page
│   ├── globals.css           # Global styles
│   ├── layout.tsx            # Root layout with nav
│   └── page.tsx              # Landing page
├── components/
│   └── ProductForm.tsx       # Reusable product form
├── services/
│   └── api.ts                # API service layer
├── types/
│   └── index.ts              # TypeScript interfaces
├── package.json              # Dependencies
├── tailwind.config.js        # Tailwind configuration
├── tsconfig.json             # TypeScript configuration
└── next.config.js            # Next.js configuration
```

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Deployment

This app is ready for deployment on Vercel, Netlify, or any Node.js hosting platform.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
