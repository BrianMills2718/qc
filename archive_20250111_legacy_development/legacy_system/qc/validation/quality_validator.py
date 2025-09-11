"""
Quality validation system for confidence-based validation and evidence checking.
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

from ..extraction.extraction_schemas import ExtractedEntity, ExtractedRelationship

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation result categories"""
    AUTO_APPROVE = "auto_approve"
    FLAG_FOR_REVIEW = "flag_for_review" 
    REQUIRE_HUMAN_VALIDATION = "require_human_validation"
    AUTO_REJECT = "auto_reject"


@dataclass
class QualityIssue:
    """Individual quality issue found during validation"""
    issue_type: str
    severity: str  # "error", "warning", "info"
    message: str
    suggestion: Optional[str] = None


@dataclass
class QualityReport:
    """Comprehensive quality report for an entity or relationship"""
    validation_result: ValidationResult
    confidence_score: float
    quality_score: float
    issues: List[QualityIssue]
    metadata: Dict[str, Any]


class QualityValidator:
    """Multi-level confidence-based validation system"""
    
    def __init__(self, 
                 auto_approve_threshold: float = 0.9,
                 review_threshold: float = 0.7,
                 validation_threshold: float = 0.5):
        self.auto_approve_threshold = auto_approve_threshold
        self.review_threshold = review_threshold
        self.validation_threshold = validation_threshold
        
    def validate_entity(self, entity: ExtractedEntity, 
                       interview_date: Optional[datetime] = None) -> QualityReport:
        """
        Comprehensive entity validation
        
        Args:
            entity: Entity to validate
            interview_date: Date of interview for temporal validation
            
        Returns:
            QualityReport with validation results
        """
        issues = []
        confidence = entity.confidence
        
        # Basic confidence validation
        if confidence >= self.auto_approve_threshold:
            result = ValidationResult.AUTO_APPROVE
        elif confidence >= self.review_threshold:
            result = ValidationResult.FLAG_FOR_REVIEW
        elif confidence >= self.validation_threshold:
            result = ValidationResult.REQUIRE_HUMAN_VALIDATION
        else:
            result = ValidationResult.AUTO_REJECT
            issues.append(QualityIssue(
                issue_type="low_confidence",
                severity="error",
                message=f"Entity confidence {confidence:.2f} below minimum threshold {self.validation_threshold}",
                suggestion="Provide additional evidence or context"
            ))
        
        # Name quality validation
        name_issues = self._validate_entity_name(entity.name)
        issues.extend(name_issues)
        
        # Evidence validation
        evidence_issues = self._validate_entity_evidence(entity, confidence)
        issues.extend(evidence_issues)
        
        # Temporal consistency (if date provided)
        if interview_date:
            temporal_issues = self._validate_temporal_consistency(entity, interview_date)
            issues.extend(temporal_issues)
        
        # Property validation
        property_issues = self._validate_entity_properties(entity)
        issues.extend(property_issues)
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(entity, issues)
        
        return QualityReport(
            validation_result=result,
            confidence_score=confidence,
            quality_score=quality_score,
            issues=issues,
            metadata={
                "entity_name": entity.name,
                "entity_type": entity.type,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def validate_relationship(self, relationship: ExtractedRelationship,
                            interview_date: Optional[datetime] = None) -> QualityReport:
        """
        Comprehensive relationship validation
        
        Args:
            relationship: Relationship to validate
            interview_date: Date of interview for temporal validation
            
        Returns:
            QualityReport with validation results
        """
        issues = []
        confidence = relationship.confidence
        
        # Basic confidence validation
        if confidence >= self.auto_approve_threshold:
            result = ValidationResult.AUTO_APPROVE
        elif confidence >= self.review_threshold:
            result = ValidationResult.FLAG_FOR_REVIEW
        elif confidence >= self.validation_threshold:
            result = ValidationResult.REQUIRE_HUMAN_VALIDATION
        else:
            result = ValidationResult.AUTO_REJECT
            issues.append(QualityIssue(
                issue_type="low_confidence",
                severity="error",
                message=f"Relationship confidence {confidence:.2f} below minimum threshold {self.validation_threshold}",
                suggestion="Provide additional evidence or context"
            ))
        
        # Evidence validation
        evidence_issues = self._validate_relationship_evidence(relationship)
        issues.extend(evidence_issues)
        
        # Logical consistency validation
        logical_issues = self._validate_relationship_logic(relationship)
        issues.extend(logical_issues)
        
        # Calculate overall quality score
        quality_score = self._calculate_relationship_quality_score(relationship, issues)
        
        return QualityReport(
            validation_result=result,
            confidence_score=confidence,
            quality_score=quality_score,
            issues=issues,
            metadata={
                "source_entity": relationship.source_entity,
                "target_entity": relationship.target_entity,
                "relationship_type": relationship.relationship_type,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _validate_entity_name(self, name: str) -> List[QualityIssue]:
        """Validate entity name quality"""
        issues = []
        
        if not name or not name.strip():
            issues.append(QualityIssue(
                issue_type="empty_name",
                severity="error",
                message="Entity name is empty or whitespace only",
                suggestion="Provide a meaningful entity name"
            ))
            return issues
        
        # Check for problematic patterns
        problematic_patterns = [
            (r'^(i|me|my|myself)$', "Use specific person name instead of pronoun"),
            (r'^(the|a|an)\s+', "Remove article from beginning of name"),
            (r'^\s*unknown\s*$', "Provide specific entity name if possible"),
            (r'^\s*generic\s*$', "Use more specific entity name"),
            (r'\b(thing|stuff|item)\b', "Use more specific terminology")
        ]
        
        name_lower = name.lower().strip()
        for pattern, suggestion in problematic_patterns:
            if re.search(pattern, name_lower):
                issues.append(QualityIssue(
                    issue_type="low_quality_name",
                    severity="warning",
                    message=f"Entity name '{name}' may be too generic or unclear",
                    suggestion=suggestion
                ))
        
        # Check for reasonable length
        if len(name.strip()) < 2:
            issues.append(QualityIssue(
                issue_type="name_too_short",
                severity="warning", 
                message=f"Entity name '{name}' is very short",
                suggestion="Consider using more descriptive name"
            ))
        elif len(name) > 100:
            issues.append(QualityIssue(
                issue_type="name_too_long",
                severity="warning",
                message=f"Entity name is very long ({len(name)} characters)",
                suggestion="Consider shortening or using abbreviation"
            ))
        
        return issues
    
    def _validate_entity_evidence(self, entity: ExtractedEntity, confidence: float) -> List[QualityIssue]:
        """Validate entity has appropriate evidence for its confidence level"""
        issues = []
        
        quote_count = len(entity.quotes) if entity.quotes else 0
        context_length = len(entity.metadata.get('context', '')) if entity.metadata else 0
        
        # High confidence should have supporting quotes
        if confidence > 0.8 and quote_count == 0:
            issues.append(QualityIssue(
                issue_type="missing_evidence",
                severity="warning",
                message="High confidence entity needs supporting quotes",
                suggestion="Add quotes from the text that mention this entity"
            ))
        
        # Very high confidence should have detailed context
        if confidence > 0.9 and context_length < 20:
            issues.append(QualityIssue(
                issue_type="insufficient_context",
                severity="warning",
                message="Very high confidence entity needs more detailed context",
                suggestion="Provide more context about how this entity was identified"
            ))
        
        # Check quote quality
        if entity.quotes:
            for i, quote in enumerate(entity.quotes):
                if not quote or len(quote.strip()) < 10:
                    issues.append(QualityIssue(
                        issue_type="poor_quote_quality",
                        severity="warning",
                        message=f"Quote {i+1} is very short or empty",
                        suggestion="Use more substantial quotes that clearly reference the entity"
                    ))
        
        return issues
    
    def _validate_relationship_evidence(self, relationship: ExtractedRelationship) -> List[QualityIssue]:
        """Validate relationship has supporting evidence with advanced checks"""
        issues = []
        
        # Enhanced contradictory evidence detection
        issues.extend(self._check_contradictory_evidence(relationship))
        
        # Advanced quote quality validation
        issues.extend(self._validate_quote_quality(relationship))
        
        # Evidence strength vs confidence validation
        issues.extend(self._validate_evidence_strength(relationship))
        
        # Context coherence validation
        issues.extend(self._validate_context_coherence(relationship))
        
        return issues
    
    def _check_contradictory_evidence(self, relationship: ExtractedRelationship) -> List[QualityIssue]:
        """Advanced contradictory evidence detection"""
        issues = []
        
        # Define more comprehensive contradictory indicators
        negative_patterns = {
            "explicit_negation": ["never", "don't", "doesn't", "won't", "cannot", "can't", "refuse to"],
            "cessation": ["stopped", "quit", "abandoned", "discontinued", "ended", "finished"],
            "avoidance": ["avoided", "stays away from", "refuses", "rejects", "dismisses"],
            "criticism": ["terrible", "awful", "useless", "waste", "problematic", "broken"],
            "replacement": ["replaced by", "switched to", "moved away from", "migrated from"]
        }
        
        positive_relationships = ["USES", "ADVOCATES_FOR", "SUPPORTS", "LIKES", "ENDORSES", "RECOMMENDS"]
        negative_relationships = ["SKEPTICAL_OF", "REJECTS", "CRITICIZES", "REPLACED_BY"]
        
        if relationship.context:
            context_lower = relationship.context.lower()
            
            # Check for contradictions in positive relationships
            if relationship.relationship_type.upper() in positive_relationships:
                for category, indicators in negative_patterns.items():
                    for indicator in indicators:
                        if indicator in context_lower:
                            # Check if it's in quotes (direct speech) which might be acceptable
                            in_quotes = (f'"{indicator}"' in relationship.context or 
                                       f"'{indicator}'" in relationship.context)
                            
                            severity = "warning" if in_quotes else "error"
                            issues.append(QualityIssue(
                                issue_type="contradictory_evidence",
                                severity=severity,
                                message=f"Context contains negative indicator '{indicator}' but relationship is positive ({relationship.relationship_type})",
                                suggestion=f"Consider using negative relationship like SKEPTICAL_OF or verify the context interpretation"
                            ))
            
            # Check for contradictions in negative relationships
            elif relationship.relationship_type.upper() in negative_relationships:
                positive_indicators = ["love", "great", "excellent", "useful", "helpful", "recommend", "prefer"]
                for indicator in positive_indicators:
                    if indicator in context_lower:
                        issues.append(QualityIssue(
                            issue_type="contradictory_evidence",
                            severity="warning",
                            message=f"Context contains positive indicator '{indicator}' but relationship is negative ({relationship.relationship_type})",
                            suggestion="Verify the relationship type matches the sentiment in context"
                        ))
        
        return issues
    
    def _validate_quote_quality(self, relationship: ExtractedRelationship) -> List[QualityIssue]:
        """Validate the quality and relevance of supporting quotes"""
        issues = []
        
        if not relationship.quotes:
            return issues
        
        for i, quote in enumerate(relationship.quotes):
            # Check quote length and substance
            if len(quote.strip()) < 10:
                issues.append(QualityIssue(
                    issue_type="poor_quote_quality",
                    severity="warning",
                    message=f"Quote {i+1} is very short ({len(quote)} chars)",
                    suggestion="Use more substantial quotes that clearly demonstrate the relationship"
                ))
            
            # Check if quote mentions both entities
            source_mentioned = relationship.source_entity.lower() in quote.lower()
            target_mentioned = relationship.target_entity.lower() in quote.lower()
            
            if not (source_mentioned or target_mentioned):
                issues.append(QualityIssue(
                    issue_type="irrelevant_quote",
                    severity="warning",
                    message=f"Quote {i+1} doesn't mention either entity in the relationship",
                    suggestion="Ensure quotes directly relate to the entities involved"
                ))
            
            # Check for vague language
            vague_terms = ["something", "stuff", "things", "it", "that", "this"]
            vague_count = sum(1 for term in vague_terms if term in quote.lower().split())
            
            if vague_count > 2:
                issues.append(QualityIssue(
                    issue_type="vague_evidence",
                    severity="info",
                    message=f"Quote {i+1} contains vague language",
                    suggestion="Look for more specific quotes with concrete details"
                ))
        
        return issues
    
    def _validate_evidence_strength(self, relationship: ExtractedRelationship) -> List[QualityIssue]:
        """Validate evidence strength matches confidence level"""
        issues = []
        
        confidence = relationship.confidence
        quote_count = len(relationship.quotes) if relationship.quotes else 0
        context_length = len(relationship.context) if relationship.context else 0
        
        # Strength requirements based on confidence
        if confidence > 0.9:  # Very high confidence
            if quote_count == 0:
                issues.append(QualityIssue(
                    issue_type="insufficient_evidence",
                    severity="error",
                    message="Very high confidence (>0.9) requires supporting quotes",
                    suggestion="Add specific quotes that demonstrate this relationship"
                ))
            elif context_length < 30:
                issues.append(QualityIssue(
                    issue_type="insufficient_context",
                    severity="warning",
                    message="Very high confidence requires detailed context",
                    suggestion="Provide more context explaining the relationship"
                ))
        
        elif confidence > 0.8:  # High confidence
            if quote_count == 0 and context_length < 20:
                issues.append(QualityIssue(
                    issue_type="insufficient_evidence",
                    severity="warning",
                    message="High confidence relationship needs either quotes or detailed context",
                    suggestion="Add supporting quotes or expand the context"
                ))
        
        elif confidence < 0.5:  # Low confidence
            if quote_count > 0 or context_length > 50:
                issues.append(QualityIssue(
                    issue_type="evidence_confidence_mismatch",
                    severity="warning",
                    message="Low confidence but substantial evidence provided",
                    suggestion="Consider if confidence should be higher given the evidence"
                ))
        
        return issues
    
    def _validate_context_coherence(self, relationship: ExtractedRelationship) -> List[QualityIssue]:
        """Validate that context makes sense for the relationship type"""
        issues = []
        
        if not relationship.context:
            return issues
        
        context_lower = relationship.context.lower()
        rel_type = relationship.relationship_type.upper()
        
        # Define expected context patterns for different relationship types
        expected_patterns = {
            "USES": ["use", "using", "utilize", "employ", "work with", "rely on"],
            "WORKS_AT": ["work at", "employed by", "job at", "position at", "based at"],
            "MANAGES": ["manage", "supervise", "oversee", "lead", "direct", "boss"],
            "COLLABORATES_WITH": ["collaborate", "work with", "partner", "team up", "cooperate"],
            "ADVOCATES_FOR": ["advocate", "support", "promote", "champion", "endorse"],
            "SKEPTICAL_OF": ["skeptical", "doubt", "question", "concern", "unsure", "hesitant"]
        }
        
        if rel_type in expected_patterns:
            patterns = expected_patterns[rel_type]
            has_expected_pattern = any(pattern in context_lower for pattern in patterns)
            
            if not has_expected_pattern:
                issues.append(QualityIssue(
                    issue_type="unexpected_context",
                    severity="info",
                    message=f"Context doesn't contain typical language for {rel_type} relationship",
                    suggestion=f"Expected terms like: {', '.join(patterns[:3])}"
                ))
        
        return issues
    
    def _validate_relationship_logic(self, relationship: ExtractedRelationship) -> List[QualityIssue]:
        """Validate logical consistency of relationship"""
        issues = []
        
        source = relationship.source_entity
        target = relationship.target_entity
        rel_type = relationship.relationship_type.upper()
        
        # Check for self-relationships that don't make sense
        if source == target:
            if rel_type not in ["PART_OF", "MANAGES", "SUPERVISES"]:
                issues.append(QualityIssue(
                    issue_type="invalid_self_relationship",
                    severity="warning",
                    message=f"Entity '{source}' has relationship '{rel_type}' with itself",
                    suggestion="Check if this self-relationship makes logical sense"
                ))
        
        # Check for duplicate/redundant relationships
        # (This would require access to other relationships, so we'll skip for now)
        
        return issues
    
    def _validate_temporal_consistency(self, entity: ExtractedEntity, 
                                     interview_date: datetime) -> List[QualityIssue]:
        """Enhanced temporal consistency validation"""
        issues = []
        
        # Check entity creation dates
        issues.extend(self._validate_entity_dates(entity, interview_date))
        
        # Check tool/technology versions
        issues.extend(self._validate_technology_versions(entity, interview_date))
        
        # Check organizational temporal consistency
        issues.extend(self._validate_organizational_timeline(entity, interview_date))
        
        # Check contextual temporal clues
        issues.extend(self._validate_contextual_temporal_clues(entity, interview_date))
        
        return issues
    
    def _validate_entity_dates(self, entity: ExtractedEntity, interview_date: datetime) -> List[QualityIssue]:
        """Validate explicit dates in entity metadata"""
        issues = []
        
        date_fields = ['start_date', 'end_date', 'created_date', 'launch_date', 'release_date']
        
        for field in date_fields:
            if field in entity.metadata:
                try:
                    entity_date = datetime.fromisoformat(str(entity.metadata[field]))
                    
                    if entity_date > interview_date:
                        issues.append(QualityIssue(
                            issue_type="temporal_inconsistency",
                            severity="error",
                            message=f"Entity {field} ({entity_date.date()}) is after interview date ({interview_date.date()})",
                            suggestion="Verify the date accuracy or remove future dates"
                        ))
                    
                    # Check for very old dates that might be typos
                    if entity_date.year < 1950:
                        issues.append(QualityIssue(
                            issue_type="suspicious_date",
                            severity="warning",
                            message=f"Entity {field} ({entity_date.date()}) seems unusually old",
                            suggestion="Verify this date is correct"
                        ))
                        
                except (ValueError, TypeError):
                    issues.append(QualityIssue(
                        issue_type="invalid_date_format",
                        severity="warning",
                        message=f"Invalid date format in {field}: '{entity.metadata[field]}'",
                        suggestion="Use ISO format: YYYY-MM-DD"
                    ))
        
        return issues
    
    def _validate_technology_versions(self, entity: ExtractedEntity, interview_date: datetime) -> List[QualityIssue]:
        """Validate technology/tool version availability"""
        issues = []
        
        if entity.type.lower() not in ["tool", "software", "platform", "system", "api"]:
            return issues
        
        # Known technology release dates (expandable)
        tech_releases = {
            "chatgpt": {"4.0": "2023-03-14", "3.5": "2022-11-30"},
            "claude": {"3.0": "2024-03-01", "2.0": "2023-07-01"},
            "github copilot": {"1.0": "2021-10-01"},
            "python": {"3.12": "2023-10-02", "3.11": "2022-10-24", "3.10": "2021-10-04"},
            "react": {"18.0": "2022-03-29", "17.0": "2020-10-20"},
            "typescript": {"5.0": "2023-03-16", "4.0": "2021-08-26"}
        }
        
        entity_name = entity.name.lower()
        version = entity.metadata.get('version', '').lower() if entity.metadata else ''
        
        # Check against known release dates
        for tech_name, versions in tech_releases.items():
            if tech_name in entity_name and version:
                for tech_version, release_date in versions.items():
                    if tech_version in version:
                        try:
                            release_dt = datetime.fromisoformat(release_date)
                            if release_dt > interview_date:
                                issues.append(QualityIssue(
                                    issue_type="version_temporal_inconsistency",
                                    severity="error",
                                    message=f"{entity.name} version {version} was released {release_date}, after interview date",
                                    suggestion="Check if the version mentioned was actually available at interview time"
                                ))
                        except ValueError:
                            continue
        
        # Check for future version indicators
        future_indicators = ['beta', 'alpha', 'preview', 'upcoming', 'next', 'future', 'planned']
        if version and any(indicator in version for indicator in future_indicators):
            issues.append(QualityIssue(
                issue_type="potential_future_version",
                severity="warning",
                message=f"Version '{version}' contains future/beta indicators",
                suggestion="Verify this version was available and stable at interview time"
            ))
        
        return issues
    
    def _validate_organizational_timeline(self, entity: ExtractedEntity, interview_date: datetime) -> List[QualityIssue]:
        """Validate organizational timeline consistency"""
        issues = []
        
        if entity.type.lower() not in ["organization", "company", "department", "center"]:
            return issues
        
        # Check for known organizational events
        if 'founded' in entity.metadata:
            try:
                founded_date = datetime.fromisoformat(str(entity.metadata['founded']))
                if founded_date > interview_date:
                    issues.append(QualityIssue(
                        issue_type="organization_temporal_inconsistency",
                        severity="error",
                        message=f"Organization founded date ({founded_date.date()}) is after interview",
                        suggestion="Verify founding date accuracy"
                    ))
            except (ValueError, TypeError):
                pass
        
        # Check for organizational changes mentioned in quotes
        if entity.quotes:
            for quote in entity.quotes:
                quote_lower = quote.lower()
                # Look for temporal indicators of change
                change_indicators = [
                    "used to be", "formerly", "previously", "before", "after the merger",
                    "recently changed", "now called", "renamed to"
                ]
                
                for indicator in change_indicators:
                    if indicator in quote_lower:
                        issues.append(QualityIssue(
                            issue_type="organizational_change_detected",
                            severity="info",
                            message=f"Quote suggests organizational change: '{indicator}'",
                            suggestion="Consider if this affects the entity's temporal validity"
                        ))
                        break
        
        return issues
    
    def _validate_contextual_temporal_clues(self, entity: ExtractedEntity, interview_date: datetime) -> List[QualityIssue]:
        """Validate temporal clues in entity context and quotes"""
        issues = []
        
        # Collect all text to analyze
        texts_to_check = []
        
        if entity.metadata and 'context' in entity.metadata:
            texts_to_check.append(entity.metadata['context'])
        
        if entity.quotes:
            texts_to_check.extend(entity.quotes)
        
        # Look for temporal indicators
        for text in texts_to_check:
            text_lower = text.lower()
            
            # Future references
            future_refs = ["will be", "going to", "planning to", "next year", "upcoming", "soon"]
            for ref in future_refs:
                if ref in text_lower:
                    issues.append(QualityIssue(
                        issue_type="future_reference_detected",
                        severity="info",
                        message=f"Text contains future reference: '{ref}'",
                        suggestion="Consider if this entity existed at interview time or was planned"
                    ))
            
            # Past references that might indicate obsolescence
            past_refs = ["used to", "previously", "no longer", "discontinued", "deprecated"]
            for ref in past_refs:
                if ref in text_lower:
                    issues.append(QualityIssue(
                        issue_type="past_reference_detected",
                        severity="info",
                        message=f"Text contains past reference: '{ref}'",
                        suggestion="Consider if this entity was still relevant at interview time"
                    ))
            
            # Specific year mentions
            import re
            year_pattern = r'\b(19|20)\d{2}\b'
            years_mentioned = re.findall(year_pattern, text)
            
            for year_match in years_mentioned:
                try:
                    year = int(year_match + "00")  # Convert match to full year
                    if year > interview_date.year:
                        issues.append(QualityIssue(
                            issue_type="future_year_mentioned",
                            severity="warning",
                            message=f"Text mentions future year: {year}",
                            suggestion="Verify the temporal context of this reference"
                        ))
                except ValueError:
                    continue
        
        return issues
    
    def _validate_entity_properties(self, entity: ExtractedEntity) -> List[QualityIssue]:
        """Validate entity properties for consistency and completeness"""
        issues = []
        
        if not entity.properties:
            return issues
        
        # Check for empty or None values
        for prop_name, prop_value in entity.properties.items():
            if prop_value is None or prop_value == "":
                issues.append(QualityIssue(
                    issue_type="empty_property",
                    severity="info",
                    message=f"Property '{prop_name}' is empty",
                    suggestion="Consider removing empty properties or providing values"
                ))
        
        return issues
    
    def _calculate_quality_score(self, entity: ExtractedEntity, 
                               issues: List[QualityIssue]) -> float:
        """Calculate overall quality score for entity"""
        base_score = entity.confidence
        
        # Penalty for issues
        error_penalty = sum(0.2 for issue in issues if issue.severity == "error")
        warning_penalty = sum(0.1 for issue in issues if issue.severity == "warning")
        
        # Bonus for good evidence
        evidence_bonus = 0.0
        if entity.quotes and len(entity.quotes) > 0:
            evidence_bonus += 0.1
        if entity.metadata and len(entity.metadata.get('context', '')) > 50:
            evidence_bonus += 0.05
        
        final_score = max(0.0, min(1.0, base_score - error_penalty - warning_penalty + evidence_bonus))
        return final_score
    
    def _calculate_relationship_quality_score(self, relationship: ExtractedRelationship,
                                            issues: List[QualityIssue]) -> float:
        """Calculate overall quality score for relationship"""
        base_score = relationship.confidence
        
        # Penalty for issues
        error_penalty = sum(0.2 for issue in issues if issue.severity == "error")
        warning_penalty = sum(0.1 for issue in issues if issue.severity == "warning")
        
        # Bonus for good evidence
        evidence_bonus = 0.0
        if relationship.quotes and len(relationship.quotes) > 0:
            evidence_bonus += 0.1
        if relationship.context and len(relationship.context) > 50:
            evidence_bonus += 0.05
        
        final_score = max(0.0, min(1.0, base_score - error_penalty - warning_penalty + evidence_bonus))
        return final_score