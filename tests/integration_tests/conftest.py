import pytest
import csv
from src.core.models.row_process_data import RowProcessData
from pathlib import Path
from io import StringIO

@pytest.fixture
def csv_factory_chs_cbo():
    """Factory para criar arquivos CSV de teste"""
    
    def _create_csv(data=None):
        
        final_data = [
            ["6990193", "350750", "USF COHAB IV BOTUCATU", "40", "MEDICO DA FAMILIA", "202301"],
            ["6990193", "350750", "USF COHAB IV BOTUCATU", "40", "MEDICO DA FAMILIA", "202302"],
        ]
        
        if data:
            final_data.append(data)
        
        print(final_data)
        
        csv_content = "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
        csv_content += "\n".join(";".join(map(str, row)) for row in final_data)
        csv_file = StringIO(csv_content)
            
        return csv_file

    return _create_csv


@pytest.fixture
def csv_factory_chs_cbo_clear():
    """Factory para criar arquivos CSV de teste"""
    def _create_csv(data):
        csv_content = "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
        csv_content += "\n".join(";".join(map(str, row)) for row in data)
        csv_file = StringIO(csv_content)
            
        return csv_file
    return _create_csv


@pytest.fixture
def csv_factory_establishment():
    """Factory para criar arquivos CSV de teste"""
    
    def _create_csv(data=None):
        
        final_data = [
            ["6990193", "350750", "USF COHAB IV BOTUCATU", "40", "MEDICO CLINICO", "202301"],
            ["6644694", "350750", "USF REAL PARK BOTUCATU", "40", "MEDICO GENERALISTA", "202302"],
        ]
        
        if data:
            final_data.append(data)
        
        print(final_data)
        
        csv_content = "CNES;IBGE;ESTABELECIMENTO;CHS AMB.;DESCRICAO CBO;COMP.\n"
        csv_content += "\n".join(";".join(map(str, row)) for row in final_data)
        csv_file = StringIO(csv_content)
        csv_reader = csv.DictReader(csv_file, delimiter=';')
            
        return csv_reader

    return _create_csv


@pytest.fixture
def valid_csv_data():
    return [
        {
            "CNES": "2337545",
            "IBGE": "317130",
            "ESTABELECIMENTO": "UNIDADE BASICA DE SAUDE",
            "CHS AMB.": "40",
            "DESCRICAO CBO": "MEDICO DA FAMILIA",
            "COMP.": "01/2023"
        },
        {
            "CNES": "2337545",
            "IBGE": "317130",
            "ESTABELECIMENTO": "UNIDADE BASICA DE SAUDE",
            "CHS AMB.": "40",
            "DESCRICAO CBO": "MEDICO DA FAMILIA",
            "COMP.": "02/2023"
        }
    ]

@pytest.fixture
def invalid_csv_data():
    return [
        {
            "CNES": "9999999",
            "IBGE": "999999",
            "ESTABELECIMENTO": "SMALL CLINIC",
            "CHS AMB.": "10",
            "DESCRICAO CBO": "MEDICO DA FAMILIA",
            "COMP.": "01/2023"
        }
    ]
    
    
@pytest.fixture
def missing_csv_data():
    return [
        {
            "CNES": "9999999",
            "IBGE": "999999",
            "ESTABELECIMENTO": "SMALL CLINIC",
            "CHS AMB.": "10",
            "DESCRICAO CBO": "MEDICO DA FAMILIA"
        }
    ]