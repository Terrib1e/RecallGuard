import axios from 'axios';
import { User, UserCreate, UserWithProducts, Product, ProductCreate } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Health check
  async healthCheck(): Promise<{
    status: string;
    service: string;
    features: Record<string, any>;
    stats: {
      users: number;
      products: number;
      recalls: number;
      unprocessed_recalls: number;
      alerts: number;
    };
  }> {
    const response = await api.get('/health');
    return response.data;
  },

  // Create user with products
  async createUser(userData: UserCreate): Promise<UserWithProducts> {
    const response = await api.post('/users', userData);
    return response.data;
  },

  // Get user by ID
  async getUser(userId: number): Promise<User> {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  },

  // Get user's products
  async getUserProducts(userId: number): Promise<Product[]> {
    const response = await api.get(`/users/${userId}/products`);
    return response.data;
  },

  // Add product to user
  async addProductToUser(userId: number, productData: ProductCreate): Promise<Product> {
    const response = await api.post(`/users/${userId}/products`, productData);
    return response.data;
  },

  // Get user's recall alerts
  async getUserRecallAlerts(userId: number): Promise<any> {
    const response = await api.get(`/users/${userId}/recall-alerts`);
    return response.data;
  },

  // Trigger manual recall check (admin)
  async triggerManualRecallCheck(): Promise<any> {
    const response = await api.post('/admin/manual-recall-check');
    return response.data;
  },

  // Trigger recall scraping (admin)
  async triggerRecallScraping(daysBack: number = 7): Promise<any> {
    const response = await api.post(`/admin/scrape-recalls?days_back=${daysBack}`);
    return response.data;
  },

  // Get recalls with pagination and filters
  async getRecalls(params: {
    page?: number;
    per_page?: number;
    search?: string;
    source?: string;
    category?: string;
    processed?: boolean;
    sort_by?: string;
    sort_order?: string;
  } = {}): Promise<any> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value.toString());
      }
    });
    
    const response = await api.get(`/recalls?${queryParams.toString()}`);
    return response.data;
  },
  
  // Get single recall details
  async getRecallDetail(recallId: number): Promise<any> {
    const response = await api.get(`/recalls/${recallId}`);
    return response.data;
  },
};

export default api;