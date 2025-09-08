"""AI-powered product matching service for RecallGuard."""

import os
import logging
from typing import List, Dict, Tuple
from rapidfuzz import fuzz, process
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class AIProductMatcher:
    """AI service to match user products with recalls."""

    def __init__(self):
        self.min_match_score = 50  # Lowered minimum similarity score for better matching
        self.brand_weight = 0.3
        self.product_weight = 0.5
        self.model_weight = 0.2

    def find_matches(self, user_products: List[Dict], recalls: List[Dict]) -> List[Dict]:
        """Find matches between user products and recalls."""
        matches = []

        for user_product in user_products:
            for recall in recalls:
                match_score, match_details = self._calculate_match_score(user_product, recall)

                if match_score >= self.min_match_score:
                    matches.append({
                        'user_product': user_product,
                        'recall': recall,
                        'match_score': match_score,
                        'match_details': match_details,
                        'confidence': self._get_confidence_level(match_score),
                        'match_reasons': self._get_match_reasons(match_details)
                    })
                elif match_score > 30:  # Log near-misses for debugging
                    logger.info(f"Near-miss: {user_product.get('product_name')} vs {recall.get('product_name')} - Score: {match_score:.1f}")

        # Sort by match score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches

    def _calculate_match_score(self, user_product: Dict, recall: Dict) -> Tuple[float, Dict]:
        """Calculate similarity score between user product and recall."""
        details = {}

        # Extract product information
        user_name = self._normalize_text(user_product.get('product_name', ''))
        user_brand = self._normalize_text(user_product.get('brand', ''))
        user_model = self._normalize_text(user_product.get('model', ''))

        recall_name = self._normalize_text(recall.get('product_name', ''))
        recall_brand = self._normalize_text(recall.get('brand', ''))
        recall_model = self._normalize_text(recall.get('model', ''))

        # Calculate individual scores
        name_score = self._fuzzy_match(user_name, recall_name)
        
        # If brand is missing in recall, check if brand name is in the product name
        if not recall_brand and user_brand:
            if user_brand.lower() in recall_name.lower():
                brand_score = 80  # Good match if brand is in product name
            else:
                brand_score = 0
        else:
            brand_score = self._fuzzy_match(user_brand, recall_brand) if user_brand and recall_brand else 0
            
        # Similar for model - check in product name if not separate
        if not recall_model and user_model:
            if user_model.lower() in recall_name.lower():
                model_score = 80
            else:
                model_score = 0
        else:
            model_score = self._fuzzy_match(user_model, recall_model) if user_model and recall_model else 0

        # Store individual scores
        details['name_score'] = name_score
        details['brand_score'] = brand_score
        details['model_score'] = model_score

        # Additional semantic matching
        keyword_score = self._keyword_matching(user_product, recall)
        details['keyword_score'] = keyword_score

        # Category matching bonus
        category_bonus = self._get_category_bonus(user_product, recall)
        details['category_bonus'] = category_bonus

        # Calculate weighted final score
        final_score = (
            name_score * self.product_weight +
            brand_score * self.brand_weight +
            model_score * self.model_weight +
            keyword_score * 0.1 +  # Small weight for keywords
            category_bonus
        )

        # Boost score for exact brand matches
        if brand_score > 90 and user_brand:
            final_score = min(100, final_score * 1.2)
            details['exact_brand_match'] = True

        # Boost score for exact model matches
        if model_score > 90 and user_model:
            final_score = min(100, final_score * 1.1)
            details['exact_model_match'] = True

        return final_score, details

    def _fuzzy_match(self, text1: str, text2: str) -> float:
        """Calculate fuzzy similarity between two texts."""
        if not text1 or not text2:
            return 0.0

        # Use multiple fuzzy matching algorithms
        ratio = fuzz.ratio(text1, text2)
        partial_ratio = fuzz.partial_ratio(text1, text2)
        token_sort_ratio = fuzz.token_sort_ratio(text1, text2)
        token_set_ratio = fuzz.token_set_ratio(text1, text2)

        # Return the best score
        return max(ratio, partial_ratio, token_sort_ratio, token_set_ratio)

    def _keyword_matching(self, user_product: Dict, recall: Dict) -> float:
        """Match based on important keywords."""
        user_text = f"{user_product.get('product_name', '')} {user_product.get('brand', '')} {user_product.get('model', '')}"
        recall_text = f"{recall.get('product_name', '')} {recall.get('brand', '')} {recall.get('model', '')} {recall.get('details', '')}"

        user_keywords = self._extract_keywords(user_text)
        recall_keywords = self._extract_keywords(recall_text)

        if not user_keywords:
            return 0.0

        matches = 0
        for keyword in user_keywords:
            if any(fuzz.ratio(keyword, recall_kw) > 80 for recall_kw in recall_keywords):
                matches += 1

        return (matches / len(user_keywords)) * 100

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        text = self._normalize_text(text)

        # Remove common stop words and short words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        words = [word for word in text.split() if len(word) > 2 and word.lower() not in stop_words]

        # Extract model numbers and important identifiers
        keywords = []
        for word in words:
            # Keep alphanumeric identifiers (likely model numbers)
            if re.match(r'^[A-Za-z0-9\-]+$', word) and len(word) > 2:
                keywords.append(word)
            # Keep significant words
            elif len(word) > 3:
                keywords.append(word)

        return keywords[:10]  # Limit to most important keywords

    def _get_category_bonus(self, user_product: Dict, recall: Dict) -> float:
        """Give bonus points for category matching."""
        # Simple category inference based on product names
        user_categories = self._infer_categories(user_product.get('product_name', ''))
        recall_categories = self._infer_categories(recall.get('product_name', ''))

        if user_categories.intersection(recall_categories):
            return 10.0  # Bonus points for category match

        return 0.0

    def _infer_categories(self, product_name: str) -> set:
        """Infer product categories from name - expanded for all FDA categories."""
        product_name = product_name.lower()
        categories = set()

        # FDA Food products
        if any(term in product_name for term in ['food', 'snack', 'drink', 'beverage', 'meat', 'dairy', 'frozen', 'supplement', 'nutrition']):
            categories.add('food')

        # FDA Drug products
        if any(term in product_name for term in ['drug', 'medication', 'medicine', 'pharmaceutical', 'pill', 'tablet', 'capsule']):
            categories.add('drug')

        # FDA Medical devices
        if any(term in product_name for term in ['medical', 'device', 'monitor', 'diagnostic', 'surgical', 'implant', 'catheter']):
            categories.add('medical_device')

        # FDA Animal/Veterinary products
        if any(term in product_name for term in ['pet', 'dog', 'cat', 'animal', 'veterinary', 'livestock', 'feed']):
            categories.add('animal_veterinary')

        # FDA Cosmetics
        if any(term in product_name for term in ['cosmetic', 'makeup', 'beauty', 'skincare', 'lotion', 'shampoo', 'lipstick']):
            categories.add('cosmetics')

        # FDA Tobacco products
        if any(term in product_name for term in ['tobacco', 'cigarette', 'vape', 'e-cigarette', 'nicotine']):
            categories.add('tobacco')

        # FDA Biologics
        if any(term in product_name for term in ['vaccine', 'blood', 'plasma', 'biologic', 'antibody']):
            categories.add('biologics')

        # Electronics
        if any(term in product_name for term in ['phone', 'iphone', 'android', 'tablet', 'laptop', 'computer', 'tv', 'television']):
            categories.add('electronics')

        # Automotive (NHTSA)
        if any(term in product_name for term in ['car', 'vehicle', 'tire', 'brake', 'engine', 'automotive', 'airbag']):
            categories.add('automotive')

        # Children's products (CPSC)
        if any(term in product_name for term in ['toy', 'baby', 'child', 'kid', 'stroller', 'crib', 'playground', 'kidkraft']):
            categories.add('children')

        # Kitchen/Appliances
        if any(term in product_name for term in ['refrigerator', 'washer', 'dryer', 'microwave', 'oven', 'dishwasher', 'kitchen', 'boiler']):
            categories.add('appliance')

        # Consumer products (CPSC)
        if any(term in product_name for term in ['consumer', 'household', 'furniture', 'ladder', 'tool']):
            categories.add('consumer_product')

        return categories

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        if not text:
            return ''

        # Convert to lowercase and remove extra whitespace
        text = ' '.join(text.lower().split())

        # Remove special characters but keep alphanumeric and hyphens
        text = re.sub(r'[^a-z0-9\s\-]', ' ', text)

        # Remove extra whitespace again
        text = ' '.join(text.split())

        return text

    def _get_confidence_level(self, score: float) -> str:
        """Get confidence level based on match score."""
        if score >= 90:
            return 'high'
        elif score >= 75:
            return 'medium'
        elif score >= 60:
            return 'low'
        else:
            return 'very_low'

    def _get_match_reasons(self, match_details: Dict) -> List[str]:
        """Generate human-readable reasons for the match."""
        reasons = []

        if match_details.get('exact_brand_match'):
            reasons.append('Exact brand match')
        elif match_details.get('brand_score', 0) > 70:
            reasons.append('Brand similarity')

        if match_details.get('exact_model_match'):
            reasons.append('Exact model match')
        elif match_details.get('model_score', 0) > 70:
            reasons.append('Model similarity')

        if match_details.get('name_score', 0) > 80:
            reasons.append('Product name similarity')

        if match_details.get('keyword_score', 0) > 50:
            reasons.append('Keyword matching')

        if match_details.get('category_bonus', 0) > 0:
            reasons.append('Product category match')

        return reasons if reasons else ['General similarity']

# Global instance
ai_matcher = AIProductMatcher()