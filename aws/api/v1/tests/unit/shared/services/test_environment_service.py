import os
from unittest.mock import MagicMock, patch

import pytest

from aws.api.v1.src.shared.services.environment_service import (
    Environment,
    EnvironmentErrorMessages,
    EnvironmentInfoMessages,
    EnvironmentVariableError,
    MissingEnvironmentVariableError,
)


@pytest.fixture
def env_with_mocked_logger():
    env = Environment([])
    env.logger = MagicMock()
    return env, env.logger


def test_fetch_variable_existing(env_with_mocked_logger):
    env, mock_logger = env_with_mocked_logger
    with patch.dict(os.environ, {"EXISTING_VAR": "test_value"}):
        assert env.fetch_variable("EXISTING_VAR") == "test_value"
        mock_logger.info.assert_called_once_with(
            EnvironmentInfoMessages.ENV_VAR_FETCHED.format(var_name="EXISTING_VAR")
        )


def test_fetch_variable_non_existing(env_with_mocked_logger):
    env, mock_logger = env_with_mocked_logger
    with pytest.raises(EnvironmentVariableError) as excinfo:
        env.fetch_variable("NON_EXISTING_VAR")
    expected_message = EnvironmentErrorMessages.ENV_VAR_NOT_SET.format(var_name="NON_EXISTING_VAR")
    assert str(excinfo.value) == expected_message
    mock_logger.error.assert_called_once_with(expected_message)


def test_fetch_required_variables_all_exist(env_with_mocked_logger):
    env, mock_logger = env_with_mocked_logger
    with patch.dict(os.environ, {"EXISTING_VAR": "test_value"}):
        env.required_vars.append("EXISTING_VAR")
        env.fetch_required_variables()
        mock_logger.error.assert_not_called()
        mock_logger.info.assert_called_with(EnvironmentInfoMessages.ALL_ENV_VARS_FETCHED)


@pytest.mark.parametrize(
    "existing_vars, required_vars, missing_vars",
    [
        (["EXISTING_VAR"], ["EXISTING_VAR", "NON_EXISTING_VAR"], ["NON_EXISTING_VAR"]),
        (
            [],
            ["NON_EXISTING_VAR_1", "NON_EXISTING_VAR_2"],
            ["NON_EXISTING_VAR_1", "NON_EXISTING_VAR_2"],
        ),
        (["IRRELEVANT_VAR"], ["NON_EXISTING_VAR"], ["NON_EXISTING_VAR"]),
    ],
)
def test_fetch_required_variables_missing(
    env_with_mocked_logger, existing_vars, required_vars, missing_vars
):
    env, mock_logger = env_with_mocked_logger
    with patch.dict(os.environ, {var: "test_value" for var in existing_vars}):
        env.required_vars = required_vars
        with pytest.raises(MissingEnvironmentVariableError) as excinfo:
            env.fetch_required_variables()
        expected_message = EnvironmentErrorMessages.MISSING_ENV_VARS.format(
            missing_vars=", ".join(missing_vars)
        )
        assert str(excinfo.value) == expected_message
        assert mock_logger.error.call_count == len(missing_vars) + 1
        assert mock_logger.info.call_count == len(set(existing_vars) & set(required_vars))