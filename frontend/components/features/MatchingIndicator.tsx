'use client';

import { useState, useEffect } from 'react';

interface MatchingIndicatorProps {
  isActive: boolean;
  confidence?: 'high' | 'medium' | 'low';
  matchCount?: number;
  className?: string;
}

export default function MatchingIndicator({
  isActive,
  confidence = 'medium',
  matchCount = 0,
  className = ''
}: MatchingIndicatorProps) {
  const [pulseCount, setPulseCount] = useState(0);

  useEffect(() => {
    if (isActive) {
      const interval = setInterval(() => {
        setPulseCount(prev => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [isActive]);

  if (!isActive) {
    return (
      <div className={`flex items-center space-x-2 text-green-600 ${className}`}>
        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
        <span className="text-sm font-medium">Monitoring Active</span>
      </div>
    );
  }

  const getConfidenceColor = () => {
    switch (confidence) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-orange-600 bg-orange-100';
      case 'low': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-blue-600 bg-blue-100';
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {/* Animated AI Brain Icon */}
      <div className="relative">
        <svg
          className="w-5 h-5 text-blue-600 animate-pulse"
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

        {/* Pulse ring animation */}
        <div className="absolute inset-0 rounded-full border-2 border-blue-400 animate-ping opacity-75"></div>
      </div>

      {/* Status text */}
      <div className="flex flex-col">
        <span className="text-sm font-medium text-blue-600">
          🧠 AI Analyzing Products...
        </span>
        {matchCount > 0 && (
          <span className={`text-xs px-2 py-0.5 rounded-full ${getConfidenceColor()}`}>
            {matchCount} potential match{matchCount !== 1 ? 'es' : ''} found
          </span>
        )}
      </div>

      {/* Progress dots */}
      <div className="flex space-x-1">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
              (pulseCount % 3) === i ? 'bg-blue-600 scale-125' : 'bg-blue-300'
            }`}
          />
        ))}
      </div>
    </div>
  );
}

// Enhanced progress bar component
interface MatchingProgressProps {
  progress: number;
  isActive: boolean;
  stage?: 'fetching' | 'parsing' | 'matching' | 'complete';
}

export function MatchingProgress({ progress, isActive, stage = 'matching' }: MatchingProgressProps) {
  const getStageInfo = () => {
    switch (stage) {
      case 'fetching':
        return { icon: '🔍', text: 'Fetching recall data...', color: 'bg-blue-500' };
      case 'parsing':
        return { icon: '📄', text: 'Processing recall text...', color: 'bg-orange-500' };
      case 'matching':
        return { icon: '🧠', text: 'AI matching products...', color: 'bg-purple-500' };
      case 'complete':
        return { icon: '✅', text: 'Analysis complete!', color: 'bg-green-500' };
      default:
        return { icon: '⚡', text: 'Processing...', color: 'bg-blue-500' };
    }
  };

  if (!isActive) return null;

  const stageInfo = getStageInfo();

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border-l-4 border-blue-500">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{stageInfo.icon}</span>
          <span className="font-medium text-gray-900">{stageInfo.text}</span>
        </div>
        <span className="text-sm text-gray-600">{Math.round(progress)}%</span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${stageInfo.color}`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>

      {stage === 'matching' && progress > 0 && (
        <div className="mt-2 text-xs text-gray-500">
          Using fuzzy matching and semantic analysis to compare your products with {Math.floor(progress * 10)} recall records...
        </div>
      )}
    </div>
  );
}

// Product status indicator for individual products
interface ProductStatusProps {
  isBeingAnalyzed: boolean;
  hasAlerts: boolean;
  productName: string;
}

export function ProductStatus({ isBeingAnalyzed, hasAlerts, productName }: ProductStatusProps) {
  if (isBeingAnalyzed) {
    return (
      <div className="flex items-center space-x-2 text-blue-600">
        <div className="animate-spin rounded-full h-3 w-3 border border-blue-600 border-t-transparent"></div>
        <span className="text-xs font-medium">Analyzing...</span>
      </div>
    );
  }

  if (hasAlerts) {
    return (
      <div className="flex items-center space-x-2 text-red-600">
        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
        <span className="text-xs font-medium">Alert Found</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-green-600">
      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
      <span className="text-xs font-medium">Safe</span>
    </div>
  );
}