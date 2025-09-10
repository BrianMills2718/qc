#!/usr/bin/env python3
"""
Taxonomy Engine - Core taxonomy processing functionality

Provides taxonomy matching, enhancement, and suggestion capabilities
for the taxonomy plugin.
"""

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


class TaxonomyEngine:
    """Core taxonomy processing engine"""
    
    def __init__(self, auto_enhance: bool = False, threshold: float = 0.7):
        self.auto_enhance = auto_enhance
        self.threshold = threshold
        self.taxonomy_data: Optional[Dict[str, Any]] = None
        self._logger = logging.getLogger(f"{__name__}.TaxonomyEngine")
        
        # Cache for performance
        self._keyword_map: Dict[str, List[str]] = {}
        self._category_map: Dict[str, Dict[str, Any]] = {}
    
    def set_taxonomy(self, taxonomy_data: Dict[str, Any]) -> None:
        """Set the taxonomy data and build caches"""
        self.taxonomy_data = taxonomy_data
        self._build_caches()
        self._logger.info(f"Taxonomy set with {len(taxonomy_data.get('categories', []))} categories")
    
    def _build_caches(self) -> None:
        """Build keyword and category caches for efficient lookup"""
        if not self.taxonomy_data:
            return
        
        # Build category map
        for category in self.taxonomy_data.get('categories', []):
            cat_id = category.get('id')
            if cat_id:
                self._category_map[cat_id] = category
        
        # Build keyword map
        keywords = self.taxonomy_data.get('keywords', {})
        for cat_id, keyword_list in keywords.items():
            for keyword in keyword_list:
                keyword_lower = keyword.lower()
                if keyword_lower not in self._keyword_map:
                    self._keyword_map[keyword_lower] = []
                if cat_id not in self._keyword_map[keyword_lower]:
                    self._keyword_map[keyword_lower].append(cat_id)
        
        self._logger.debug(f"Built caches: {len(self._category_map)} categories, {len(self._keyword_map)} keywords")
    
    def enhance_code(self, code: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a single code with taxonomy information"""
        enhanced_code = code.copy()
        
        # Get text to analyze
        code_name = code.get('name', '').lower()
        code_description = code.get('description', '').lower()
        combined_text = f"{code_name} {code_description}"
        
        # Find matching categories
        categories = self._find_matching_categories(combined_text)
        
        if categories:
            enhanced_code['taxonomy_categories'] = categories
            enhanced_code['taxonomy_enhanced'] = True
            
            # Add primary category (most relevant)
            if categories:
                enhanced_code['primary_taxonomy_category'] = categories[0]
        else:
            enhanced_code['taxonomy_enhanced'] = False
        
        return enhanced_code
    
    def suggest_categories(self, code_text: str) -> List[str]:
        """Suggest taxonomy categories for given text"""
        text_lower = code_text.lower()
        categories = self._find_matching_categories(text_lower)
        
        # Return category names instead of IDs for readability
        category_names = []
        for cat_id in categories:
            if cat_id in self._category_map:
                category_names.append(self._category_map[cat_id].get('name', cat_id))
        
        return category_names
    
    def _find_matching_categories(self, text: str) -> List[str]:
        """Find categories that match the given text"""
        if not self.taxonomy_data:
            return []
        
        # Score each category
        category_scores: Dict[str, float] = {}
        
        # Check keyword matches
        words = text.lower().split()
        for word in words:
            # Direct keyword match
            if word in self._keyword_map:
                for cat_id in self._keyword_map[word]:
                    category_scores[cat_id] = category_scores.get(cat_id, 0) + 1.0
            
            # Partial keyword match
            for keyword, cat_ids in self._keyword_map.items():
                if word in keyword or keyword in word:
                    for cat_id in cat_ids:
                        category_scores[cat_id] = category_scores.get(cat_id, 0) + 0.5
        
        # Check category name matches
        for category in self.taxonomy_data.get('categories', []):
            cat_id = category.get('id')
            cat_name = category.get('name', '').lower()
            
            # Check if category name appears in text
            if cat_name in text:
                category_scores[cat_id] = category_scores.get(cat_id, 0) + 2.0
            
            # Check subcategories
            for subcat in category.get('subcategories', []):
                subcat_lower = subcat.replace('_', ' ').lower()
                if subcat_lower in text:
                    category_scores[cat_id] = category_scores.get(cat_id, 0) + 1.5
                
                # Check individual words from subcategory
                for word in subcat_lower.split():
                    if word in text and len(word) > 3:  # Skip short words
                        category_scores[cat_id] = category_scores.get(cat_id, 0) + 0.3
        
        # Sort by score and apply threshold
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Normalize scores
        if sorted_categories:
            max_score = sorted_categories[0][1]
            if max_score > 0:
                results = []
                for cat_id, score in sorted_categories:
                    normalized_score = score / max_score
                    if normalized_score >= self.threshold:
                        results.append(cat_id)
                    else:
                        break  # Stop once below threshold
                return results
        
        return []
    
    def get_category_info(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a category"""
        return self._category_map.get(category_id)
    
    def analyze_code_coverage(self, codes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how well codes cover the taxonomy"""
        if not self.taxonomy_data:
            return {"error": "No taxonomy loaded"}
        
        # Track category usage
        category_usage = {cat['id']: 0 for cat in self.taxonomy_data.get('categories', [])}
        uncategorized_codes = []
        
        # Analyze each code
        for code in codes:
            if code.get('taxonomy_enhanced'):
                categories = code.get('taxonomy_categories', [])
                if categories:
                    for cat_id in categories:
                        if cat_id in category_usage:
                            category_usage[cat_id] += 1
                else:
                    uncategorized_codes.append(code.get('name', 'Unknown'))
            else:
                uncategorized_codes.append(code.get('name', 'Unknown'))
        
        # Calculate coverage metrics
        total_categories = len(category_usage)
        used_categories = sum(1 for count in category_usage.values() if count > 0)
        coverage_percentage = (used_categories / total_categories * 100) if total_categories > 0 else 0
        
        return {
            "total_codes": len(codes),
            "categorized_codes": len(codes) - len(uncategorized_codes),
            "uncategorized_codes": uncategorized_codes,
            "taxonomy_categories": total_categories,
            "used_categories": used_categories,
            "coverage_percentage": coverage_percentage,
            "category_usage": category_usage
        }