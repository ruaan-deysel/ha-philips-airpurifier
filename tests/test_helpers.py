"""Tests for helpers module."""

from custom_components.philips_airpurifier.helpers import extract_model, extract_name


class TestExtractName:
    """Test extract_name function."""

    def test_extract_name_gen1(self) -> None:
        """Test extracting name from Gen1 API (name key)."""
        status = {"name": "Living Room"}
        assert extract_name(status) == "Living Room"

    def test_extract_name_gen2(self) -> None:
        """Test extracting name from Gen2 API (D01-03 key)."""
        status = {"D01-03": "Bedroom"}
        assert extract_name(status) == "Bedroom"

    def test_extract_name_gen3(self) -> None:
        """Test extracting name from Gen3 API (D01S03 key)."""
        status = {"D01S03": "Office"}
        assert extract_name(status) == "Office"

    def test_extract_name_empty(self) -> None:
        """Test extracting name from empty status dict."""
        status = {}
        assert extract_name(status) == ""

    def test_extract_name_priority(self) -> None:
        """Test that extract_name prioritizes Gen1 over Gen2 and Gen3."""
        status = {"name": "Gen1 Name", "D01-03": "Gen2 Name", "D01S03": "Gen3 Name"}
        assert extract_name(status) == "Gen1 Name"

    def test_extract_name_priority_gen2_over_gen3(self) -> None:
        """Test that extract_name prioritizes Gen2 over Gen3 when Gen1 is absent."""
        status = {"D01-03": "Gen2 Name", "D01S03": "Gen3 Name"}
        assert extract_name(status) == "Gen2 Name"

    def test_extract_name_gen2_only(self) -> None:
        """Test extracting name when only Gen2 key is present."""
        status = {"D01S03": "Gen3 Name"}
        assert extract_name(status) == "Gen3 Name"

    def test_extract_name_falsy_value_skipped(self) -> None:
        """Test that falsy values (empty string, None) are skipped."""
        status = {"name": "", "D01-03": "Bedroom"}
        assert extract_name(status) == "Bedroom"

    def test_extract_name_none_value_skipped(self) -> None:
        """Test that None values are skipped."""
        status = {"name": None, "D01-03": "Bedroom"}
        assert extract_name(status) == "Bedroom"

    def test_extract_name_with_special_characters(self) -> None:
        """Test extracting name with special characters."""
        status = {"name": "Living Room (Main)"}
        assert extract_name(status) == "Living Room (Main)"

    def test_extract_name_with_unicode(self) -> None:
        """Test extracting name with unicode characters."""
        status = {"name": "Schlafzimmer"}
        assert extract_name(status) == "Schlafzimmer"

    def test_extract_name_with_spaces(self) -> None:
        """Test extracting name with leading/trailing spaces."""
        status = {"name": "  Living Room  "}
        assert extract_name(status) == "  Living Room  "


class TestExtractModel:
    """Test extract_model function."""

    def test_extract_model_gen1(self) -> None:
        """Test extracting model from Gen1 API (modelid key)."""
        status = {"modelid": "AC3858/51"}
        assert extract_model(status) == "AC3858/51"

    def test_extract_model_gen2(self) -> None:
        """Test extracting model from Gen2 API (D01-05 key)."""
        status = {"D01-05": "AC1715/11"}
        assert extract_model(status) == "AC1715/11"

    def test_extract_model_gen3(self) -> None:
        """Test extracting model from Gen3 API (D01S05 key)."""
        status = {"D01S05": "AC0850/11"}
        assert extract_model(status) == "AC0850/11"

    def test_extract_model_truncate(self) -> None:
        """Test that extract_model truncates to 9 characters."""
        status = {"modelid": "AC3858/51_extra_long"}
        assert extract_model(status) == "AC3858/51"

    def test_extract_model_empty(self) -> None:
        """Test extracting model from empty status dict."""
        status = {}
        assert extract_model(status) == ""

    def test_extract_model_priority(self) -> None:
        """Test that extract_model prioritizes Gen1 over Gen2 and Gen3."""
        status = {
            "modelid": "AC3858/51",
            "D01-05": "AC1715/11",
            "D01S05": "AC0850/11",
        }
        assert extract_model(status) == "AC3858/51"

    def test_extract_model_priority_gen2_over_gen3(self) -> None:
        """Test that extract_model prioritizes Gen2 over Gen3 when Gen1 is absent."""
        status = {"D01-05": "AC1715/11", "D01S05": "AC0850/11"}
        assert extract_model(status) == "AC1715/11"

    def test_extract_model_gen3_only(self) -> None:
        """Test extracting model when only Gen3 key is present."""
        status = {"D01S05": "AC0850/11"}
        assert extract_model(status) == "AC0850/11"

    def test_extract_model_falsy_value_skipped(self) -> None:
        """Test that falsy values (empty string, None) are skipped."""
        status = {"modelid": "", "D01-05": "AC1715/11"}
        assert extract_model(status) == "AC1715/11"

    def test_extract_model_none_value_skipped(self) -> None:
        """Test that None values are skipped."""
        status = {"modelid": None, "D01-05": "AC1715/11"}
        assert extract_model(status) == "AC1715/11"

    def test_extract_model_exactly_9_chars(self) -> None:
        """Test extracting model that is exactly 9 characters."""
        status = {"modelid": "AC3858/51"}
        assert extract_model(status) == "AC3858/51"
        assert len(extract_model(status)) == 9

    def test_extract_model_less_than_9_chars(self) -> None:
        """Test extracting model that is less than 9 characters."""
        status = {"modelid": "AC0850/11"}
        assert extract_model(status) == "AC0850/11"
        assert len(extract_model(status)) == 9

    def test_extract_model_more_than_9_chars(self) -> None:
        """Test extracting model that is more than 9 characters."""
        status = {"modelid": "AC3858/51_extra"}
        assert extract_model(status) == "AC3858/51"
        assert len(extract_model(status)) == 9

    def test_extract_model_gen2_truncate(self) -> None:
        """Test that Gen2 model is also truncated to 9 characters."""
        status = {"D01-05": "AC1715/11_long_suffix"}
        assert extract_model(status) == "AC1715/11"
        assert len(extract_model(status)) == 9

    def test_extract_model_gen3_truncate(self) -> None:
        """Test that Gen3 model is also truncated to 9 characters."""
        status = {"D01S05": "AC0850/11_extended"}
        assert extract_model(status) == "AC0850/11"
        assert len(extract_model(status)) == 9

    def test_extract_model_single_char(self) -> None:
        """Test extracting a single character model."""
        status = {"modelid": "X"}
        assert extract_model(status) == "X"

    def test_extract_model_numeric(self) -> None:
        """Test extracting numeric model."""
        status = {"modelid": "123456789"}
        assert extract_model(status) == "123456789"

    def test_extract_model_with_special_chars(self) -> None:
        """Test extracting model with special characters."""
        status = {"modelid": "AC-3858/51"}
        assert extract_model(status) == "AC-3858/5"
