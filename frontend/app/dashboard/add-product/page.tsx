'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { apiService } from '@/services/api';
import { ProductCreate } from '@/types';

export default function AddProductPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [products, setProducts] = useState<ProductCreate[]>([
    { product_name: '', brand: '', model: '' },
  ]);

  const handleProductUpdate = (index: number, product: ProductCreate) => {
    setProducts((prev) => {
      const updated = [...prev];
      updated[index] = product;
      return updated;
    });
  };

  const addProduct = () => {
    setProducts((prev) => [
      ...prev,
      { product_name: '', brand: '', model: '' },
    ]);
  };

  const removeProduct = (index: number) => {
    if (products.length > 1) {
      setProducts((prev) => prev.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const userId = localStorage.getItem('userId');
    if (!userId) {
      router.push('/auth/register');
      return;
    }

    setIsLoading(true);

    try {
      // Filter out empty products
      const validProducts = products.filter(
        (product) => product.product_name.trim() !== ''
      );

      if (validProducts.length === 0) {
        toast.error('Please add at least one product');
        setIsLoading(false);
        return;
      }

            // Add each product individually using the proper API endpoint
      const userIdNum = parseInt(userId);
      const addedProducts = [];

      for (const product of validProducts) {
        const addedProduct = await apiService.addProductToUser(userIdNum, product);
        addedProducts.push(addedProduct);
      }

      toast.success(`Successfully added ${validProducts.length} product(s)!`);
      router.push('/dashboard');
    } catch (error: any) {
      console.error('Add product error:', error);
      toast.error(
        error.response?.data?.detail || 'Failed to add products. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="text-primary-600 hover:text-primary-700 font-medium mb-4 inline-flex items-center"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            Add Your Products
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            Add products to your account to start receiving recall alerts
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {products.map((product, index) => (
            <ProductForm
              key={index}
              initialData={product}
              onUpdate={(updatedProduct) => handleProductUpdate(index, updatedProduct)}
              onRemove={() => removeProduct(index)}
              canRemove={products.length > 1}
            />
          ))}

          <div className="flex justify-center">
            <button
              type="button"
              onClick={addProduct}
              className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-md font-medium"
            >
              Add Another Product
            </button>
          </div>

          <div className="flex justify-center pt-6">
            <button
              type="submit"
              disabled={isLoading}
              className="bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white px-8 py-3 rounded-md text-lg font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              {isLoading ? 'Adding Products...' : 'Add Products'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface ProductFormProps {
  initialData: ProductCreate;
  onUpdate: (product: ProductCreate) => void;
  onRemove: () => void;
  canRemove: boolean;
}

function ProductForm({ initialData, onUpdate, onRemove, canRemove }: ProductFormProps) {
  const [product, setProduct] = useState<ProductCreate>(initialData);

  const handleChange = (field: keyof ProductCreate, value: string) => {
    const updated = { ...product, [field]: value };
    setProduct(updated);
    onUpdate(updated);
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">Product Details</h3>
        {canRemove && (
          <button
            type="button"
            onClick={onRemove}
            className="text-red-600 hover:text-red-700 text-sm font-medium"
          >
            Remove Product
          </button>
        )}
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Product Name *
          </label>
          <input
            type="text"
            required
            value={product.product_name}
            onChange={(e) => handleChange('product_name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., iPhone 15"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Brand
          </label>
          <input
            type="text"
            value={product.brand}
            onChange={(e) => handleChange('brand', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., Apple"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Model
          </label>
          <input
            type="text"
            value={product.model}
            onChange={(e) => handleChange('model', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., A2846"
          />
        </div>
      </div>
    </div>
  );
}