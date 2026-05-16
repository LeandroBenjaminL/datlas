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

    def test_distributions(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        dist = explorer.distributions()
        assert len(dist) > 0
        for _col, data in dist.items():
            assert "counts" in data
            assert "edges" in data

    def test_correlations_no_numeric(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        corr = explorer.correlations()
        assert "matrix" in corr
        assert "pairs" in corr

    def test_statistics(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        stats = explorer.statistics()
        assert len(stats) > 0
        for _col, data in stats.items():
            assert "skewness" in data
            assert "kurtosis" in data

    def test_preview(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        preview = explorer.preview()
        assert len(preview) == 5
        assert isinstance(preview[0], dict)

    def test_categorical_breakdown(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        cat = explorer.categorical_breakdown()
        assert "ciudad" in cat
        assert len(cat["ciudad"]) > 0

    def test_null_summary(self, test_csv_path):
        explorer = DataExplorer(test_csv_path)
        ns = explorer.null_summary()
        assert ns["total_nulls"] > 0
        assert "columns" in ns

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
