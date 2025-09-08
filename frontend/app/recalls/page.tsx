'use client';

import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';
import toast from 'react-hot-toast';

export default function RecallsPage() {
  const [recalls, setRecalls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecall, setSelectedRecall] = useState<any>(null);
  const [isClient, setIsClient] = useState(false);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecalls, setTotalRecalls] = useState(0);
  const [perPage, setPerPage] = useState(20);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showProcessed, setShowProcessed] = useState<boolean | undefined>(undefined);
  const [sortBy, setSortBy] = useState('recall_date');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Stats
  const [sources, setSources] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [stats, setStats] = useState<any>({});

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (isClient) {
      fetchRecalls();
    }
  }, [isClient, currentPage, perPage, selectedSource, selectedCategory, showProcessed, sortBy, sortOrder]);

  const fetchRecalls = async () => {
    setLoading(true);
    try {
      const response = await apiService.getRecalls({
        page: currentPage,
        per_page: perPage,
        search: searchTerm || undefined,
        source: selectedSource || undefined,
        category: selectedCategory || undefined,
        processed: showProcessed,
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      setRecalls(response.recalls);
      setTotalPages(response.pagination.pages);
      setTotalRecalls(response.pagination.total);
      
      if (response.stats) {
        setStats(response.stats);
        setSources(response.stats.sources || []);
        setCategories(response.stats.categories || []);
      }
    } catch (error) {
      console.error('Error fetching recalls:', error);
      toast.error('Failed to load recalls');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchRecalls();
  };

  const viewRecallDetails = async (recall: any) => {
    try {
      const details = await apiService.getRecallDetail(recall.id);
      setSelectedRecall(details);
    } catch (error) {
      toast.error('Failed to load recall details');
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getCategoryBadgeColor = (category: string) => {
    const colors: any = {
      food: 'bg-green-100 text-green-800',
      drug: 'bg-blue-100 text-blue-800',
      medical_device: 'bg-purple-100 text-purple-800',
      consumer_product: 'bg-yellow-100 text-yellow-800',
      automotive: 'bg-red-100 text-red-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const getSourceBadgeColor = (source: string) => {
    const colors: any = {
      FDA: 'bg-blue-100 text-blue-800',
      CPSC: 'bg-orange-100 text-orange-800',
      NHTSA: 'bg-red-100 text-red-800',
      USDA: 'bg-green-100 text-green-800',
    };
    return colors[source] || 'bg-gray-100 text-gray-800';
  };

  if (!isClient) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading recalls...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Recall Database</h1>
          <p className="mt-2 text-gray-600">
            Browse and search through {stats.total_recalls || 0} collected recalls
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm font-medium text-gray-500">Total Recalls</div>
            <div className="mt-1 text-2xl font-semibold text-gray-900">
              {stats.total_recalls || 0}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm font-medium text-gray-500">Unprocessed</div>
            <div className="mt-1 text-2xl font-semibold text-orange-600">
              {stats.unprocessed_recalls || 0}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm font-medium text-gray-500">Sources</div>
            <div className="mt-1 text-2xl font-semibold text-gray-900">
              {sources.length}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm font-medium text-gray-500">Categories</div>
            <div className="mt-1 text-2xl font-semibold text-gray-900">
              {categories.length}
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <form onSubmit={handleSearch}>
                <input
                  type="text"
                  placeholder="Search recalls..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </form>
            </div>

            {/* Source Filter */}
            <div>
              <select
                value={selectedSource}
                onChange={(e) => {
                  setSelectedSource(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Sources</option>
                {sources.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Categories</option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category?.replace('_', ' ')}
                  </option>
                ))}
              </select>
            </div>

            {/* Processed Filter */}
            <div>
              <select
                value={showProcessed === undefined ? '' : showProcessed.toString()}
                onChange={(e) => {
                  setShowProcessed(e.target.value === '' ? undefined : e.target.value === 'true');
                  setCurrentPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Status</option>
                <option value="false">Unprocessed</option>
                <option value="true">Processed</option>
              </select>
            </div>

            {/* Sort */}
            <div>
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [field, order] = e.target.value.split('-');
                  setSortBy(field);
                  setSortOrder(order);
                  setCurrentPage(1);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="recall_date-desc">Newest First</option>
                <option value="recall_date-asc">Oldest First</option>
                <option value="created_at-desc">Recently Added</option>
                <option value="product_name-asc">Product A-Z</option>
                <option value="brand-asc">Brand A-Z</option>
              </select>
            </div>
          </div>
        </div>

        {/* Recalls Table */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-flex items-center">
                <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="ml-2">Loading recalls...</span>
              </div>
            </div>
          ) : recalls.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No recalls found matching your criteria
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Source
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recalls.map((recall) => (
                    <tr key={recall.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {recall.product_name}
                        </div>
                        {recall.brand && (
                          <div className="text-sm text-gray-500">
                            {recall.brand} {recall.model && `- ${recall.model}`}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSourceBadgeColor(recall.source)}`}>
                          {recall.source}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {recall.category && (
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryBadgeColor(recall.category)}`}>
                            {recall.category.replace('_', ' ')}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatDate(recall.recall_date)}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          recall.processed 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {recall.processed ? 'Processed' : 'Pending'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <button
                          onClick={() => viewRecallDetails(recall)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                        >
                          View
                        </button>
                        {recall.link && (
                          <a
                            href={recall.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Source →
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing{' '}
                      <span className="font-medium">{(currentPage - 1) * perPage + 1}</span> to{' '}
                      <span className="font-medium">
                        {Math.min(currentPage * perPage, totalRecalls)}
                      </span>{' '}
                      of <span className="font-medium">{totalRecalls}</span> results
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <select
                      value={perPage}
                      onChange={(e) => {
                        setPerPage(Number(e.target.value));
                        setCurrentPage(1);
                      }}
                      className="px-3 py-1 border border-gray-300 rounded-md text-sm"
                    >
                      <option value={10}>10 per page</option>
                      <option value={20}>20 per page</option>
                      <option value={50}>50 per page</option>
                      <option value={100}>100 per page</option>
                    </select>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      {[...Array(Math.min(5, totalPages))].map((_, i) => {
                        const page = currentPage - 2 + i;
                        if (page > 0 && page <= totalPages) {
                          return (
                            <button
                              key={page}
                              onClick={() => setCurrentPage(page)}
                              className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                page === currentPage
                                  ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                  : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                              }`}
                            >
                              {page}
                            </button>
                          );
                        }
                        return null;
                      })}
                      <button
                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage === totalPages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Recall Details Modal */}
        {selectedRecall && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">Recall Details</h2>
                  <button
                    onClick={() => setSelectedRecall(null)}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {selectedRecall.product_name}
                    </h3>
                    <div className="flex flex-wrap gap-2 mb-4">
                      <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getSourceBadgeColor(selectedRecall.source)}`}>
                        {selectedRecall.source}
                      </span>
                      {selectedRecall.category && (
                        <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getCategoryBadgeColor(selectedRecall.category)}`}>
                          {selectedRecall.category.replace('_', ' ')}
                        </span>
                      )}
                      <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
                        selectedRecall.processed 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {selectedRecall.processed ? 'Processed' : 'Pending'}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500">Brand</label>
                      <p className="mt-1 text-sm text-gray-900">{selectedRecall.brand || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">Model</label>
                      <p className="mt-1 text-sm text-gray-900">{selectedRecall.model || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">Recall Date</label>
                      <p className="mt-1 text-sm text-gray-900">{formatDate(selectedRecall.recall_date)}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">Added to Database</label>
                      <p className="mt-1 text-sm text-gray-900">{formatDate(selectedRecall.created_at)}</p>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-500 mb-2">Details</label>
                    <div className="bg-gray-50 p-4 rounded-md">
                      <p className="text-sm text-gray-900 whitespace-pre-wrap">
                        {selectedRecall.details || 'No details available'}
                      </p>
                    </div>
                  </div>

                  {selectedRecall.link && (
                    <div>
                      <a
                        href={selectedRecall.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        View Original Source →
                      </a>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                    <div>
                      <label className="block text-sm font-medium text-gray-500">Alerts Sent</label>
                      <p className="mt-1 text-sm text-gray-900">{selectedRecall.alerts_count || 0} alerts</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500">Affected Users</label>
                      <p className="mt-1 text-sm text-gray-900">{selectedRecall.affected_users || 0} users</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}