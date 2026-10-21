import tempfile
import unittest
from pathlib import Path

from ryx.paths import SOURCE_ROOT, find_resource, resolve_paths


class ResolvePathsTest(unittest.TestCase):
    def test_ryx_home_isola_tudo_numa_pasta(self):
        paths = resolve_paths({"HOME": "/h", "RYX_HOME": "/r"})
        self.assertEqual(paths.home, Path("/h"))
        self.assertEqual(paths.config_dir, Path("/r/config"))
        self.assertEqual(paths.data_dir, Path("/r/data"))
        self.assertEqual(paths.state_dir, Path("/r/state"))
        self.assertEqual(paths.backup_dir, Path("/r/backups"))

    def test_sem_ryx_home_usa_xdg_quando_definido(self):
        paths = resolve_paths(
            {"HOME": "/h", "XDG_CONFIG_HOME": "/c", "XDG_DATA_HOME": "/d", "XDG_STATE_HOME": "/s"}
        )
        self.assertEqual(paths.config_dir, Path("/c/ryx"))
        self.assertEqual(paths.data_dir, Path("/d/ryx"))
        self.assertEqual(paths.state_dir, Path("/s/ryx"))
        self.assertEqual(paths.backup_dir, Path("/d/ryx/backups"))

    def test_sem_nada_cai_nos_padroes_do_home(self):
        paths = resolve_paths({"HOME": "/h"})
        self.assertEqual(paths.config_dir, Path("/h/.config/ryx"))
        self.assertEqual(paths.data_dir, Path("/h/.local/share/ryx"))
        self.assertEqual(paths.state_dir, Path("/h/.local/state/ryx"))

    def test_arquivos_derivados(self):
        paths = resolve_paths({"HOME": "/h", "RYX_HOME": "/r"})
        self.assertEqual(paths.user_config, Path("/r/config/config.toml"))
        self.assertEqual(paths.state_file, Path("/r/state/state.json"))
        self.assertEqual(paths.log_file, Path("/r/state/ryx.log"))


class FindResourceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.paths = resolve_paths({"HOME": str(self.root), "RYX_HOME": str(self.root / "ryx")})

    def tearDown(self):
        self._tmp.cleanup()

    def test_achados_na_arvore_do_codigo(self):
        found = find_resource("config/default.toml", self.paths, {})
        self.assertEqual(found, SOURCE_ROOT / "config" / "default.toml")

    def test_ryx_resources_tem_prioridade_sobre_a_pasta_de_dados(self):
        custom = self.root / "res"
        (custom / "config").mkdir(parents=True)
        (custom / "config" / "default.toml").write_text("x")
        (self.paths.data_dir / "config").mkdir(parents=True)
        (self.paths.data_dir / "config" / "default.toml").write_text("y")
        found = find_resource("config/default.toml", self.paths, {"RYX_RESOURCES": str(custom)})
        self.assertEqual(found, custom / "config" / "default.toml")

    def test_pasta_de_dados_vem_antes_da_arvore_do_codigo(self):
        (self.paths.data_dir / "config").mkdir(parents=True)
        (self.paths.data_dir / "config" / "default.toml").write_text("y")
        found = find_resource("config/default.toml", self.paths, {})
        self.assertEqual(found, self.paths.data_dir / "config" / "default.toml")

    def test_recurso_inexistente_devolve_none(self):
        self.assertIsNone(find_resource("nao/existe.toml", self.paths, {}))


if __name__ == "__main__":
    unittest.main()
