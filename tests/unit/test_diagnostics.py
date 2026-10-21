import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from ryx import __version__
from ryx.modules import FAIL, OK, WARN, worst
from ryx.modules import diagnostics
from tests.helpers import FIXTURES, make_ctx, write

MB = 1024 * 1024


def which_all(command):
    return f"/bin/{command}"


def disk(free_mb):
    return lambda _path: SimpleNamespace(free=free_mb * MB)


def by_name(checks):
    return {c.name: c for c in checks}


class RunChecksTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ctx, _ = make_ctx(self.root, termux=True)

    def tearDown(self):
        self._tmp.cleanup()

    def checks(self, **kwargs):
        defaults = {"which": which_all, "disk_usage": disk(5000), "meminfo": FIXTURES / "meminfo.txt"}
        return by_name(diagnostics.run_checks(self.ctx, **{**defaults, **kwargs}))

    def test_ambiente_saudavel_tudo_ok(self):
        checks = self.checks()
        self.assertEqual(worst(list(checks.values())), OK)
        self.assertIn("Termux", checks["ambiente"].detail)

    def test_python_antigo_e_falha(self):
        self.assertEqual(self.checks(version_info=(3, 10))["python"].status, FAIL)
        self.assertEqual(self.checks(version_info=(3, 11))["python"].status, OK)

    def test_disco_nos_tres_niveis(self):
        self.assertEqual(self.checks(disk_usage=disk(50))["disco"].status, FAIL)
        self.assertEqual(self.checks(disk_usage=disk(300))["disco"].status, WARN)
        self.assertEqual(self.checks(disk_usage=disk(2000))["disco"].status, OK)

    def test_disco_que_nao_da_para_medir_vira_aviso(self):
        def boom(_path):
            raise OSError(5, "erro de E/S")

        self.assertEqual(self.checks(disk_usage=boom)["disco"].status, WARN)

    def test_memoria_baixa_e_ausente(self):
        low = write(self.root / "meminfo", "MemAvailable:  102400 kB\n")
        self.assertEqual(self.checks(meminfo=low)["memória"].status, WARN)
        self.assertEqual(self.checks(meminfo=self.root / "nao-existe")["memória"].status, WARN)
        self.assertIn("1205", self.checks()["memória"].detail)

    def test_comando_ausente_e_aviso_com_dica(self):
        check = self.checks(which=lambda c: None if c == "git" else f"/bin/{c}")["comando git"]
        self.assertEqual(check.status, WARN)
        self.assertIn("pkg install", check.fix)

    def test_fora_do_termux_e_aviso(self):
        ctx, _ = make_ctx(self.root / "outro", termux=False)
        checks = by_name(diagnostics.run_checks(ctx, which=which_all, disk_usage=disk(5000)))
        self.assertEqual(checks["ambiente"].status, WARN)

    def test_config_invalida_e_estado_corrompido_sao_falhas(self):
        self.ctx.config_error = "config.toml: chave desconhecida"
        self.assertEqual(self.checks()["config"].status, FAIL)
        write(self.ctx.paths.state_file, "{quebrado")
        self.assertEqual(self.checks()["estado"].status, FAIL)


class MemInfoTest(unittest.TestCase):
    def test_le_o_valor_em_mb(self):
        self.assertEqual(diagnostics.read_mem_available_mb(FIXTURES / "meminfo.txt"), 1205)

    def test_lixo_devolve_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            junk = write(Path(tmp) / "m", "MemAvailable: abc kB\n")
            self.assertIsNone(diagnostics.read_mem_available_mb(junk))


class CommandsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ctx, self.lines = make_ctx(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_doctor_json_e_valido(self):
        code = diagnostics.run(Namespace(handler=diagnostics._doctor, json=True), self.ctx)
        payload = json.loads("\n".join(self.lines))
        self.assertIn(payload["status"], {OK, WARN, FAIL})
        self.assertIn("python", {c["name"] for c in payload["checks"]})
        self.assertEqual(code, 1 if payload["status"] == FAIL else 0)

    def test_doctor_sai_com_1_quando_ha_falha(self):
        self.ctx.config_error = "config.toml: ruim"
        code = diagnostics.run(Namespace(handler=diagnostics._doctor, json=False), self.ctx)
        self.assertEqual(code, 1)
        self.assertTrue(any("[FALHA]" in line for line in self.lines))
        self.assertEqual(self.lines[-1], "resultado: fail")

    def test_info_mostra_versao_e_pastas(self):
        self.assertEqual(diagnostics.run(Namespace(handler=diagnostics._info), self.ctx), 0)
        text = "\n".join(self.lines)
        self.assertIn(f"ryx {__version__}", text)
        self.assertIn("data_dir:", text)

    def test_doctor_nao_cria_nenhum_arquivo(self):
        diagnostics.run(Namespace(handler=diagnostics._doctor, json=False), self.ctx)
        self.assertFalse(self.ctx.paths.state_file.exists())
        self.assertFalse(self.ctx.paths.backup_dir.exists())


class NodeStateAndObservabilityTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ctx, self.lines = make_ctx(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_node_state_saudavel(self):
        from datetime import datetime, timezone
        from ryx.capabilities import Capability, SUPPORTED
        from ryx.modules import Check, OK
        now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
        checks = [Check("python", OK, "3.11"), Check("disco", OK, "1000 MB")]
        caps = [Capability("runtime.python", SUPPORTED, "3.11", now, 3600)]
        state, sev = diagnostics.determine_node_state(checks, caps, heartbeat_at=now, now=now)
        self.assertEqual(state, diagnostics.NODE_HEALTHY)
        self.assertEqual(sev, diagnostics.SEV_INFO)

    def test_heartbeat_velho_vira_unknown_nunca_healthy(self):
        from datetime import datetime, timedelta, timezone
        from ryx.capabilities import Capability, SUPPORTED
        from ryx.modules import Check, OK
        now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
        old_heartbeat = now - timedelta(seconds=300)  # 5 minutos atrás, ttl padrão 120s
        checks = [Check("python", OK, "3.11")]
        caps = [Capability("runtime.python", SUPPORTED, "3.11", now, 3600)]
        state, sev = diagnostics.determine_node_state(checks, caps, heartbeat_at=old_heartbeat, heartbeat_ttl_s=120, now=now)
        self.assertNotEqual(state, diagnostics.NODE_HEALTHY)
        self.assertEqual(state, diagnostics.NODE_UNKNOWN)
        self.assertEqual(sev, diagnostics.SEV_WARNING)

    def test_capacidade_vencida_vira_unknown_nunca_healthy(self):
        from datetime import datetime, timedelta, timezone
        from ryx.capabilities import Capability, SUPPORTED
        from ryx.modules import Check, OK
        now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
        stale_time = now - timedelta(seconds=70)  # bateria com ttl de 60s
        checks = [Check("python", OK, "3.11")]
        caps = [Capability("battery.read", SUPPORTED, "80%", stale_time, 60)]
        state, sev = diagnostics.determine_node_state(checks, caps, heartbeat_at=now, now=now)
        self.assertNotEqual(state, diagnostics.NODE_HEALTHY)
        self.assertEqual(state, diagnostics.NODE_UNKNOWN)
        self.assertEqual(sev, diagnostics.SEV_WARNING)

    def test_node_offline_e_blocked(self):
        from datetime import datetime, timezone
        from ryx.modules import Check, FAIL, OK
        now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
        checks_ok = [Check("python", OK, "3.11")]
        # offline
        state, sev = diagnostics.determine_node_state(checks_ok, offline=True, now=now)
        self.assertEqual(state, diagnostics.NODE_OFFLINE)
        self.assertEqual(sev, diagnostics.SEV_ERROR)

        # blocked (falha crítica de check)
        checks_fail = [Check("config", FAIL, "corrompida")]
        state_blocked, sev_blocked = diagnostics.determine_node_state(checks_fail, offline=False, now=now)
        self.assertEqual(state_blocked, diagnostics.NODE_BLOCKED)
        self.assertEqual(sev_blocked, diagnostics.SEV_CRITICAL)

    def test_doctor_json_inclui_node_state_e_severity(self):
        code = diagnostics.run(Namespace(handler=diagnostics._doctor, json=True), self.ctx)
        payload = json.loads("\n".join(self.lines))
        self.assertIn("node_state", payload)
        self.assertIn("severity", payload)
        self.assertIn(payload["node_state"], diagnostics.NODE_STATES)
        self.assertIn(payload["severity"], diagnostics.SEVERITIES)

    def test_doctor_no_color_sem_ansi(self):
        import os
        old_env = os.environ.get("NO_COLOR")
        try:
            os.environ["NO_COLOR"] = "1"
            diagnostics.run(Namespace(handler=diagnostics._doctor, json=False), self.ctx)
            full_text = "\n".join(self.lines)
            self.assertNotIn("\x1b[", full_text)
        finally:
            if old_env is None:
                os.environ.pop("NO_COLOR", None)
            else:
                os.environ["NO_COLOR"] = old_env

    def test_format_narrow_respeita_40_colunas(self):
        long_line = "Este é um texto longo de diagnóstico de nó que excede largamente quarenta colunas e precisa quebrar suavemente."
        wrapped = diagnostics.format_narrow(long_line, width=40)
        self.assertTrue(len(wrapped) > 1)
        for line in wrapped:
            self.assertLessEqual(len(line), 40)


if __name__ == "__main__":
    unittest.main()

