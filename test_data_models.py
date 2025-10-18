"""
Test suite for PC28 data models
Phase 2: Data Models Implementation
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from api_client import (
    PC28Data, 
    PredictionResult, 
    TailFrequencyResult, 
    ModelInfo,
    extract_features, 
    validate_pc28_data,
    categorize_models
)

class TestPC28Data:
    """Test PC28Data model validation"""
    
    def test_valid_pc28_data(self):
        """Test valid PC28 data creation"""
        data = PC28Data(
            sum=15,
            tail=5,
            combination="大单",
            period="20251018001",
            numbers=[5, 5, 5]
        )
        assert data.sum == 15
        assert data.tail == 5
        assert data.combination == "大单"
        assert data.period == "20251018001"
        assert data.numbers == [5, 5, 5]
    
    def test_invalid_sum_too_high(self):
        """Test validation error for sum > 27"""
        with pytest.raises(ValidationError):
            PC28Data(sum=28, tail=8, combination="大双")
    
    def test_invalid_sum_negative(self):
        """Test validation error for negative sum"""
        with pytest.raises(ValidationError):
            PC28Data(sum=-1, tail=9, combination="小单")
    
    def test_invalid_tail_too_high(self):
        """Test validation error for tail > 9"""
        with pytest.raises(ValidationError):
            PC28Data(sum=15, tail=10, combination="大单")
    
    def test_invalid_combination(self):
        """Test validation error for invalid combination"""
        with pytest.raises(ValidationError):
            PC28Data(sum=15, tail=5, combination="无效组合")
    
    def test_extreme_combinations(self):
        """Test extreme value combinations"""
        # Test low extreme
        data_low = PC28Data(sum=2, tail=2, combination="极值")
        assert data_low.combination == "极值"
        
        # Test high extreme
        data_high = PC28Data(sum=25, tail=5, combination="极值")
        assert data_high.combination == "极值"
    
    def test_all_valid_combinations(self):
        """Test all valid combination types"""
        combinations = ["大单", "小双", "小单", "大双", "极值"]
        for combo in combinations:
            data = PC28Data(sum=15, tail=5, combination=combo)
            assert data.combination == combo

class TestPredictionResult:
    """Test PredictionResult model"""
    
    def test_valid_prediction_result(self):
        """Test valid prediction result creation"""
        result = PredictionResult(
            sum_range="10-17",
            combination="大单",
            probabilities={"大单": 0.3, "小双": 0.25, "小单": 0.25, "大双": 0.2},
            confidence=0.85
        )
        assert result.sum_range == "10-17"
        assert result.combination == "大单"
        assert result.confidence == 0.85
        assert isinstance(result.timestamp, datetime)
    
    def test_invalid_confidence_too_high(self):
        """Test validation error for confidence > 1.0"""
        with pytest.raises(ValidationError):
            PredictionResult(
                sum_range="10-17",
                combination="大单",
                probabilities={"大单": 0.5},
                confidence=1.5
            )

class TestTailFrequencyResult:
    """Test TailFrequencyResult model"""
    
    def test_valid_tail_frequency_result(self):
        """Test valid tail frequency result creation"""
        result = TailFrequencyResult(
            frequencies={0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1, 
                        5: 0.1, 6: 0.1, 7: 0.15, 8: 0.1, 9: 0.05},
            chi_square_statistic=12.5,
            p_value=0.03,
            is_significant=True,
            window_size=100
        )
        assert result.p_value == 0.03
        assert result.is_significant == True
        assert result.window_size == 100

class TestModelInfo:
    """Test ModelInfo model"""
    
    def test_valid_model_info(self):
        """Test valid model info creation"""
        model = ModelInfo(
            id="gpt-4o",
            name="GPT-4o",
            developer="OpenAI",
            type="text",
            context_length=128000,
            description="Advanced text model",
            features=["chat", "reasoning"],
            url="https://docs.aimlapi.com/models/gpt-4o"
        )
        assert model.id == "gpt-4o"
        assert model.developer == "OpenAI"
        assert model.context_length == 128000

class TestExtractFeatures:
    """Test extract_features function"""
    
    def test_extract_valid_features(self):
        """Test extracting features from valid API data"""
        sample_data = {
            "retdata": [
                {"number": [5, 5, 5], "period": "20251018001"},
                {"number": [1, 1, 1], "period": "20251018002"},
                {"number": [9, 9, 9], "period": "20251018003"},
                {"number": [7, 3, 4], "period": "20251018004"}
            ]
        }
        
        features = extract_features(sample_data)
        assert len(features) == 4
        
        # Test first feature (sum=15, 大单)
        assert features[0].sum == 15
        assert features[0].tail == 5
        assert features[0].combination == "大单"
        assert features[0].period == "20251018001"
        
        # Test second feature (sum=3, 极值)
        assert features[1].sum == 3
        assert features[1].combination == "极值"
        
        # Test third feature (sum=27, 极值)
        assert features[2].sum == 27
        assert features[2].combination == "极值"
        
        # Test fourth feature (sum=14, 大双)
        assert features[3].sum == 14
        assert features[3].combination == "大双"
    
    def test_extract_features_invalid_data(self):
        """Test extracting features with invalid data"""
        sample_data = {
            "retdata": [
                {"number": [5, 5, 5], "period": "20251018001"},  # Valid
                {"number": [1, 1], "period": "20251018002"},     # Invalid: only 2 numbers
                {"invalid": "data"},                              # Invalid: no number field
                {"number": [5, 5, 5], "period": "20251018004"}   # Valid
            ]
        }
        
        features = extract_features(sample_data)
        assert len(features) == 2  # Only 2 valid features extracted
        assert features[0].sum == 15
        assert features[1].sum == 15
    
    def test_extract_features_empty_data(self):
        """Test extracting features from empty data"""
        empty_data = {}
        features = extract_features(empty_data)
        assert len(features) == 0
        
        no_retdata = {"other": "data"}
        features = extract_features(no_retdata)
        assert len(features) == 0

class TestValidatePC28Data:
    """Test validate_pc28_data function"""
    
    def test_valid_data(self):
        """Test validation of valid PC28 data"""
        assert validate_pc28_data(15, [5, 5, 5]) == True
        assert validate_pc28_data(0, [0, 0, 0]) == True
        assert validate_pc28_data(27, [9, 9, 9]) == True
    
    def test_invalid_sum_range(self):
        """Test validation of invalid sum ranges"""
        assert validate_pc28_data(-1, [0, 0, 0]) == False
        assert validate_pc28_data(28, [9, 9, 10]) == False
    
    def test_invalid_numbers_count(self):
        """Test validation of invalid number counts"""
        assert validate_pc28_data(15, [5, 5]) == False
        assert validate_pc28_data(15, [5, 5, 5, 5]) == False
    
    def test_inconsistent_sum(self):
        """Test validation of inconsistent sum"""
        assert validate_pc28_data(15, [5, 5, 4]) == False
        assert validate_pc28_data(10, [5, 5, 5]) == False
    
    def test_invalid_number_range(self):
        """Test validation of numbers outside 0-9 range"""
        assert validate_pc28_data(30, [10, 10, 10]) == False
        assert validate_pc28_data(-3, [-1, -1, -1]) == False

class TestCategorizeModels:
    """Test categorize_models function"""
    
    def test_categorize_valid_models(self):
        """Test categorizing valid model data"""
        sample_data = {
            "data": [
                {
                    "id": "gpt-4o",
                    "type": "text",
                    "info": {
                        "name": "GPT-4o",
                        "developer": "OpenAI",
                        "contextLength": 128000,
                        "description": "Advanced text model"
                    },
                    "features": ["chat", "reasoning"]
                },
                {
                    "id": "dall-e-3",
                    "type": "image",
                    "info": {
                        "name": "DALL-E 3",
                        "developer": "OpenAI",
                        "description": "Image generation model"
                    },
                    "features": ["generation"]
                }
            ]
        }
        
        categories = categorize_models(sample_data)
        assert len(categories["text"]) == 1
        assert len(categories["image"]) == 1
        assert categories["text"][0].id == "gpt-4o"
        assert categories["image"][0].id == "dall-e-3"
    
    def test_categorize_empty_data(self):
        """Test categorizing empty model data"""
        empty_data = {}
        categories = categorize_models(empty_data)
        assert all(len(models) == 0 for models in categories.values())

if __name__ == "__main__":
    pytest.main([__file__, "-v"])