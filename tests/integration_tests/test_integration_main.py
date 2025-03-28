import csv
import pytest
from pathlib import Path
from src.main import Application
from src.config.settings import settings

class TestMainApplicationIntegration:
    def _create_csv_file(self, path: Path, data: list, delimiter: str = ";"):
        with open(path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["CNES", "IBGE", "ESTABELECIMENTO", "CHS AMB.", "DESCRICAO CBO", "COMP."]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
        return path


    @pytest.fixture
    def prepare_test_environment(self, valid_csv_data, invalid_csv_data, missing_csv_data):
        # Cria diretórios originais se não existirem
        Path(settings.ASSETS_DIR).mkdir(parents=True, exist_ok=True)
        Path(settings.REPORTS_DIR).mkdir(parents=True, exist_ok=True)

        # Cria arquivos de teste
        valid_path = Path(settings.ASSETS_DIR) / "valid_data.csv"
        invalid_path = Path(settings.ASSETS_DIR) / "invalid_data.csv"
        missing_path = Path(settings.ASSETS_DIR) / "missing_data.csv"
        
        self._create_csv_file(valid_path, valid_csv_data)
        self._create_csv_file(invalid_path, invalid_csv_data)
        self._create_csv_file(missing_path, missing_csv_data)

        yield  # Executa o teste aqui

        # Teardown: Remove arquivos criados
        valid_path.unlink(missing_ok=True)
        invalid_path.unlink(missing_ok=True)
        missing_path.unlink(missing_ok=True)
        report_path = Path(settings.REPORTS_DIR) / "overall_results.csv"
        report_path.unlink(missing_ok=True)
    
    
    def test_full_application_workflow(self, prepare_test_environment, caplog):
        """Testa execução completa da aplicação com dados válidos e inválidos"""
        
        # Executa aplicação
        app = Application()
        app.run()
        
        # Verificações

        assert "Processing file: valid_data.csv" in caplog.text
        assert "STATUS: NOT ELIGIBLE" in caplog.text  # Ajuste conforme lógica real
        assert "Processing file: invalid_data.csv" in caplog.text
        assert "STATUS: NOT ELIGIBLE" in caplog.text
        assert "Processing file: missing_data.csv" in caplog.text
        assert "STATUS: NOT ELIGIBLE" in caplog.text
        
        # Verifica relatório
        report_path = Path(settings.REPORTS_DIR) / "overall_results.csv"
        assert report_path.exists(), "Relatório não foi gerado"
        with report_path.open('r', encoding='utf-8') as f:
            results = list(csv.DictReader(f, delimiter=';'))
            
            assert len(results) == 3, "Número incorreto de registros no relatório"
            
            # Verifica primeiro registro
            valid_data = results[2]
            assert valid_data["File"] == "valid_data"
            assert valid_data["Status"] == "Not eligible"
            assert valid_data["Pending"] == "46.00"
            
            # Verifica segundo registro
            invalid_data = results[0]
            assert invalid_data["File"] == "invalid_data"
            assert invalid_data["Status"] == "Not eligible"
            assert invalid_data["Pending"] == "48.00"
            
            # Verifica terceiro registro
            missing_data = results[1]
            assert missing_data["File"] == "missing_data"
            assert missing_data["Status"] == "Not eligible"
            assert missing_data["Pending"] == "48.00"
            
      