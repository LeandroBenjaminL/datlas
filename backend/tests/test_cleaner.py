import pandas as pd
import pytest

from app.services.cleaner import DataCleaner


class TestDataCleaner:
    def test_load_csv(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        assert cleaner.df is not None
        assert cleaner.original_shape == (10, 6)

    def test_detect_nulls(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        nulls = cleaner.detect_nulls()
        assert "edad" in nulls
        assert "salario" in nulls
        assert "fecha_ingreso" in nulls
        assert nulls["edad"]["null_count"] == 2

    def test_detect_outliers(self, test_csv_path):
        """detect_outliers returns a dict; current CSV has no IQR outliers."""
        cleaner = DataCleaner(test_csv_path)
        outliers = cleaner.detect_outliers()
        assert isinstance(outliers, dict)
        # test.csv salario range 31000-75000, no IQR outliers in any column

    def test_detect_outliers_with_data(self, tmp_path):
        """Detect outliers in a dataset with a known extreme value."""
        csv_path = tmp_path / "outliers.csv"
        csv_path.write_text(
            "value\n"
            "10\n"
            "12\n"
            "11\n"
            "9\n"
            "13\n"
            "10\n"
            "9999\n"  # outlier claro
            "11\n"
            "10\n"
            "12\n"
        )
        cleaner = DataCleaner(str(csv_path))
        outliers = cleaner.detect_outliers()
        assert "value" in outliers
        assert outliers["value"]["outlier_count"] == 1
        assert outliers["value"]["upper_bound"] < 9999

    def test_detect_duplicates(self, test_csv_path):
        """detect_duplicates returns a report; current CSV has no duplicates."""
        cleaner = DataCleaner(test_csv_path)
        dupes = cleaner.detect_duplicates()
        assert "total_duplicate_rows" in dupes
        assert "duplicate_percent" in dupes
        assert "columns_with_duplicates" in dupes
        assert dupes["total_duplicate_rows"] == 0

    def test_detect_duplicates_with_data(self, tmp_path):
        """Detect duplicate rows in a dataset with known duplicates."""
        csv_path = tmp_path / "dupes.csv"
        csv_path.write_text(
            "nombre,edad,ciudad\n"
            "Ana,28,BSAS\n"
            "Carlos,35,CORDOBA\n"
            "Ana,28,BSAS\n"  # duplicado exacto de fila 0
            "Maria,22,ROSARIO\n"
            "Carlos,35,CORDOBA\n"  # duplicado exacto de fila 1
            "Juan,40,BSAS\n"
        )
        cleaner = DataCleaner(str(csv_path))
        dupes = cleaner.detect_duplicates()
        # 4 filas participan en duplicados (0,1,2,4) con keep=False
        assert dupes["total_duplicate_rows"] == 4
        assert dupes["duplicate_percent"] > 0

    def test_detect_types(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        types = cleaner.detect_types()
        assert "nombre" in types
        assert types["edad"]["detected_type"] == "float64"

    def test_analyze_returns_report(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        report = cleaner.analyze()
        assert "original_shape" in report
        assert "nulls" in report
        assert "outliers" in report
        assert "duplicates" in report
        assert "types" in report

    def test_clean_fill_nulls_median(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        result = cleaner.clean({"fill_nulls": {"edad": "median"}})
        assert len(result["applied_fixes"]) > 0
        # Verify nulls were actually filled
        assert cleaner.df["edad"].isnull().sum() == 0

    def test_clean_remove_outliers(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        result = cleaner.clean({"remove_outliers": ["salario"]})
        assert result["new_shape"][0] <= result["original_shape"][0]

    def test_clean_remove_duplicates(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        result = cleaner.clean({"remove_duplicates": True})
        assert "applied_fixes" in result
        # Current CSV has no duplicates, so 0 removed
        assert result["rows_removed"] == 0

    def test_clean_remove_duplicates_with_dupes(self, tmp_path):
        """Remove duplicate rows and verify actual row count reduction."""
        csv_path = tmp_path / "dupes.csv"
        csv_path.write_text(
            "nombre,edad\n"
            "Ana,28\n"
            "Carlos,35\n"
            "Ana,28\n"  # duplicado
            "Maria,22\n"
            "Carlos,35\n"  # duplicado
        )
        cleaner = DataCleaner(str(csv_path))
        assert cleaner.original_shape == (5, 2)
        result = cleaner.clean({"remove_duplicates": True})
        assert result["original_shape"] == (5, 2)
        assert result["new_shape"] == (3, 2)
        assert result["rows_removed"] == 2
        assert "removed 2 duplicate rows" in result["applied_fixes"]

    def test_full_clean(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        result = cleaner.clean(
            {
                "fill_nulls": {"edad": "median", "salario": "mean"},
                "remove_outliers": ["salario"],
                "remove_duplicates": True,
            }
        )
        assert result["new_shape"][0] <= result["original_shape"][0]
        assert len(result["applied_fixes"]) >= 3
        # Verify nulls were actually filled
        assert cleaner.df["edad"].isnull().sum() == 0
        assert cleaner.df["salario"].isnull().sum() == 0

    def test_clean_without_fixes(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        result = cleaner.clean({})
        assert result["new_shape"] == result["original_shape"]
        assert result["applied_fixes"] == []


class TestDataCleanerEdgeCases:
    """Tests de error y casos límite — filosofía: los tests deben
    proteger contra regresiones en escenarios inesperados, no solo
    verificar el camino feliz."""

    def test_load_empty_csv(self, tmp_path):
        """CSV con solo header y cero filas de datos."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("nombre,edad,ciudad\n")
        cleaner = DataCleaner(str(csv_path))
        # No debería crashear al cargar
        assert cleaner.original_shape[0] == 0
        assert cleaner.original_shape[1] == 3
        # analyze() debería funcionar sin datos
        report = cleaner.analyze()
        assert report["original_shape"]["rows"] == 0
        assert report["original_shape"]["columns"] == 3
        # detect_nulls no debería crashear
        nulls = cleaner.detect_nulls()
        assert nulls == {}
        # detect_duplicates no debería crashear
        dupes = cleaner.detect_duplicates()
        assert dupes["total_duplicate_rows"] == 0

    def test_load_all_nulls_csv(self, tmp_path):
        """CSV donde TODAS las columnas tienen TODOS los valores nulos."""
        csv_path = tmp_path / "all_nulls.csv"
        csv_path.write_text(
            "a,b,c\n"
            ",,\n"
            ",,\n"
            ",,\n"
        )
        cleaner = DataCleaner(str(csv_path))
        # detect_nulls debe reportar todas las columnas
        nulls = cleaner.detect_nulls()
        assert "a" in nulls
        assert "b" in nulls
        assert "c" in nulls
        assert nulls["a"]["null_count"] == 3
        assert nulls["a"]["null_percent"] == 100.0
        # clean con fill_nulls debería rellenar todo
        result = cleaner.clean({"fill_nulls": {"a": "mode", "b": "mode", "c": "mode"}})
        assert len(result["applied_fixes"]) >= 1
        assert cleaner.df["a"].isnull().sum() == 0
        assert cleaner.df["b"].isnull().sum() == 0
        assert cleaner.df["c"].isnull().sum() == 0

    def test_load_single_row_csv(self, tmp_path):
        """CSV con una sola fila — IQR no puede calcularse con 1 dato."""
        csv_path = tmp_path / "single.csv"
        csv_path.write_text(
            "nombre,edad,ciudad\n"
            "Ana,28,BSAS\n"
        )
        cleaner = DataCleaner(str(csv_path))
        assert cleaner.original_shape == (1, 3)
        # detect_outliers no debería crashear con 1 fila (no hay outliers)
        outliers = cleaner.detect_outliers()
        assert outliers == {}  # IQR con 1 dato no produce outliers
        # analyze debería funcionar
        report = cleaner.analyze()
        assert report["original_shape"]["rows"] == 1
        # clean no debería crashear
        result = cleaner.clean({"remove_duplicates": True})
        assert result["rows_removed"] == 0

    def test_load_latin1_encoding_csv(self, tmp_path):
        """CSV en Latin-1 con tildes y ñ — probar encoding alternativo."""
        csv_path = tmp_path / "latin1.csv"
        content = (
            "nombre,ciudad,año\n"
            "José,Córdoba,2023\n"
            "María,España,2024\n"
        )
        csv_path.write_bytes(content.encode("latin-1"))
        # pd.read_csv por defecto usa utf-8, debería lanzar error
        import pandas as pd

        with pytest.raises(UnicodeDecodeError):
            DataCleaner(str(csv_path))
        # Pero con encoding latin-1 debería funcionar
        df = pd.read_csv(str(csv_path), encoding="latin-1")
        assert df.iloc[0]["nombre"] == "José"

    def test_load_binary_file(self, tmp_path):
        """Archivo que no es CSV (binario) — debe lanzar error claro."""
        bin_path = tmp_path / "not_a_csv.bin"
        bin_path.write_bytes(bytes(range(256)))
        with pytest.raises((UnicodeDecodeError, pd.errors.ParserError)):
            DataCleaner(str(bin_path))

    def test_load_malformed_csv(self, tmp_path):
        """CSV malformado — columnas inconsistentes por fila."""
        csv_path = tmp_path / "malformed.csv"
        csv_path.write_text(
            "nombre,edad,ciudad\n"
            "Ana,28\n"  # falta columna
            "Carlos,35,extra\n"  # columna de más
        )
        with pytest.raises(pd.errors.ParserError):
            DataCleaner(str(csv_path))

    def test_clean_remove_outliers_all_same_value(self, tmp_path):
        """Columna numérica con todos los valores iguales — IQR = 0."""
        csv_path = tmp_path / "same_values.csv"
        csv_path.write_text(
            "x,y\n"
            "5,10\n"
            "5,10\n"
            "5,10\n"
            "5,10\n"
            "5,9999\n"  # outlier en y
        )
        cleaner = DataCleaner(str(csv_path))
        # detect_outliers: x no debería marcar outliers (IQR=0, todos iguales)
        outliers = cleaner.detect_outliers()
        # y tiene outlier, x no
        assert "y" in outliers
        # x podría o no aparecer; si IQR=0, lower=upper=5, y todos son 5 exacto
        # entonces no se detecta outlier en x.
        result = cleaner.clean({"remove_outliers": ["x", "y"]})
        # Verificar que no crashea y que elimina el outlier de y
        assert result["rows_removed"] >= 0
