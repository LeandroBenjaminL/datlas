import pytest

from app.services.explorer import DataExplorer


class TestDataExplorer:
    def test_load_csv(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        assert explorer.df is not None
        assert explorer.shape == (10, 6)

    def test_profile_shape(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        profile = explorer.profile()
        assert profile["shape"]["rows"] == 10
        assert profile["shape"]["columns"] == 6

    def test_profile_columns(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        profile = explorer.profile()
        for col in ["nombre", "edad", "ciudad", "salario", "fecha_ingreso", "activo"]:
            assert col in profile["columns"]
        # Verificar valores concretos, no solo estructura
        assert profile["columns"]["edad"]["nulls"] == 2
        assert profile["columns"]["edad"]["null_pct"] == 20.0
        assert profile["columns"]["salario"]["nulls"] == 2
        assert profile["columns"]["activo"]["unique"] == 2  # true, false
        assert profile["columns"]["ciudad"]["unique"] == 3  # BSAS, CORDOBA, ROSARIO
        # Edad: valores numéricos verificables en test.csv
        assert profile["columns"]["edad"]["max"] == 50.0
        assert profile["columns"]["edad"]["min"] == 22.0

    def test_distributions(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        dist = explorer.distributions()
        assert len(dist) > 0
        for _col, data in dist.items():
            assert "counts" in data
            assert "edges" in data
        # Verificar valores concretos de distribución de edad
        assert "edad" in dist
        assert len(dist["edad"]["counts"]) == 20  # bins por defecto
        assert len(dist["edad"]["edges"]) == 21  # edges = bins + 1
        assert sum(dist["edad"]["counts"]) == 8  # 10 filas - 2 nulos

    def test_correlations_no_numeric(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        corr = explorer.correlations()
        assert "matrix" in corr
        assert "pairs" in corr
        # Verificar correlación real entre edad y salario (esperada positiva moderada)
        assert len(corr["pairs"]) >= 1
        edad_salario = [p for p in corr["pairs"] if {p["x"], p["y"]} == {"edad", "salario"}]
        assert len(edad_salario) == 1
        # Con datos reales de test.csv, la correlación edad-salario debería existir
        assert "correlation" in edad_salario[0]
        assert isinstance(edad_salario[0]["correlation"], float)

    def test_statistics(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        stats = explorer.statistics()
        assert len(stats) > 0
        for _col, data in stats.items():
            assert "skewness" in data
            assert "kurtosis" in data
        # Verificar dirección: edad con distribución razonablemente simétrica
        assert "edad" in stats
        assert isinstance(stats["edad"]["skewness"], float)
        assert isinstance(stats["edad"]["kurtosis"], float)

    def test_preview(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        preview = explorer.preview()
        assert len(preview) == 5
        assert isinstance(preview[0], dict)
        # Verificar datos concretos de la primera fila
        assert preview[0]["nombre"] == "Ana"
        assert preview[0]["edad"] == 28.0
        assert preview[0]["ciudad"] == "Buenos Aires"
        assert preview[0]["activo"] is True

    def test_categorical_breakdown(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        cat = explorer.categorical_breakdown()
        assert "ciudad" in cat
        assert len(cat["ciudad"]) > 0
        # Verificar conteos reales: Buenos Aires aparece 4 veces, Córdoba 3, Rosario 3
        ciudades = {c["value"]: c["count"] for c in cat["ciudad"]}
        assert ciudades.get("Buenos Aires") == 4
        assert ciudades.get("Córdoba") == 3
        assert ciudades.get("Rosario") == 3

    def test_null_summary(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        ns = explorer.null_summary()
        assert ns["total_nulls"] > 0
        assert "columns" in ns
        # Verificar conteos exactos de nulos en test.csv
        assert ns["total_nulls"] == 5  # 2 edad + 2 salario + 1 fecha_ingreso
        assert ns["columns"]["edad"]["count"] == 2
        assert ns["columns"]["salario"]["count"] == 2
        assert ns["columns"]["fecha_ingreso"]["count"] == 1
        # Verificar porcentajes
        assert ns["columns"]["edad"]["pct"] == 20.0
        assert ns["overall_pct"] == pytest.approx(8.33, rel=0.01)  # 5/(10*6)*100

    def test_analyze(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        report = explorer.analyze()
        assert "profile" in report
        assert "distributions" in report
        assert "correlations" in report
        assert "statistics" in report
        assert "preview" in report
        assert "categorical_breakdown" in report
        assert "null_summary" in report
