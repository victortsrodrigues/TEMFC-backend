import re
from pydantic import BaseModel, field_validator, ValidationError as PydanticValidationError

class ValidateSchema(BaseModel):
    """
    Schema for validating CPF and name inputs.
    """
    cpf: str
    name: str

    @field_validator('cpf')
    def validate_cpf(cls, v: str) -> str:
        """Validate and clean CPF input"""
        cleaned_cpf = re.sub(r'\D', '', v)
        if len(cleaned_cpf) != 11:
            raise ValueError('CPF deve possuir 11 dígitos')
        return cleaned_cpf

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate and clean name input"""
        stripped = v.strip()
        if not stripped:
            raise ValueError('Nome Completo não pode estar em branco')
        return stripped.upper()