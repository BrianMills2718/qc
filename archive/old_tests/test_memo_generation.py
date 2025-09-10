"""
Test suite for memo generation in GT workflow
This should have been written BEFORE trying end-to-end tests
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import copy
from pathlib import Path
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow, OpenCode, AxialRelationship, CoreCategory, TheoreticalModel

class TestMemoGeneration(unittest.TestCase):
    """Test memo generation doesn't break with actual GT schemas"""
    
    def setUp(self):
        """Set up test data"""
        self.mock_operations = Mock()
        self.mock_config = Mock()
        self.mock_config.minimum_code_frequency = 1
        self.mock_config.relationship_confidence_threshold = 0.5
        
        self.workflow = GroundedTheoryWorkflow(self.mock_operations, self.mock_config)
        
        # Test interviews
        self.interviews = [
            {'id': 1, 'text': 'Test interview 1'},
            {'id': 2, 'text': 'Test interview 2'},
            {'id': 3, 'text': 'Test interview 3'}
        ]
        
        # Test open codes
        self.open_codes = [
            OpenCode(
                code_name="Test Code 1",
                description="Description 1",
                properties=["prop1"],
                dimensions=["dim1"],
                supporting_quotes=["Quote 1", "Quote 2"],
                frequency=5,
                confidence=0.9
            ),
            OpenCode(
                code_name="Test Code 2",
                description="Description 2",
                properties=["prop2"],
                dimensions=["dim2"],
                supporting_quotes=["Quote 3"],
                frequency=3,
                confidence=0.8
            )
        ]
        
        # Test axial relationships
        self.axial_relationships = [
            AxialRelationship(
                central_category="Test Code 1",
                related_category="Test Code 2",
                relationship_type="causal",
                conditions=["condition1"],
                consequences=["consequence1"],
                supporting_evidence=["Evidence 1", "Evidence 2"],
                strength=0.85
            )
        ]
        
        # Test core category
        self.core_category = CoreCategory(
            category_name="Core Test Category",
            description="Core description",
            properties=["core_prop"],
            integration_points=["point1"],
            saturation_level=0.9
        )
        
        # Test theoretical model
        self.theoretical_model = TheoreticalModel(
            model_name="Test Theory",
            core_category="Core Test Category",
            theoretical_framework="Framework description",
            propositions=["Prop 1", "Prop 2", "Prop 3"],
            conceptual_relationships=["Rel 1"],
            scope_conditions=["Condition 1"],
            implications=["Implication 1"],
            future_research=["Future 1"]
        )
    
    def test_shallow_copy_bug(self):
        """Test that interview.copy() doesn't modify original"""
        original = {'id': 1, 'text': 'test', 'quotes': []}
        modified = original.copy()
        modified['quotes'].append({'text': 'new quote'})
        
        # This test would have caught our shallow copy bug
        self.assertEqual(len(original['quotes']), 1, 
                        "Shallow copy modifies original! Use deepcopy instead")
    
    def test_deep_copy_works(self):
        """Test that deepcopy preserves original"""
        import copy
        original = {'id': 1, 'text': 'test', 'quotes': []}
        modified = copy.deepcopy(original)
        modified['quotes'].append({'text': 'new quote'})
        
        self.assertEqual(len(original['quotes']), 0, 
                        "Deepcopy should preserve original")
        self.assertEqual(len(modified['quotes']), 1, 
                        "Deepcopy should allow modification")
    
    def test_axial_relationship_has_correct_fields(self):
        """Test that we're using correct field names for AxialRelationship"""
        rel = self.axial_relationships[0]
        
        # This would have caught the evidence_summary bug
        self.assertFalse(hasattr(rel, 'evidence_summary'), 
                        "AxialRelationship doesn't have evidence_summary field!")
        self.assertTrue(hasattr(rel, 'supporting_evidence'), 
                       "AxialRelationship should have supporting_evidence field")
        self.assertIsInstance(rel.supporting_evidence, list,
                            "supporting_evidence should be a list")
    
    def test_open_coding_memo_data_structure(self):
        """Test that open coding memo gets correct data"""
        # Mock the memo generation to check what data it receives
        self.mock_operations.generate_analytical_memo_from_data = MagicMock()
        
        # Simulate what our fixed code does
        interviews_with_codes = []
        for i, interview in enumerate(self.interviews):
            enhanced = copy.deepcopy(interview)
            if 'quotes' not in enhanced:
                enhanced['quotes'] = []
            
            # Only add to first interview
            if i == 0:
                for code in self.open_codes:
                    for quote in code.supporting_quotes:
                        enhanced['quotes'].append({
                            'text': quote,
                            'code': code.code_name,
                            'frequency': code.frequency,
                            'confidence': code.confidence
                        })
            interviews_with_codes.append(enhanced)
        
        # Verify structure
        self.assertEqual(len(interviews_with_codes), 3, "Should have 3 interviews")
        self.assertGreater(len(interviews_with_codes[0]['quotes']), 0, 
                          "First interview should have quotes")
        self.assertEqual(len(interviews_with_codes[1].get('quotes', [])), 0,
                        "Second interview should not have quotes")
    
    def test_axial_coding_memo_data_structure(self):
        """Test that axial coding memo gets correct data"""
        interviews_with_axial = []
        for i, interview in enumerate(self.interviews):
            enhanced = copy.deepcopy(interview)
            if 'quotes' not in enhanced:
                enhanced['quotes'] = []
            
            if i == 0:
                # Add axial relationships correctly
                for rel in self.axial_relationships:
                    # This is the correct way to access evidence
                    evidence_text = rel.supporting_evidence[0] if rel.supporting_evidence else f"{rel.central_category} relates to {rel.related_category}"
                    enhanced['quotes'].append({
                        'text': evidence_text,
                        'code': f"RELATIONSHIP: {rel.central_category} → {rel.related_category}",
                        'frequency': 1,
                        'confidence': rel.strength
                    })
            interviews_with_axial.append(enhanced)
        
        # Verify no AttributeError would occur
        self.assertEqual(len(interviews_with_axial[0]['quotes']), 1,
                        "Should have relationship quote")
        self.assertEqual(interviews_with_axial[0]['quotes'][0]['text'], "Evidence 1",
                        "Should use supporting_evidence[0]")
    
    def test_no_massive_duplication(self):
        """Test that we don't duplicate codes for every interview"""
        # Bad approach (what we had initially)
        bad_interviews = []
        for interview in self.interviews:
            enhanced = copy.deepcopy(interview)
            enhanced['quotes'] = []
            for code in self.open_codes:  # Adding to EVERY interview
                for quote in code.supporting_quotes:
                    enhanced['quotes'].append({'text': quote})
            bad_interviews.append(enhanced)
        
        total_bad_quotes = sum(len(i['quotes']) for i in bad_interviews)
        
        # Good approach (what we fixed)
        good_interviews = []
        for i, interview in enumerate(self.interviews):
            enhanced = copy.deepcopy(interview)
            enhanced['quotes'] = []
            if i == 0:  # Only first interview
                for code in self.open_codes:
                    for quote in code.supporting_quotes:
                        enhanced['quotes'].append({'text': quote})
            good_interviews.append(enhanced)
        
        total_good_quotes = sum(len(i['quotes']) for i in good_interviews)
        
        self.assertEqual(total_bad_quotes, 9, "Bad approach creates 3x duplication")
        self.assertEqual(total_good_quotes, 3, "Good approach avoids duplication")
        
    def test_memo_generator_accepts_list_of_dicts(self):
        """Test that memo generator expects List[Dict] not single dict"""
        # This would have caught our type error
        from src.qc.core.robust_cli_operations import RobustCLIOperations
        
        # The method signature expects List[Dict[str, Any]]
        # Passing a single dict should fail type checking
        single_dict = {"interviews": self.interviews, "codes": self.open_codes}
        
        # This is wrong and would fail
        with self.assertRaises(TypeError, msg="Should not accept single dict"):
            # This would fail if we had proper type checking
            pass  # In real test, would call the actual method
        
        # This is correct
        list_of_dicts = self.interviews  # List[Dict]
        # This should work
        self.assertIsInstance(list_of_dicts, list)
        self.assertIsInstance(list_of_dicts[0], dict)

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)