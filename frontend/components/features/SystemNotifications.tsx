'use client';

import { useState, useEffect } from 'react';
// Using a simple X icon instead of lucide-react
const XIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

export interface SystemNotification {
  id: string;
  type: 'matching' | 'scraping' | 'alert' | 'success' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  autoHide?: boolean;
  duration?: number;
}

interface SystemNotificationsProps {
  notifications: SystemNotification[];
  onDismiss: (id: string) => void;
}

export default function SystemNotifications({ notifications, onDismiss }: SystemNotificationsProps) {
  const [visibleNotifications, setVisibleNotifications] = useState<SystemNotification[]>([]);

  useEffect(() => {
    setVisibleNotifications(notifications);

    // Auto-hide notifications
    notifications.forEach(notification => {
      if (notification.autoHide) {
        setTimeout(() => {
          onDismiss(notification.id);
        }, notification.duration || 5000);
      }
    });
  }, [notifications, onDismiss]);

  const getNotificationStyles = (type: SystemNotification['type']) => {
    switch (type) {
      case 'matching':
        return {
          bg: 'bg-blue-50 border-blue-200',
          icon: '🧠',
          iconBg: 'bg-blue-100 text-blue-600',
          titleColor: 'text-blue-800',
          messageColor: 'text-blue-600'
        };
      case 'scraping':
        return {
          bg: 'bg-purple-50 border-purple-200',
          icon: '🔍',
          iconBg: 'bg-purple-100 text-purple-600',
          titleColor: 'text-purple-800',
          messageColor: 'text-purple-600'
        };
      case 'alert':
        return {
          bg: 'bg-red-50 border-red-200',
          icon: '🚨',
          iconBg: 'bg-red-100 text-red-600',
          titleColor: 'text-red-800',
          messageColor: 'text-red-600'
        };
      case 'success':
        return {
          bg: 'bg-green-50 border-green-200',
          icon: '✅',
          iconBg: 'bg-green-100 text-green-600',
          titleColor: 'text-green-800',
          messageColor: 'text-green-600'
        };
      default:
        return {
          bg: 'bg-gray-50 border-gray-200',
          icon: 'ℹ️',
          iconBg: 'bg-gray-100 text-gray-600',
          titleColor: 'text-gray-800',
          messageColor: 'text-gray-600'
        };
    }
  };

  if (visibleNotifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-3 max-w-sm">
      {visibleNotifications.map((notification) => {
        const styles = getNotificationStyles(notification.type);

        return (
          <div
            key={notification.id}
            className={`relative p-4 rounded-lg border shadow-lg ${styles.bg} transform transition-all duration-300 animate-in slide-in-from-right`}
          >
            <div className="flex items-start space-x-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${styles.iconBg}`}>
                <span className="text-sm">{styles.icon}</span>
              </div>

              <div className="flex-1 min-w-0">
                <h4 className={`text-sm font-medium ${styles.titleColor}`}>
                  {notification.title}
                </h4>
                <p className={`mt-1 text-sm ${styles.messageColor}`}>
                  {notification.message}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {notification.timestamp.toLocaleTimeString()}
                </p>
              </div>

              <button
                onClick={() => onDismiss(notification.id)}
                className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
                title="Dismiss notification"
                aria-label="Dismiss notification"
              >
                <XIcon />
              </button>
            </div>

            {/* Progress indicator for ongoing activities */}
            {(notification.type === 'matching' || notification.type === 'scraping') && (
              <div className="mt-3">
                <div className="w-full bg-white bg-opacity-50 rounded-full h-1">
                  <div className="bg-current h-1 rounded-full animate-pulse" style={{ width: '60%' }} />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// Hook for managing system notifications
export function useSystemNotifications() {
  const [notifications, setNotifications] = useState<SystemNotification[]>([]);

  const addNotification = (notification: Omit<SystemNotification, 'id' | 'timestamp'>) => {
    const newNotification: SystemNotification = {
      ...notification,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
    };

    setNotifications(prev => [...prev, newNotification]);
    return newNotification.id;
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  // Predefined notification types
  const notifyAIMatching = (productCount: number) => {
    return addNotification({
      type: 'matching',
      title: 'AI Analysis Started',
      message: `Analyzing ${productCount} products for recall matches using advanced fuzzy matching and semantic analysis.`,
      autoHide: false,
    });
  };

  const notifyRecallScraping = (sources: string[]) => {
    return addNotification({
      type: 'scraping',
      title: 'Fetching Latest Recalls',
      message: `Collecting recent recalls from ${sources.join(', ')} databases.`,
      autoHide: true,
      duration: 8000,
    });
  };

  const notifyMatchFound = (productName: string, confidence: string) => {
    return addNotification({
      type: 'alert',
      title: 'Potential Recall Match',
      message: `Found ${confidence} confidence match for "${productName}". Check your alerts for details.`,
      autoHide: false,
    });
  };

  const notifyAnalysisComplete = (matchCount: number) => {
    return addNotification({
      type: 'success',
      title: 'Analysis Complete',
      message: matchCount > 0
        ? `Analysis complete! Found ${matchCount} potential matches.`
        : 'Analysis complete! No recall matches found for your products.',
      autoHide: true,
      duration: 6000,
    });
  };

  return {
    notifications,
    addNotification,
    dismissNotification,
    clearAllNotifications,
    notifyAIMatching,
    notifyRecallScraping,
    notifyMatchFound,
    notifyAnalysisComplete,
  };
}