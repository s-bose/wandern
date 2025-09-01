from typing import TypeVar, cast

import pytest
from pydantic import BaseModel, ValidationError

from wandern.agents.models import AgentResponse


class SampleData(BaseModel):
    """Sample data model for testing AgentResponse"""

    id: int
    name: str
    active: bool = True


class ComplexData(BaseModel):
    """Complex data model for testing AgentResponse with nested structures"""

    user_id: str
    metadata: dict[str, str] | None = None
    scores: list[float] | None = None


def test_agent_response_generic_type_vars():
    """Test AgentResponse uses correct TypeVars"""
    # Verify the TypeVars are correctly defined
    from wandern.agents.models import _DataT, _ErrorT

    assert isinstance(_DataT, TypeVar)
    assert isinstance(_ErrorT, TypeVar)
    assert _DataT.__bound__ == BaseModel


def test_agent_response_with_simple_data():
    """Test AgentResponse with simple data model"""
    data = SampleData(id=1, name="test")
    response = AgentResponse[SampleData, str](
        data=data, message="Operation successful", error=None
    )

    assert response.data == data
    assert response.data.id == 1
    assert response.data.name == "test"
    assert response.data.active is True
    assert response.message == "Operation successful"
    assert response.error is None


def test_agent_response_with_complex_data():
    """Test AgentResponse with complex data model"""
    data = ComplexData(
        user_id="user123",
        metadata={"role": "admin", "department": "engineering"},
        scores=[85.5, 92.0, 78.3],
    )
    response = AgentResponse[ComplexData, dict](
        data=data, message="User data retrieved", error=None
    )

    assert response.data == data
    assert response.data.user_id == "user123"
    assert response.data.metadata is not None
    assert response.data.metadata["role"] == "admin"
    assert response.data.scores == [85.5, 92.0, 78.3]
    assert response.message == "User data retrieved"
    assert response.error is None


def test_agent_response_with_error():
    """Test AgentResponse with error information"""
    data = SampleData(id=2, name="failed")
    error_info = {"code": 500, "details": "Internal server error"}

    response = AgentResponse[SampleData, dict](
        data=data, message="Operation failed", error=error_info
    )

    assert response.data == data
    assert response.message == "Operation failed"
    assert response.error is not None
    assert response.error == error_info
    assert response.error["code"] == 500


def test_agent_response_minimal_fields():
    """Test AgentResponse with only required data field"""
    data = SampleData(id=3, name="minimal")
    response = AgentResponse[SampleData, str](data=data)

    assert response.data == data
    assert response.message is None
    assert response.error is None


def test_agent_response_default_values():
    """Test AgentResponse default values for optional fields"""
    data = SampleData(id=4, name="defaults")
    response = AgentResponse[SampleData, str](data=data, message="Test message")

    assert response.data == data
    assert response.message == "Test message"
    assert response.error is None  # Default value


@pytest.mark.parametrize(
    "error_type,error_value",
    [
        (str, "String error message"),
        (int, 404),
        (dict, {"error_code": "AUTH_FAILED", "message": "Invalid credentials"}),
        (list, ["error1", "error2", "error3"]),
        (type(None), None),
    ],
)
def test_agent_response_different_error_types(error_type, error_value):
    """Test AgentResponse with different error types"""
    data = SampleData(id=5, name="error_test")

    if error_type is type(None):
        response = AgentResponse[SampleData, str](data=data, error=error_value)
    else:
        response = AgentResponse[SampleData, error_type](data=data, error=error_value)

    assert response.data == data
    assert response.error == error_value


def test_agent_response_validation_missing_data():
    """Test AgentResponse validation when data field is missing"""
    with pytest.raises(ValidationError):
        AgentResponse[SampleData, str](message="Missing data field", error="Some error")  # type: ignore


def test_agent_response_validation_invalid_data_type():
    """Test AgentResponse validation with invalid data type"""
    with pytest.raises(ValidationError):
        AgentResponse[SampleData, str](
            data=cast(SampleData, "not a SampleData instance"),
            message="Invalid data type",
        )


def test_agent_response_validation_data_field_validation():
    """Test AgentResponse when data field fails its own validation"""
    with pytest.raises(ValidationError):
        AgentResponse[SampleData, str](
            data=SampleData(id="not_an_int", name="test"),  # type: ignore
            message="Data validation should fail",
        )


def test_agent_response_nested_data_models():
    """Test AgentResponse with nested data models"""

    class NestedModel(BaseModel):
        inner: SampleData
        count: int

    inner_data = SampleData(id=10, name="inner")
    nested_data = NestedModel(inner=inner_data, count=5)

    response = AgentResponse[NestedModel, str](
        data=nested_data, message="Nested data processed"
    )

    assert response.data.inner.id == 10
    assert response.data.inner.name == "inner"
    assert response.data.count == 5
    assert response.message == "Nested data processed"


def test_agent_response_serialization():
    """Test AgentResponse can be serialized to dict"""
    data = SampleData(id=6, name="serialize")
    response = AgentResponse[SampleData, str](
        data=data, message="Serialization test", error="Some error"
    )

    response_dict = response.model_dump()

    assert "data" in response_dict
    assert "message" in response_dict
    assert "error" in response_dict
    assert response_dict["data"]["id"] == 6
    assert response_dict["data"]["name"] == "serialize"
    assert response_dict["message"] == "Serialization test"
    assert response_dict["error"] == "Some error"


def test_agent_response_json_serialization():
    """Test AgentResponse can be serialized to JSON"""
    data = SampleData(id=7, name="json_test")
    response = AgentResponse[SampleData, str](data=data, message="JSON test")

    json_str = response.model_dump_json()

    assert isinstance(json_str, str)
    assert '"id":7' in json_str
    assert '"name":"json_test"' in json_str
    assert '"message":"JSON test"' in json_str


def test_agent_response_equality():
    """Test AgentResponse equality comparison"""
    data1 = SampleData(id=8, name="equal_test")
    data2 = SampleData(id=8, name="equal_test")

    response1 = AgentResponse[SampleData, str](
        data=data1, message="Test message", error=None
    )

    response2 = AgentResponse[SampleData, str](
        data=data2, message="Test message", error=None
    )

    assert response1 == response2


def test_agent_response_inequality():
    """Test AgentResponse inequality comparison"""
    data1 = SampleData(id=9, name="test1")
    data2 = SampleData(id=10, name="test2")

    response1 = AgentResponse[SampleData, str](data=data1, message="Message 1")
    response2 = AgentResponse[SampleData, str](data=data2, message="Message 2")

    assert response1 != response2


def test_agent_response_with_optional_data_fields():
    """Test AgentResponse with data models containing optional fields"""
    data = ComplexData(user_id="user456")  # Only required field
    response = AgentResponse[ComplexData, str](
        data=data, message="Optional fields test"
    )

    assert response.data.user_id == "user456"
    assert response.data.metadata is None
    assert response.data.scores is None
    assert response.message == "Optional fields test"
