import re
from errors.validation_error import ValidationError
from pydantic import BaseModel, field_validator, ValidationError as PydanticValidationError

class ValidateSchema(BaseModel):
    cpf: str
    name: str

    @field_validator('cpf')
    def validate_cpf(cls, v: str) -> str:
        """Validate and clean CPF input"""
        cleaned_cpf = re.sub(r'\D', '', v)
        if len(cleaned_cpf) != 11:
            raise ValueError('CPF must have exactly 11 digits')
        if len(set(cleaned_cpf)) == 1:
            raise ValueError('Invalid CPF (all digits are identical)')
        return cleaned_cpf

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate and clean name input"""
        stripped = v.strip()
        if not stripped:
            raise ValueError('Name cannot be empty')
        return stripped.upper()