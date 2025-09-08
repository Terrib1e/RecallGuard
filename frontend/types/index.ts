export interface Product {
  id: number;
  user_id: number;
  product_name: string;
  brand?: string;
  model?: string;
  created_at: string;
}

export interface ProductCreate {
  product_name: string;
  brand?: string;
  model?: string;
}

export interface User {
  id: number;
  email: string;
  phone?: string;
  created_at: string;
}

export interface UserCreate {
  email: string;
  phone?: string;
  products?: ProductCreate[];
}

export interface UserWithProducts extends User {
  products: Product[];
}