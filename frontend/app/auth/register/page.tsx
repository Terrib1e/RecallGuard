'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { apiService } from '@/services/api';
import { UserCreate } from '@/types';

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [userData, setUserData] = useState({
    email: '',
    phone: '',
  });

  const handleUserDataChange = (field: string, value: string) => {
    setUserData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const registerData: UserCreate = {
        email: userData.email,
        phone: userData.phone || undefined,
        products: [], // Empty products array
      };

      const response = await apiService.createUser(registerData);

      // Store user ID in localStorage for simple auth
      localStorage.setItem('userId', response.id.toString());

      toast.success('Registration successful! You can now add your products in the dashboard.');
      router.push('/dashboard');
    } catch (error: any) {
      console.error('Registration error:', error);
      toast.error(
        error.response?.data?.detail || 'Registration failed. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Join RecallGuard
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            Sign up to start monitoring your products for recalls
          </p>
        </div>

        <div className="bg-white p-8 rounded-lg shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label
                  htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Email Address *
                </label>
                <input
                  type="email"
                  id="email"
                  required
                  value={userData.email}
                  onChange={(e) => handleUserDataChange('email', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="your@email.com"
                />
              </div>

              <div>
                <label
                  htmlFor="phone"
                className="block text-sm font-medium text-gray-700 mb-2"
                >
                Phone Number (Optional)
                </label>
                <input
                  type="tel"
                  id="phone"
                  value={userData.phone}
                  onChange={(e) => handleUserDataChange('phone', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="+1 (555) 123-4567"
                />
              <p className="mt-1 text-sm text-gray-500">
                We&apos;ll use this to send you urgent recall alerts
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white py-3 px-4 rounded-md text-lg font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              After signing up, you can add your products in your dashboard to start receiving recall alerts.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}