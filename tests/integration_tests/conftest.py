import pytest
import csv
from src.core.models.row_process_data import RowProcessData
from pathlib import Path

@pytest.fixture
def csv_factory_chs_cbo(tmp_path):
    """Factory para criar arquivos CSV de teste"""
    
    def _create_csv(data=None, filename="test_data.csv"):
        
        final_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICO DA FAMILIA",
                "COMP.": "01/2023"
            },
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICO DA FAMILIA",
                "COMP.": "02/2023"
            },
        ] + (data if data else [])        

        csv_path = tmp_path / filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["CNES", "IBGE", "ESTABELECIMENTO", "CHS AMB.", "DESCRICAO CBO", "COMP."]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(final_data)
            
        return csv_path

    return _create_csv


@pytest.fixture
def csv_factory_establishment(tmp_path):
    """Factory para criar arquivos CSV de teste"""
    
    def _create_csv(data=None, filename="test_data.csv"):
        
        final_data = [
            {
                "CNES": "6990193",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF COHAB IV BOTUCATU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICO CLINICO",
                "COMP.": "01/2023"
            },
            {
                "CNES": "6644694",
                "IBGE": "350750",
                "ESTABELECIMENTO": "USF REAL PARK BOTUCATU",
                "CHS AMB.": "40",
                "DESCRICAO CBO": "MEDICO GENERALISTA",
                "COMP.": "02/2023"
            },
        ] + (data if data else [])        

        csv_path = tmp_path / filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["CNES", "IBGE", "ESTABELECIMENTO", "CHS AMB.", "DESCRICAO CBO", "COMP."]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(final_data)
            
        return csv_path

    return _create_csv