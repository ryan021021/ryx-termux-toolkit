"""Capacidades com estado, evidência e frescor (ADR-0003). Fixture A15 medida na Fase 0."""

import json
import tempfile
import unittest
from argparse import Namespace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from ryx import capabilities as caps
from ryx.modules import diagnostics
from tests.helpers import make_ctx

T0 = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


def clock():
    return T0


def negado(_path):
    raise PermissionError(13, "Permission denied")


def status_de(tabela):
    """Runner falso: comando -> (código, saída) ou None (não rodou)."""
    return lambda command: tabela.get(command[0])


class EstadosTest(unittest.TestCase):
    def test_os_cinco_estados_da_adr(self):
        self.assertEqual(
            caps.STATES,
            ("SUPPORTED", "UNSUPPORTED", "UNKNOWN", "TEMPORARILY_UNAVAILABLE", "NEEDS_CONFIGURATION"),
        )

    def test_estado_invalido_e_recusado(self):
        with self.assertRaises(ValueError):
            caps.Capability("x", "OK", "e", T0, 60)

    def test_hora_sem_fuso_e_recusada(self):
        with self.assertRaises(ValueError):
            caps.Capability("x", caps.SUPPORTED, "e", datetime(2026, 10, 21, 12, 0), 60)


class FrescorTest(unittest.TestCase):
    def test_medida_dentro_do_ttl_nao_esta_velha(self):
        cap = caps.Capability("x", caps.SUPPORTED, "e", T0, 60)
        self.assertFalse(cap.is_stale(T0 + timedelta(seconds=60)))

    def test_medida_depois_do_ttl_esta_velha(self):
        cap = caps.Capability("x", caps.SUPPORTED, "e", T0, 60)
        self.assertTrue(cap.is_stale(T0 + timedelta(seconds=61)))

    def test_as_dict_tem_hora_utc_e_marca_de_velho(self):
        cap = caps.Capability("x", caps.SUPPORTED, "e", T0, 60)
        data = cap.as_dict(T0 + timedelta(seconds=120))
        self.assertEqual(data["measured_at"], "2026-10-21T12:00:00Z")
        self.assertEqual(data["ttl_s"], 60)
        self.assertTrue(data["stale"])


class LeituraTest(unittest.TestCase):
    def test_leitura_negada_e_unsupported_nunca_zero(self):
        cap = caps.probe_readable("proc.loadavg", Path("/proc/loadavg"), reader=negado, now=clock)
        self.assertEqual(cap.state, caps.UNSUPPORTED)
        self.assertIn("negada", cap.evidence)

    def test_arquivo_ausente_e_unsupported(self):
        def ausente(_path):
            raise FileNotFoundError(2, "No such file")

        cap = caps.probe_readable("proc.loadavg", Path("/proc/loadavg"), reader=ausente, now=clock)
        self.assertEqual(cap.state, caps.UNSUPPORTED)
        self.assertIn("não existe", cap.evidence)

    def test_conteudo_que_nao_e_texto_e_unknown_sem_derrubar(self):
        def binario(_path):
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

        cap = caps.probe_readable("proc.loadavg", Path("/proc/loadavg"), reader=binario, now=clock)
        self.assertEqual(cap.state, caps.UNKNOWN)

    def test_leitura_ok_e_supported(self):
        cap = caps.probe_readable("proc.loadavg", Path("/x"), reader=lambda _p: "0.1 0.2", now=clock)
        self.assertEqual(cap.state, caps.SUPPORTED)


class ComandoTest(unittest.TestCase):
    def probe(self, which, tabela):
        return caps.probe_command("git", which=which, status=status_de(tabela), now=clock)

    def test_ausente_no_path_e_unsupported(self):
        cap = self.probe(lambda _c: None, {})
        self.assertEqual(cap.state, caps.UNSUPPORTED)
        self.assertEqual(cap.id, "command.git")

    def test_presente_mas_sem_uso_que_funcione_e_unknown(self):
        cap = self.probe(lambda c: f"/bin/{c}", {"git": (1, "")})
        self.assertEqual(cap.state, caps.UNKNOWN)

    def test_presente_que_nao_chegou_a_rodar_e_temporariamente_indisponivel(self):
        cap = self.probe(lambda c: f"/bin/{c}", {})
        self.assertEqual(cap.state, caps.TEMPORARILY_UNAVAILABLE)

    def test_presente_e_respondendo_e_supported(self):
        cap = self.probe(lambda c: f"/bin/{c}", {"git": (0, "git version 2.53")})
        self.assertEqual(cap.state, caps.SUPPORTED)
        self.assertIn("2.53", cap.evidence)


