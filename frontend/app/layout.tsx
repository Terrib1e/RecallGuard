import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import ToasterProvider from '@/components/ui/ToasterProvider';
import Link from 'next/link';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'RecallGuard - Product Recall Alerts',
  description: 'Stay informed about product recalls and safety alerts',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link href="/" className="flex-shrink-0 flex items-center">
                  <span className="text-xl font-bold text-primary-600">
                    RecallGuard
                  </span>
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <Link
                  href="/auth/register"
                  className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Register
                </Link>
                <Link
                  href="/dashboard"
                  className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main>{children}</main>
        <ToasterProvider />
      </body>
    </html>
  );
}