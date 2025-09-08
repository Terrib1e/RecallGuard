"""LLM-powered recall parsing service using Google Gemini."""

import os
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMRecallParser:
    """LLM-powered service to parse recall text and extract structured product information."""

    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("GEMINI_API_KEY not found. LLM parsing will be disabled.")
            self.enabled = False
            return

        try:
            genai.configure(api_key=api_key)

            # Configure generation settings for more reliable JSON output
            generation_config = {
                "temperature": 0.1,  # Low temperature for more consistent output
                "top_p": 0.8,
                "top_k": 20,
                "max_output_tokens": 1024,
            }

            # Safety settings to avoid refusals
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            self.enabled = True
            logger.info("Gemini LLM parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.enabled = False

    def parse_recall_text(self, recall_text: str, source: str = "UNKNOWN") -> Optional[Dict]:
        """Parse recall text using LLM to extract structured product information."""

        if not self.enabled:
            logger.warning("LLM parser not enabled, falling back to basic parsing")
            return self._fallback_parse(recall_text, source)

        # Validate input
        if not recall_text or not recall_text.strip():
            logger.warning("Empty or whitespace-only recall text provided")
            return self._fallback_parse(recall_text, source)

        # Truncate extremely long text to avoid API limits
        if len(recall_text) > 8000:
            logger.warning(f"Recall text too long ({len(recall_text)} chars), truncating to 8000")
            recall_text = recall_text[:8000] + "..."

        try:
            # Create a detailed prompt for the LLM
            prompt = self._create_parsing_prompt(recall_text, source)

            # Generate response from Gemini with retry logic
            max_retries = 3
            retry_delay = 1  # seconds

            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    break
                except Exception as api_error:
                    if "429" in str(api_error) or "quota" in str(api_error).lower():
                        logger.warning(f"API rate limit hit on attempt {attempt + 1}, retrying in {retry_delay}s...")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                    raise api_error

            # Check if response object is valid
            if not response:
                logger.warning("No response object from Gemini API")
                return self._fallback_parse(recall_text, source)

            # Check if response has text attribute and content
            if not hasattr(response, 'text') or not response.text:
                logger.warning(f"Empty or missing text in Gemini response for text: {recall_text[:100]}...")

                # Log detailed response info for debugging
                if hasattr(response, 'candidates') and response.candidates:
                    logger.warning(f"Response has {len(response.candidates)} candidates")
                    for i, candidate in enumerate(response.candidates):
                        if hasattr(candidate, 'finish_reason'):
                            finish_reason = candidate.finish_reason
                            logger.warning(f"Candidate {i} finish_reason: {finish_reason}")
                            # Check for specific finish reasons that indicate problems
                            if finish_reason in ['SAFETY', 'RECITATION', 'MAX_TOKENS']:
                                logger.warning(f"Response blocked due to: {finish_reason}")
                        if hasattr(candidate, 'safety_ratings'):
                            logger.warning(f"Candidate {i} safety_ratings: {candidate.safety_ratings}")
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                logger.warning(f"Candidate {i} has {len(candidate.content.parts)} content parts")
                else:
                    logger.warning("Response has no candidates")

                return self._fallback_parse(recall_text, source)

            response_text = response.text.strip()
            if not response_text:
                logger.warning("Empty response text from Gemini after stripping")
                return self._fallback_parse(recall_text, source)

            # Log response for debugging (first 200 chars)
            logger.debug(f"LLM response preview: {response_text[:200]}...")

            # Parse the JSON response
            try:
                parsed_data = json.loads(response_text)

                # Validate and clean the response
                cleaned_data = self._validate_and_clean_response(parsed_data, recall_text)

                logger.debug(f"LLM parsed: {cleaned_data.get('product_name', 'Unknown')} by {cleaned_data.get('brand', 'Unknown')}")
                return cleaned_data

            except json.JSONDecodeError as e:
                logger.debug(f"Initial JSON parse failed (likely markdown wrapped): {e}")
                logger.debug(f"Full response text: {response_text}")

                # Try to extract JSON from response if it's wrapped in markdown
                json_match = self._extract_json_from_text(response_text)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match)
                        cleaned_data = self._validate_and_clean_response(parsed_data, recall_text)
                        logger.debug("Successfully extracted JSON from markdown-wrapped response")
                        return cleaned_data
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse extracted JSON from markdown")

                logger.warning(f"Could not extract valid JSON from LLM response: {response_text[:200]}...")
                return self._fallback_parse(recall_text, source)

        except Exception as e:
            logger.error(f"Error in LLM parsing: {e}")
            return self._fallback_parse(recall_text, source)

    def _create_parsing_prompt(self, recall_text: str, source: str) -> str:
        """Create a detailed prompt for the LLM to parse recall information."""

        prompt = f"""
You are an expert product recall analyst. Parse the following recall announcement and extract structured information.

RECALL TEXT:
{recall_text}

SOURCE: {source}

Extract the following information and return ONLY a valid JSON object with these exact fields:

{{
    "product_name": "The main product being recalled (be specific, e.g., 'Wireless Bluetooth Headphones' not just 'headphones')",
    "brand": "The manufacturer or brand name (null if not found)",
    "model": "The specific model number or name (null if not found)",
    "recall_date": "The recall date in YYYY-MM-DD format (null if not found)",
    "category": "Product category: 'electronics', 'automotive', 'food', 'children', 'appliance', 'medical', 'consumer_product', or 'other'",
    "hazard": "The main safety hazard or reason for recall (brief description)",
    "affected_units": "Number of units affected (null if not mentioned)",
    "confidence": "Your confidence in the extraction: 'high', 'medium', or 'low'"
}}

IMPORTANT RULES:
1. Return ONLY the JSON object, no other text, no explanations, no markdown code blocks, no backticks
2. Start your response directly with {{ and end with }} - do not wrap in ```json or ``` blocks
3. Use null for missing information, not empty strings
4. Be specific with product names - include key descriptors
5. Extract the actual recall initiation date, not announcement date
6. Choose the most specific category that fits
7. Keep hazard description under 100 characters
8. If text is unclear or corrupted, set confidence to 'low'
9. Do not include any safety warnings or refusals - always return the JSON
10. NO MARKDOWN FORMATTING - just plain JSON starting with {{ and ending with }}

Examples of good product names:
- "Model XYZ Wireless Earbuds" not "earbuds"
- "2023 Honda Civic Sedan" not "car"
- "Baby Formula Powder" not "formula"
"""

        return prompt

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON object from text that might be wrapped in markdown or other content."""
        import re

        # First try to extract from markdown code blocks
        markdown_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # ```json { } ```
            r'```\s*(\{.*?\})\s*```',      # ``` { } ```
            r'`(\{.*?\})`',                # `{ }`
        ]

        for pattern in markdown_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                # Check if this looks like valid JSON with our expected fields
                if '"product_name"' in match and '"confidence"' in match:
                    return match.strip()

        # Fallback to general JSON object patterns
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Match nested braces
            r'\{.*?\}',  # Simple brace matching
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                # Check if this looks like valid JSON with our expected fields
                if '"product_name"' in match and '"confidence"' in match:
                    return match.strip()

        return None

    def _validate_and_clean_response(self, parsed_data: Dict, original_text: str) -> Dict:
        """Validate and clean the LLM response."""

        # Ensure required fields exist
        required_fields = ['product_name', 'brand', 'model', 'recall_date', 'category', 'hazard', 'confidence']
        for field in required_fields:
            if field not in parsed_data:
                parsed_data[field] = None

        # Clean and validate product name
        if not parsed_data.get('product_name') or parsed_data['product_name'] in ['null', 'NULL', '']:
            parsed_data['product_name'] = 'Consumer Product'
        else:
            # Limit length and clean
            parsed_data['product_name'] = str(parsed_data['product_name'])[:200].strip()

        # Clean brand
        if parsed_data.get('brand') and parsed_data['brand'] not in ['null', 'NULL', '']:
            parsed_data['brand'] = str(parsed_data['brand'])[:100].strip()
        else:
            parsed_data['brand'] = None

        # Clean model
        if parsed_data.get('model') and parsed_data['model'] not in ['null', 'NULL', '']:
            parsed_data['model'] = str(parsed_data['model'])[:100].strip()
        else:
            parsed_data['model'] = None

        # Validate and parse date
        if parsed_data.get('recall_date') and parsed_data['recall_date'] not in ['null', 'NULL', '']:
            try:
                # Try to parse the date
                date_str = str(parsed_data['recall_date'])
                if len(date_str) == 10 and date_str.count('-') == 2:  # YYYY-MM-DD format
                    parsed_data['recall_date'] = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    parsed_data['recall_date'] = None
            except:
                parsed_data['recall_date'] = None
        else:
            parsed_data['recall_date'] = None

        # Validate category
        valid_categories = ['electronics', 'automotive', 'food', 'children', 'appliance', 'medical', 'consumer_product', 'other']
        if parsed_data.get('category') not in valid_categories:
            parsed_data['category'] = 'consumer_product'

        # Clean hazard description
        if parsed_data.get('hazard') and parsed_data['hazard'] not in ['null', 'NULL', '']:
            parsed_data['hazard'] = str(parsed_data['hazard'])[:200].strip()
        else:
            parsed_data['hazard'] = 'Safety concern'

        # Validate confidence
        if parsed_data.get('confidence') not in ['high', 'medium', 'low']:
            parsed_data['confidence'] = 'medium'

        # Clean affected units
        if parsed_data.get('affected_units') and parsed_data['affected_units'] not in ['null', 'NULL', '']:
            try:
                # Extract number from string if needed
                units_str = str(parsed_data['affected_units']).replace(',', '').replace(' units', '').replace(' approximately', '')
                parsed_data['affected_units'] = int(float(units_str))
            except:
                parsed_data['affected_units'] = None
        else:
            parsed_data['affected_units'] = None

        return parsed_data

    def _fallback_parse(self, recall_text: str, source: str) -> Dict:
        """Fallback parsing when LLM is not available."""

        # Basic regex-based parsing as fallback
        product_name = self._extract_basic_product_name(recall_text)
        brand = self._extract_basic_brand(recall_text)

        return {
            'product_name': product_name or 'Consumer Product',
            'brand': brand,
            'model': None,
            'recall_date': None,
            'category': 'consumer_product',
            'hazard': 'Product recall - see details',
            'affected_units': None,
            'confidence': 'low'
        }

    def _extract_basic_product_name(self, text: str) -> Optional[str]:
        """Basic product name extraction for fallback."""
        if not text:
            return None

        import re

        # Look for common patterns
        patterns = [
            r'([A-Za-z\s]+)\s+Recalled\s+by',
            r'Recall\s+of\s+([A-Za-z\s]+)',
            r'^([A-Za-z\s]+?)\s+(?:Recalled|Recall)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback to first few words
        words = text.split()[:3]
        return ' '.join(words) if words else None

    def _extract_basic_brand(self, text: str) -> Optional[str]:
        """Basic brand extraction for fallback."""
        if not text:
            return None

        import re

        patterns = [
            r'Recalled\s+by\s+([A-Za-z\s&]+?)(?:\s+NEWS|\s+CPSC|\s+U\.S\.|\s*$)',
            r'manufactured\s+by\s+([A-Za-z\s&]+?)(?:\s|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                brand = match.group(1).strip()
                if len(brand) > 1:
                    return brand

        return None

    def batch_parse_recalls(self, recalls: List[Dict]) -> List[Dict]:
        """Parse multiple recalls in batch for efficiency."""

        parsed_recalls = []

        for recall in recalls:
            try:
                # Get the text to parse
                text_to_parse = ''
                if recall.get('details'):
                    text_to_parse = recall['details']
                elif recall.get('raw_data') and isinstance(recall['raw_data'], dict):
                    if 'description' in recall['raw_data']:
                        text_to_parse = recall['raw_data']['description']
                    elif 'xml_data' in recall['raw_data']:
                        text_to_parse = recall['raw_data']['xml_data']

                if not text_to_parse:
                    logger.warning(f"No text found for recall {recall.get('id', 'unknown')}")
                    continue

                # Parse with LLM
                parsed_data = self.parse_recall_text(text_to_parse, recall.get('source', 'UNKNOWN'))

                if parsed_data:
                    # Update the recall with parsed data
                    updated_recall = recall.copy()
                    updated_recall.update({
                        'product_name': parsed_data['product_name'],
                        'brand': parsed_data['brand'],
                        'model': parsed_data['model'],
                        'category': parsed_data['category'],
                        'llm_confidence': parsed_data['confidence'],
                        'llm_hazard': parsed_data['hazard'],
                        'llm_affected_units': parsed_data['affected_units']
                    })

                    # Update recall date if LLM found a better one
                    if parsed_data['recall_date']:
                        updated_recall['recall_date'] = parsed_data['recall_date']

                    parsed_recalls.append(updated_recall)

            except Exception as e:
                logger.error(f"Error parsing recall {recall.get('id', 'unknown')}: {e}")
                continue

        return parsed_recalls

# Global instance
llm_parser = LLMRecallParser()