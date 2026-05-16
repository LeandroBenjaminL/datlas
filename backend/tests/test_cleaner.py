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
        cleaner = DataCleaner(test_csv_path)
        outliers = cleaner.detect_outliers()
        for col, info in outliers.items():
            assert info["outlier_count"] > 0
            assert "lower_bound" in info
            assert "upper_bound" in info

    def test_detect_duplicates(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        dupes = cleaner.detect_duplicates()
        assert "total_duplicate_rows" in dupes
        assert "duplicate_percent" in dupes

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
        assert result["rows_removed"] >= 0
        assert len(result["applied_fixes"]) > 0

    def test_clean_remove_outliers(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        result = cleaner.clean({"remove_outliers": ["salario"]})
        assert result["new_shape"][0] <= result["original_shape"][0]

    def test_clean_remove_duplicates(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        result = cleaner.clean({"remove_duplicates": True})
        assert "applied_fixes" in result

    def test_full_clean(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        result = cleaner.clean({
            "fill_nulls": {"edad": "median", "salario": "mean"},
            "remove_outliers": ["salario"],
            "remove_duplicates": True,
        })
        assert result["new_shape"][0] <= result["original_shape"][0]
        assert len(result["applied_fixes"]) >= 3

    def test_clean_without_fixes(self, test_csv_path):
        cleaner = DataCleaner(test_csv_path)
        result = cleaner.clean({})
        assert result["new_shape"] == result["original_shape"]
        assert result["applied_fixes"] == []
