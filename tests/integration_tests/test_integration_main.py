import csv
from pathlib import Path
import pytest
from src.main import Application
from src.config.settings import settings

class TestMainApplicationIntegration:
    @pytest.fixture
    def valid_csv_data(self):
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
    def insufficient_csv_data(self):
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


    def _create_csv_file(self, path: Path, data: list, delimiter: str = ";"):
        # print(f"!!!!!!!!!!!!!!!!!!!!!{path}")
        with open(path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["CNES", "IBGE", "ESTABELECIMENTO", "CHS AMB.", "DESCRICAO CBO", "COMP."]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
        return path


    @pytest.fixture
    def prepare_test_environment(self, tmp_path, monkeypatch, valid_csv_data, insufficient_csv_data):
        """Configura ambiente isolado para testes"""
        # Configura paths temporários
        assets_dir = tmp_path / "assets"
        reports_dir = tmp_path / "reports"
        
        # Aplica patches nas configurações
        monkeypatch.setattr(settings, "ASSETS_DIR", str(assets_dir))
        monkeypatch.setattr(settings, "REPORTS_DIR", str(reports_dir))
                
        # Cria estrutura de diretórios
        assets_dir.mkdir()
        reports_dir.mkdir()

        # Cria arquivos de teste
        self._create_csv_file(
            assets_dir / "valid_medical_data.csv",
            valid_csv_data
        )
        self._create_csv_file(
            assets_dir / "insufficient_medical_data.csv",
            insufficient_csv_data
        )

        return {
            "assets_dir": assets_dir,
            "reports_dir": reports_dir
        }

    def test_full_application_workflow(self, prepare_test_environment, caplog):
        """Testa execução completa da aplicação com dados válidos e inválidos"""
                
        print(f"!!!!!!!!!!!!!!!!!!!!!!{settings.ASSETS_DIR}")
        print(f"!!!!!!!!!!!!!!!!!!!!!!{settings.REPORTS_DIR}")
        
        # Executa aplicação
        app = Application()
        print(f"!!!!!!!!!!!!!!!!!!!!!!{settings.ASSETS_DIR}")
        print(f"!!!!!!!!!!!!!!!!!!!!!!{settings.REPORTS_DIR}")
        app.run()
        
        print(f"!!!!!!!!!!!!!!!!!!!!!!{settings.ASSETS_DIR}")
        print(f"!!!!!!!!!!!!!!!!!!!!!!{settings.REPORTS_DIR}")
        
        # Verifica logs
        print(f"@@@@@@@@@@@@@@@@@@@@{caplog.text}")
        # self._assert_log_contents(caplog.text)
        
        # Verifica relatório
        # parametro = prepare_test_environment["reports_dir"]
        # print(f"!!!!!!!!!!!!!!!!!!!!!!{parametro}")
        self._assert_report_contents(prepare_test_environment["reports_dir"])

    def _assert_log_contents(self, log_text: str):
        """Valida mensagens no log"""
        assert "Processing file: valid_medical_data.csv" in log_text
        assert "STATUS: NOT ELIGIBLE" in log_text
        assert "Processing file: insufficient_medical_data.csv" in log_text
        assert "STATUS: NOT ELIGIBLE" in log_text

    def _assert_report_contents(self, reports_dir: Path):
        """Valida conteúdo do relatório gerado"""
        report_path = reports_dir / "overall_results.csv"
        print(f"!!!!!!!!!!!!!!!!!!!!!!{report_path}")
        assert report_path.exists(), "Relatório não foi gerado"

        with report_path.open('r', encoding='utf-8') as f:
            results = list(csv.DictReader(f, delimiter=';'))
            
            assert len(results) == 2, "Número incorreto de registros no relatório"
            
            # Verifica primeiro registro
            valid_data = results[0]
            assert valid_data["File"] == "valid_medical_data"
            assert valid_data["Status"] == "Eligible"
            assert valid_data["Processed Months"] == "2"
            assert valid_data["CHS Total"] == "80"
            assert valid_data["Pending Hours"] == "40"
            
            # Verifica segundo registro
            invalid_data = results[1]
            assert invalid_data["File"] == "insufficient_medical_data"
            assert invalid_data["Status"] == "Not eligible"
            assert invalid_data["Status Reason"] == "Insufficient CHS"
            assert invalid_data["CHS Total"] == "10"