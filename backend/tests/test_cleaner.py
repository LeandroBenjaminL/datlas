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
