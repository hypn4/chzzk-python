"""Input widgets for Chzzk TUI."""

from __future__ import annotations

from typing import Literal

from textual.validation import ValidationResult, Validator
from textual.widgets import Input

ValidateOn = Literal["blur", "changed", "submitted"]


class CookieValidator(Validator):
    """Validator for Naver authentication cookie values."""

    def __init__(self, min_length: int = 10) -> None:
        """Initialize the validator.

        Args:
            min_length: Minimum required cookie length.
        """
        super().__init__()
        self.min_length = min_length

    def validate(self, value: str) -> ValidationResult:
        """Validate the cookie value.

        Args:
            value: The cookie value to validate.

        Returns:
            Validation result indicating success or failure.
        """
        if not value:
            return self.failure("Cookie value is required")
        if len(value) < self.min_length:
            return self.failure(f"Cookie must be at least {self.min_length} characters")
        if " " in value:
            return self.failure("Cookie should not contain spaces")
        return self.success()


class MaskedInput(Input):
    """Input widget with password masking for sensitive data.

    Displays input as asterisks while maintaining the actual value.
    Provides validation feedback for cookie format requirements.
    """

    DEFAULT_CSS = """
    MaskedInput {
        border: tall $primary;
    }
    MaskedInput:focus {
        border: tall $accent;
    }
    MaskedInput.-invalid {
        border: tall $error;
    }
    MaskedInput.-valid {
        border: tall $success;
    }
    """

    def __init__(
        self,
        placeholder: str = "",
        *,
        validate_on: list[ValidateOn] | None = None,
        min_length: int = 10,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the masked input widget.

        Args:
            placeholder: Placeholder text when empty.
            validate_on: Events to trigger validation (e.g., ["blur", "changed"]).
            min_length: Minimum required input length.
            id: Widget ID.
            classes: CSS classes.
        """
        default_validate_on: list[ValidateOn] = ["blur", "changed"]
        super().__init__(
            placeholder=placeholder,
            password=True,
            validators=[CookieValidator(min_length=min_length)],
            validate_on=validate_on or default_validate_on,
            id=id,
            classes=classes,
        )

    @property
    def is_valid(self) -> bool:
        """Check if the current value is valid.

        Returns:
            True if validation passes, False otherwise.
        """
        if not self.validators:
            return True
        for validator in self.validators:
            result = validator.validate(self.value)
            if not result.is_valid:
                return False
        return True
