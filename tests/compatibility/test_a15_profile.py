"""Testes de compatibilidade usando a fixture de perfil do Galaxy A15 (Fase 0)."""

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from ryx import capabilities as caps

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "profile_a15.json"
T0 = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)


def load_a15_fixture() -> dict:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class A15FixtureValidationTest(unittest.TestCase):
    def setUp(self):
        self.fixture = load_a15_fixture()

    def test_fixture_marcada_explicitamente_como_simulada(self):
        meta = self.fixture.get("_meta", {})
        self.assertTrue(meta.get("simulated"), "A fixture DEVE conter _meta.simulated=True")
        self.assertIn("SIMULADOS", meta.get("warning", "").upper())
        self.assertEqual(meta.get("measured_phase"), "FASE0")

    def test_fixture_contem_dados_essenciais_da_fase0(self):
        self.assertEqual(self.fixture["device"]["model"], "SM-A156B")
        self.assertEqual(self.fixture["device"]["android_version"], 16)
        self.assertFalse(self.fixture["environment"]["has_python"])
        self.assertTrue(self.fixture["environment"]["has_termux_api"])
        self.assertFalse(self.fixture["files"]["/proc/loadavg"]["accessible"])
        self.assertTrue(self.fixture["files"]["/proc/meminfo"]["accessible"])


class A15CompatibilityTest(unittest.TestCase):
    def setUp(self):
        self.fixture = load_a15_fixture()
        self.commands = self.fixture["commands"]
        self.files = self.fixture["files"]

        # Adaptadores baseados na fixture
        def fake_which(cmd: str) -> str | None:
            entry = self.commands.get(cmd)
            return entry["path"] if entry and isinstance(entry, dict) else None

        def fake_status(argv: list[str]) -> tuple[int, str] | None:
            cmd = argv[0]
            entry = self.commands.get(cmd)
            if not entry or not isinstance(entry, dict):
                return None
            out = entry.get("version_output") or entry.get("stdout") or ""
            return (entry.get("exit_code", 0), out)

        def fake_reader(path: Path) -> str:
            str_path = str(path).replace("\\", "/")
            # Normaliza para casar com as chaves da fixture (ex: /proc/loadavg)
            for k, f_data in self.files.items():
                if str_path.endswith(k) or str_path == k:
                    if not f_data.get("accessible"):
                        err_type = f_data.get("error", "PermissionError")
                        if err_type == "PermissionError":
                            raise PermissionError(13, f_data.get("message", "Permission denied"))
                        raise OSError(f_data.get("message", "Erro ao acessar"))
                    return f_data.get("content", "")
            raise FileNotFoundError(2, f"No such file: {path}")

        self.fake_which = fake_which
        self.fake_status = fake_status
        self.fake_reader = fake_reader

    def test_detector_coleta_capacidades_conforme_fixture_a15(self):
        collected = caps.collect(
            is_termux=self.fixture["environment"]["is_termux"],
            which=self.fake_which,
            status=self.fake_status,
            reader=self.fake_reader,
            now=lambda: T0,
        )
        by_id = {c.id: c for c in collected}

        # Verifica cada expectativa declarada na fixture
        expected = self.fixture["expected_capabilities"]
        for cap_id, exp_state in expected.items():
            self.assertIn(cap_id, by_id, f"Capacidade {cap_id} deveria ter sido coletada")
            self.assertEqual(
                by_id[cap_id].state,
                exp_state,
                f"Capacidade {cap_id} esperava {exp_state}, mas veio {by_id[cap_id].state}",
            )

    def test_detector_falha_se_chamar_de_supported_algo_que_a_fixture_nega(self):
        """Critério estrito da tarefa: falha se o detector chamar de SUPPORTED o que a fixture nega."""
        collected = caps.collect(
            is_termux=self.fixture["environment"]["is_termux"],
            which=self.fake_which,
            status=self.fake_status,
            reader=self.fake_reader,
            now=lambda: T0,
        )
        by_id = {c.id: c for c in collected}

        # 1. /proc/loadavg é expressamente negado na fixture (accessible=false)
        self.assertFalse(self.fixture["files"]["/proc/loadavg"]["accessible"])
        self.assertNotEqual(
            by_id["proc.loadavg"].state,
            caps.SUPPORTED,
            "Detector chamou /proc/loadavg de SUPPORTED mesmo com leitura negada pela fixture!",
        )
        self.assertEqual(by_id["proc.loadavg"].state, caps.UNSUPPORTED)
        self.assertIn("negada", by_id["proc.loadavg"].evidence)

        # 2. Comandos ausentes no A15 nunca devem virar SUPPORTED
        for cmd in ("python", "python3", "openssl"):
            self.assertIsNone(self.fake_which(cmd))
            # Se fosse investigado via probe_command, teria que ser UNSUPPORTED
            cap_cmd = caps.probe_command(cmd, which=self.fake_which, status=self.fake_status, now=lambda: T0)
            self.assertNotEqual(
                cap_cmd.state,
                caps.SUPPORTED,
                f"Comando {cmd} ausente na fixture virou SUPPORTED indevidamente!",
            )
            self.assertEqual(cap_cmd.state, caps.UNSUPPORTED)

    def test_bateria_do_a15_via_termux_api_registra_leitura_correta(self):
        cap = caps.probe_battery(
            is_termux=True,
            which=self.fake_which,
            status=self.fake_status,
            now=lambda: T0,
        )
        self.assertEqual(cap.state, caps.SUPPORTED)
        self.assertIn("100%", cap.evidence)


if __name__ == "__main__":
    unittest.main()