class PythonTest(unittest.TestCase):
    """Python vem do próprio interpretador: no Windows, `python3 --version` pode baixar e instalar Python."""

    def test_versao_suportada_e_supported(self):
        cap = caps.probe_python(version_info=(3, 14, 8), now=clock)
        self.assertEqual((cap.id, cap.state), ("runtime.python", caps.SUPPORTED))
        self.assertIn("3.14.8", cap.evidence)

    def test_versao_antiga_pede_configuracao(self):
        cap = caps.probe_python(version_info=(3, 10, 0), now=clock)
        self.assertEqual(cap.state, caps.NEEDS_CONFIGURATION)

    def test_collect_nunca_roda_python_como_comando(self):
        rodados = []

        def status(command):
            rodados.append(command[0])
            return (0, "x")

        caps.collect(is_termux=True, which=lambda c: f"/bin/{c}", status=status, reader=negado, now=clock)
        self.assertFalse([c for c in rodados if c.startswith("python")])


class BateriaTest(unittest.TestCase):
    def probe(self, termux, which, tabela):
        return caps.probe_battery(termux, which=which, status=status_de(tabela), now=clock)

    def test_fora_do_termux_e_unsupported(self):
        self.assertEqual(self.probe(False, lambda _c: None, {}).state, caps.UNSUPPORTED)

    def test_termux_sem_termux_api_pede_configuracao(self):
        self.assertEqual(self.probe(True, lambda _c: None, {}).state, caps.NEEDS_CONFIGURATION)

    def test_json_valido_e_supported_com_nivel_na_evidencia(self):
        saida = json.dumps({"percentage": 100, "temperature": 29.0, "plugged": "PLUGGED_USB"})
        cap = self.probe(True, lambda c: f"/bin/{c}", {"termux-battery-status": (0, saida)})
        self.assertEqual(cap.state, caps.SUPPORTED)
        self.assertIn("100%", cap.evidence)

    def test_json_sem_nivel_nao_e_supported(self):
        cap = self.probe(True, lambda c: f"/bin/{c}", {"termux-battery-status": (0, "{}")})
        self.assertEqual(cap.state, caps.UNKNOWN)

    def test_saida_que_nao_e_json_e_unknown(self):
        cap = self.probe(True, lambda c: f"/bin/{c}", {"termux-battery-status": (0, "app não instalado")})
        self.assertEqual(cap.state, caps.UNKNOWN)


class PerfilA15Test(unittest.TestCase):
    """Simulação do A15 medido na Fase 0 (não é prova no aparelho): sem /proc/loadavg, com termux-api."""

    def test_detector_nao_chama_de_supported_o_que_o_aparelho_nega(self):
        found = {"git": "/x/git", "termux-battery-status": "/x/tb"}
        lista = caps.collect(
            is_termux=True,
            which=found.get,
            status=status_de({"git": (0, "git version 2.51"), "termux-battery-status": (0, '{"percentage": 75}')}),
            reader=negado,
            now=clock,
        )
        por_id = {c.id: c for c in lista}
        self.assertEqual(por_id["proc.loadavg"].state, caps.UNSUPPORTED)
        self.assertNotIn("command.python3", por_id)
        self.assertEqual(por_id["runtime.python"].state, caps.SUPPORTED)
        self.assertEqual(por_id["command.git"].state, caps.SUPPORTED)
        self.assertEqual(por_id["battery.read"].state, caps.SUPPORTED)


FIXA = [caps.Capability("proc.loadavg", caps.UNSUPPORTED, "leitura negada em /proc/loadavg", T0, 60)]


class DoctorTest(unittest.TestCase):
    """O doctor não roda sonda de verdade aqui: collect é trocado por uma lista fixa."""

    def doctor(self, as_json):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, lines = make_ctx(Path(tmp), termux=False)
            with mock.patch.object(caps, "collect", return_value=FIXA) as collect:
                code = diagnostics.run(Namespace(handler=diagnostics._doctor, json=as_json), ctx)
        return code, lines, collect

    def test_json_mantem_status_e_checks_e_acrescenta_capacidades(self):
        code, lines, collect = self.doctor(True)
        payload = json.loads("\n".join(lines))
        self.assertEqual(set(payload), {"status", "checks", "capabilities"})
        self.assertEqual(code, 1 if payload["status"] == "fail" else 0)
        collect.assert_called_once_with(False)
        [cap] = payload["capabilities"]
        self.assertEqual(set(cap), {"id", "state", "evidence", "measured_at", "ttl_s", "stale"})
        self.assertEqual((cap["id"], cap["state"]), ("proc.loadavg", caps.UNSUPPORTED))
        self.assertTrue(cap["stale"])  # medida de T0 com ttl 60 s, lida agora

    def test_saida_em_texto_nao_mede_capacidades(self):
        _code, lines, collect = self.doctor(False)
        collect.assert_not_called()
        self.assertFalse([line for line in lines if "proc.loadavg" in line])
        self.assertTrue(lines[-1].startswith("resultado: "))


if __name__ == "__main__":
    unittest.main()
