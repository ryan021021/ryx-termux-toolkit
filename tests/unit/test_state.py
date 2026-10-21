import json
import tempfile
import unittest
from pathlib import Path

from ryx.state import STATE_VERSION, StateError, empty_state, load_state, save_state, update_state
from tests.helpers import IS_WINDOWS


class StateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.file = Path(self._tmp.name) / "sub" / "state.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_sem_arquivo_devolve_estado_vazio(self):
        self.assertEqual(load_state(self.file), empty_state())

    def test_ida_e_volta(self):
        data = empty_state()
        data["shell"]["a"] = {"x": 1}
        save_state(self.file, data)
        self.assertEqual(load_state(self.file)["shell"], {"a": {"x": 1}})

    def test_nao_deixa_temporario_para_tras(self):
        save_state(self.file, empty_state())
        self.assertEqual([p.name for p in self.file.parent.iterdir()], ["state.json"])

    @unittest.skipIf(IS_WINDOWS, "permissão POSIX")
    def test_arquivo_fica_com_modo_0600(self):
        save_state(self.file, empty_state())
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o600)

    def test_json_corrompido_vira_state_error_que_cita_o_arquivo(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text("{nao e json")
        with self.assertRaisesRegex(StateError, "state.json: ilegível"):
            load_state(self.file)

    def test_formato_estranho_e_versao_futura_sao_recusados(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text("[]")
        with self.assertRaisesRegex(StateError, "formato desconhecido"):
            load_state(self.file)
        self.file.write_text(json.dumps({"version": STATE_VERSION + 1}))
        with self.assertRaisesRegex(StateError, "mais nova"):
            load_state(self.file)

    def test_arquivo_ilegivel_vira_state_error(self):
        self.file.parent.mkdir(parents=True)
        cases = {
            "nao utf-8": bytes([0x80, 0x81, 0x82]),
            "aninhamento absurdo": b"[" * 200_000,
            "vazio": b"",
        }
        for label, raw in cases.items():
            with self.subTest(label=label):
                self.file.write_bytes(raw)
                with self.assertRaisesRegex(StateError, "state.json: ilegível"):
                    load_state(self.file)

    def test_tipos_errados_nos_campos_sao_recusados(self):
        self.file.parent.mkdir(parents=True)
        variants = [
            {"shell": []},
            {"shell": "x"},
            {"shell": None},
            {"shell": {"~/.bashrc": "texto"}},
            {"backups": {}},
            {"backups": "x"},
            {"backups": None},
        ]
        for variant in variants:
            with self.subTest(variant=variant):
                self.file.write_text(json.dumps({"version": 1, **variant}))
                with self.assertRaisesRegex(StateError, "formato inválido"):
                    load_state(self.file)

    def test_estado_antigo_ganha_as_chaves_novas(self):
        self.file.parent.mkdir(parents=True)
        self.file.write_text(json.dumps({"version": 1}))
        self.assertEqual(load_state(self.file)["backups"], [])

    def test_update_state_aplica_a_mudanca(self):
        update_state(self.file, lambda s: s["backups"].append("a"))
        update_state(self.file, lambda s: s["backups"].append("b"))
        self.assertEqual(load_state(self.file)["backups"], ["a", "b"])

    def test_erro_dentro_da_mudanca_nao_toca_o_arquivo(self):
        save_state(self.file, empty_state())
        before = self.file.read_bytes()

        def boom(_state):
            raise RuntimeError("falhou no meio")

        with self.assertRaises(RuntimeError):
            update_state(self.file, boom)
        self.assertEqual(self.file.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
