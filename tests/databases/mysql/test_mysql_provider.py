import pytest

from wandern.databases.mysql import (
    MySQLConnectionParams,
    parse_params_from_dsn,
    validate_parsed_params,
)


def test_parse_params_from_dsn_valid():
    """Test parsing a valid MySQL DSN."""
    dsn = "mysql://user:pass@localhost:3306/testdb"
    params = parse_params_from_dsn(dsn)

    assert params["host"] == "localhost"
    assert params["port"] == 3306
    assert params["user"] == "user"
    assert params["password"] == "pass"
    assert params["database"] == "testdb"


def test_parse_params_from_dsn_minimal():
    """Test parsing minimal DSN with only required fields."""
    dsn = "mysql://localhost:3306"
    params = parse_params_from_dsn(dsn)

    assert params["host"] == "localhost"
    assert params["port"] == 3306
    assert "user" not in params
    assert "password" not in params
    assert "database" not in params


def test_parse_params_from_dsn_with_query_params():
    """Test parsing DSN with query parameters."""
    dsn = "mysql://user:pass@localhost:3306/testdb?autocommit=true&use_pure=false"
    params = parse_params_from_dsn(dsn)

    assert params["host"] == "localhost"
    assert params["port"] == 3306
    assert params["user"] == "user"
    assert params["password"] == "pass"
    assert params["database"] == "testdb"
    assert params["autocommit"] == "true"
    assert params["use_pure"] == "false"


def test_parse_params_from_dsn_invalid_scheme():
    """Test parsing DSN with invalid scheme raises ValueError."""
    dsn = "postgresql://localhost:3306/testdb"

    with pytest.raises(ValueError, match="DSN string must start with mysql://"):
        parse_params_from_dsn(dsn)


def test_parse_params_from_dsn_missing_host_port():
    """Test parsing DSN without host or port raises ValueError."""
    dsn_no_port = "mysql://localhost/testdb"
    dsn_no_host = "mysql://:3306/testdb"

    with pytest.raises(ValueError, match="Host and port are required in DSN"):
        parse_params_from_dsn(dsn_no_port)
    
    with pytest.raises(ValueError, match="Host and port are required in DSN"):
        parse_params_from_dsn(dsn_no_host)

def test_parse_params_from_dsn_empty_query_param():
    """Test parsing DSN with empty query parameter value raises ValueError."""
    dsn = "mysql://localhost:3306/testdb?autocommit="

    with pytest.raises(ValueError, match="Empty value for query parameter"):
        parse_params_from_dsn(dsn)


def test_parse_params_from_dsn_ignores_unknown_query_params():
    """Test that unknown query parameters are ignored."""
    dsn = "mysql://localhost:3306/testdb?unknown_param=value&autocommit=true"
    params = parse_params_from_dsn(dsn)

    assert "unknown_param" not in params
    assert params["autocommit"] == "true"


def test_validate_parsed_params_valid_port():
    """Test validating params with valid port."""
    params: MySQLConnectionParams = {
        "host": "localhost",
        "port": 3306,
    }

    validated = validate_parsed_params(params)
    assert validated["port"] == 3306


def test_validate_parsed_params_port_string_conversion():
    """Test validating params converts port string to int."""
    params: MySQLConnectionParams = {
        "host": "localhost",
        "port": "3306",  # type: ignore
    }

    validated = validate_parsed_params(params)
    assert validated["port"] == 3306
    assert isinstance(validated["port"], int)


def test_validate_parsed_params_invalid_port():
    """Test validating params with invalid port raises ValueError."""
    params: MySQLConnectionParams = {
        "host": "localhost",
        "port": "invalid",  # type: ignore
    }

    with pytest.raises(ValueError, match="Invalid port value"):
        validate_parsed_params(params)


def test_validate_parsed_params_port_out_of_range_low():
    """Test validating params with port below valid range."""
    params: MySQLConnectionParams = {
        "host": "localhost",
        "port": 0,
    }

    with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
        validate_parsed_params(params)


def test_validate_parsed_params_port_out_of_range_high():
    """Test validating params with port above valid range."""
    params: MySQLConnectionParams = {
        "host": "localhost",
        "port": 70000,
    }

    with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
        validate_parsed_params(params)


def test_validate_parsed_params_boolean_conversion():
    """Test validating params converts boolean strings to bool."""
    params: MySQLConnectionParams = {
        "host": "localhost",
        "port": 3306,
        "autocommit": "true",  # type: ignore
        "ssl_disabled": "1",  # type: ignore
        "use_pure": "yes",  # type: ignore
    }

    validated = validate_parsed_params(params)
    assert validated["autocommit"] is True
    assert validated["ssl_disabled"] is True
    assert validated["use_pure"] is True


def test_validate_parsed_params_boolean_false_conversion():
    """Test validating params converts false boolean strings correctly."""
    params: MySQLConnectionParams = {
        "host": "localhost",
        "port": 3306,
        "autocommit": "false",  # type: ignore
        "ssl_disabled": "0",  # type: ignore
        "use_pure": "no",  # type: ignore
    }

    validated = validate_parsed_params(params)
    assert validated["autocommit"] is False
    assert validated["ssl_disabled"] is False
    assert validated["use_pure"] is False


def test_validate_parsed_params_invalid_boolean():
    """Test validating params with invalid boolean value raises ValueError."""
    params: MySQLConnectionParams = {
        "host": "localhost",
        "port": 3306,
        "autocommit": 123,  # type: ignore
    }

    with pytest.raises(ValueError, match="Invalid value for boolean parameter"):
        validate_parsed_params(params)


def test_validate_parsed_params_preserves_other_fields():
    """Test that validation preserves non-validated fields."""
    params: MySQLConnectionParams = {
        "host": "localhost",
        "port": 3306,
        "user": "testuser",
        "password": "testpass",
        "database": "testdb",
    }

    validated = validate_parsed_params(params)
    assert validated["host"] == "localhost"
    assert validated["user"] == "testuser"
    assert validated["password"] == "testpass"
    assert validated["database"] == "testdb"
