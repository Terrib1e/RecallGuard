'use client';

import { useState } from 'react';
import { ProductCreate } from '@/types';

interface ProductFormProps {
  onSubmit: (product: ProductCreate) => void;
  onRemove?: () => void;
  canRemove?: boolean;
  initialData?: ProductCreate;
}

export default function ProductForm({
  onSubmit,
  onRemove,
  canRemove = false,
  initialData,
}: ProductFormProps) {
  const [product, setProduct] = useState<ProductCreate>({
    product_name: initialData?.product_name || '',
    brand: initialData?.brand || '',
    model: initialData?.model || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (product.product_name.trim()) {
      onSubmit(product);
    }
  };

  const handleChange = (field: keyof ProductCreate, value: string) => {
    setProduct((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Product Details</h3>
        {canRemove && onRemove && (
          <button
            type="button"
            onClick={onRemove}
            className="text-red-600 hover:text-red-700 text-sm font-medium"
          >
            Remove Product
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="product_name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Product Name *
          </label>
          <input
            type="text"
            id="product_name"
            required
            value={product.product_name}
            onChange={(e) => handleChange('product_name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., iPhone 15"
          />
        </div>

        <div>
          <label
            htmlFor="brand"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Brand
          </label>
          <input
            type="text"
            id="brand"
            value={product.brand}
            onChange={(e) => handleChange('brand', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., Apple"
          />
        </div>

        <div>
          <label
            htmlFor="model"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Model
          </label>
          <input
            type="text"
            id="model"
            value={product.model}
            onChange={(e) => handleChange('model', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., A2846"
          />
        </div>
      </form>
    </div>
  );
}