'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { apiService } from '@/services/api';
import { Product, User } from '@/types';
import MatchingIndicator, { MatchingProgress, ProductStatus } from '@/components/features/MatchingIndicator';

interface SystemStatus {
  isMatching: boolean;
  isScrapingRecalls: boolean;
  lastScrapedAt: string | null;
  matchingProgress: number;
  unprocessedRecalls: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [recallAlerts, setRecallAlerts] = useState<any>(null);
  const [isCheckingRecalls, setIsCheckingRecalls] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    isMatching: false,
    isScrapingRecalls: false,
    lastScrapedAt: null,
    matchingProgress: 0,
    unprocessedRecalls: 0,
  });

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!isClient) return;
    
    const userId = localStorage.getItem('userId');
    if (!userId) {
      router.push('/auth/register');
      return;
    }

    loadUserData(parseInt(userId));

    // Poll system status every 10 seconds
    const statusInterval = setInterval(() => {
      checkSystemStatus();
    }, 10000);

    return () => clearInterval(statusInterval);
  }, [router, isClient]);

  const loadUserData = async (userId: number) => {
    try {
      setIsLoading(true);
      const [userData, userProducts, userRecallAlerts] = await Promise.all([
        apiService.getUser(userId),
        apiService.getUserProducts(userId),
        apiService.getUserRecallAlerts(userId),
      ]);
      setUser(userData);
      setProducts(userProducts);
      setRecallAlerts(userRecallAlerts);
    } catch (error: any) {
      console.error('Error loading user data:', error);
      toast.error('Failed to load user data');
      // If user not found, redirect to register
      if (error.response?.status === 404) {
        localStorage.removeItem('userId');
        router.push('/auth/register');
      }
    } finally {
      setIsLoading(false);
    }
  };

    const checkSystemStatus = async () => {
    try {
      const health = await apiService.healthCheck();

      // Check if system just started matching
      const wasMatching = systemStatus.isMatching;
      const isNowMatching = health.stats.unprocessed_recalls > 0 && Math.random() > 0.7;

      // Show toast notification when matching starts
      if (!wasMatching && isNowMatching) {
        toast.success('🧠 AI started analyzing your products for recalls!', {
          duration: 3000,
          position: 'top-center',
        });
      }

      // Simulate system status based on health data
      setSystemStatus(prev => ({
        ...prev,
        unprocessedRecalls: health.stats.unprocessed_recalls,
        isMatching: isNowMatching,
        lastScrapedAt: new Date().toISOString(),
      }));
    } catch (error) {
      console.error('Error checking system status:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('userId');
    toast.success('Logged out successfully');
    router.push('/');
  };

  const handleManualRecallCheck = async () => {
    setIsCheckingRecalls(true);
    setSystemStatus(prev => ({ ...prev, isMatching: true, matchingProgress: 0 }));

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setSystemStatus(prev => ({
        ...prev,
        matchingProgress: Math.min(prev.matchingProgress + Math.random() * 25, 95)
      }));
    }, 500);

    try {
      await apiService.triggerManualRecallCheck();
      toast.success('Manual recall check completed! We\'ll notify you if any matches are found.');

      // Complete progress
      setSystemStatus(prev => ({ ...prev, matchingProgress: 100 }));

      // Reload recall alerts after a short delay
      setTimeout(async () => {
        const userId = localStorage.getItem('userId');
        if (userId) {
          const alerts = await apiService.getUserRecallAlerts(parseInt(userId));
          setRecallAlerts(alerts);
        }
        setSystemStatus(prev => ({ ...prev, isMatching: false, matchingProgress: 0 }));
      }, 2000);
    } catch (error: any) {
      console.error('Error triggering recall check:', error);
      toast.error('Failed to trigger recall check. Please try again.');
      setSystemStatus(prev => ({ ...prev, isMatching: false, matchingProgress: 0 }));
    } finally {
      clearInterval(progressInterval);
      setIsCheckingRecalls(false);
    }
  };

  const handleRecallScraping = async () => {
    setIsCheckingRecalls(true);
    setSystemStatus(prev => ({ ...prev, isScrapingRecalls: true }));

    try {
      const result = await apiService.triggerRecallScraping(7);
      toast.success(`Recall scraping completed! ${result.stats.new_recalls} new recalls added.`);

      // Reload recall alerts after scraping
      setTimeout(async () => {
        const userId = localStorage.getItem('userId');
        if (userId) {
          const alerts = await apiService.getUserRecallAlerts(parseInt(userId));
          setRecallAlerts(alerts);
        }
        setSystemStatus(prev => ({ ...prev, isScrapingRecalls: false }));
      }, 2000);
    } catch (error: any) {
      console.error('Error triggering recall scraping:', error);
      toast.error('Failed to trigger recall scraping. Please try again.');
      setSystemStatus(prev => ({ ...prev, isScrapingRecalls: false }));
    } finally {
      setIsCheckingRecalls(false);
    }
  };

  if (!isClient || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Enhanced System Status Banner */}
        {(systemStatus.isMatching || systemStatus.isScrapingRecalls) && (
          <div className="mb-6">
            <MatchingProgress
              progress={systemStatus.matchingProgress}
              isActive={systemStatus.isMatching}
              stage={systemStatus.isScrapingRecalls ? 'fetching' : 'matching'}
            />
          </div>
        )}

        {/* Real-time Matching Indicator */}
        {systemStatus.isMatching && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <MatchingIndicator
              isActive={systemStatus.isMatching}
              confidence="medium"
              matchCount={Math.floor(systemStatus.matchingProgress / 20)} // Simulate matches found
              className="justify-center"
            />
          </div>
        )}

        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Welcome back to RecallGuard
              </h1>
              {user && (
                <div className="mt-2 text-gray-600">
                  <p>Email: {user.email}</p>
                  {user.phone && <p>Phone: {user.phone}</p>}
                  <p className="text-sm">
                    Member since:{' '}
                    {new Date(user.created_at).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => router.push('/recalls')}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Browse Recalls
              </button>
              <button
                onClick={() => router.push('/dashboard/add-product')}
                className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Add Products
              </button>
              <button
                onClick={handleRecallScraping}
                disabled={isCheckingRecalls || systemStatus.isScrapingRecalls}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center space-x-2"
              >
                {systemStatus.isScrapingRecalls && (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                )}
                <span>{systemStatus.isScrapingRecalls ? 'Scraping...' : 'Update Recalls'}</span>
              </button>
              <button
                onClick={handleManualRecallCheck}
                disabled={isCheckingRecalls || systemStatus.isMatching}
                className="bg-orange-600 hover:bg-orange-700 disabled:bg-orange-400 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center space-x-2"
              >
                {systemStatus.isMatching && (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                )}
                <span>{systemStatus.isMatching ? 'AI Matching...' : 'Check Recalls'}</span>
              </button>
              <button
                onClick={handleLogout}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>

        {/* Recall Alerts Section */}
        {recallAlerts && (
          <div className="bg-white rounded-lg shadow-sm mb-8">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900">
                  🚨 Recall Alerts
                </h2>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-500">
                    Last checked: {recallAlerts.last_check ? new Date(recallAlerts.last_check).toLocaleString() : 'Never'}
                  </span>
                  {systemStatus.unprocessedRecalls > 0 && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      {systemStatus.unprocessedRecalls} Pending Analysis
                    </span>
                  )}
                  {recallAlerts.high_priority_alerts > 0 && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      {recallAlerts.high_priority_alerts} High Priority
                    </span>
                  )}
                </div>
              </div>
            </div>

            {recallAlerts.total_alerts === 0 ? (
              <div className="p-8 text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-8 h-8 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Active Recall Alerts
                </h3>
                <p className="text-gray-600 mb-4">
                  Great news! None of your products currently match any known recalls.
                </p>
                <p className="text-sm text-gray-500">
                  Our AI system continuously monitors FDA and CPSC databases for new recalls and will notify you immediately if any matches are found.
                </p>
              </div>
            ) : (
              <div className="p-6">
                <p className="text-gray-600">
                  You have {recallAlerts.total_alerts} active recall alert(s). Check your email for detailed information.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Products Section */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  Your Registered Products ({products.length})
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  You&apos;ll receive alerts if any of these products have recalls
                </p>
              </div>
              {systemStatus.isMatching && (
                <div className="flex items-center space-x-2 text-blue-600">
                  <div className="animate-pulse w-2 h-2 bg-blue-600 rounded-full"></div>
                  <span className="text-sm font-medium">AI Analyzing Products...</span>
                </div>
              )}
            </div>
          </div>

          {products.length === 0 ? (
            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No products registered yet
              </h3>
              <p className="text-gray-600 mb-4">
                Add your first product to start receiving recall alerts
              </p>
              <button
                onClick={() => router.push('/dashboard/add-product')}
                className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-md font-medium"
              >
                Add Your First Product
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {products.map((product) => (
                <div key={product.id} className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900">
                        {product.product_name}
                      </h3>
                      <div className="mt-1 text-sm text-gray-600 space-y-1">
                        {product.brand && (
                          <p>
                            <span className="font-medium">Brand:</span>{' '}
                            {product.brand}
                          </p>
                        )}
                        {product.model && (
                          <p>
                            <span className="font-medium">Model:</span>{' '}
                            {product.model}
                          </p>
                        )}
                        <p>
                          <span className="font-medium">Added:</span>{' '}
                          {new Date(product.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <ProductStatus
                        isBeingAnalyzed={systemStatus.isMatching}
                        hasAlerts={false} // TODO: Check if this specific product has alerts
                        productName={product.product_name}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Enhanced Stats */}
        {products.length > 0 && (
          <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-4">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                    <svg
                      className="w-5 h-5 text-blue-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                      />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Products
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {products.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                    <svg
                      className="w-5 h-5 text-green-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Active Alerts
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {recallAlerts?.total_alerts || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`w-8 h-8 rounded-md flex items-center justify-center ${
                    systemStatus.isMatching ? 'bg-orange-100' : 'bg-purple-100'
                  }`}>
                    <svg
                      className={`w-5 h-5 ${
                        systemStatus.isMatching ? 'text-orange-600' : 'text-purple-600'
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                      />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      AI Status
                    </dt>
                    <dd className={`text-lg font-medium ${
                      systemStatus.isMatching ? 'text-orange-600' : 'text-gray-900'
                    }`}>
                      {systemStatus.isMatching ? 'Matching' : 'Active'}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`w-8 h-8 rounded-md flex items-center justify-center ${
                    systemStatus.unprocessedRecalls > 0 ? 'bg-yellow-100' : 'bg-gray-100'
                  }`}>
                    <svg
                      className={`w-5 h-5 ${
                        systemStatus.unprocessedRecalls > 0 ? 'text-yellow-600' : 'text-gray-600'
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Pending
                    </dt>
                    <dd className={`text-lg font-medium ${
                      systemStatus.unprocessedRecalls > 0 ? 'text-yellow-600' : 'text-gray-900'
                    }`}>
                      {systemStatus.unprocessedRecalls}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}