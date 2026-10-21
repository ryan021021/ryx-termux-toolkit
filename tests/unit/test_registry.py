import types
import unittest

from ryx.registry import MODULE_NAMES, ModuleSpec, Registry, build_registry


def fake_module(name):
    return types.SimpleNamespace(SPEC=ModuleSpec(name, f"resumo de {name}"))


class RegistryTest(unittest.TestCase):
    def test_todos_os_modulos_ligados_por_padrao(self):
        registry = build_registry({})
        self.assertEqual([s.name for s, _ in registry.specs()], MODULE_NAMES)
        self.assertTrue(all(enabled for _, enabled in registry.specs()))

    def test_flag_desliga_o_modulo(self):
        registry = build_registry({"ai": False})
        enabled = [m.SPEC.name for m in registry.enabled_modules()]
        self.assertNotIn("ai", enabled)
        self.assertIn("shell", enabled)
        self.assertFalse(dict((s.name, e) for s, e in registry.specs())["ai"])

    def test_modulo_duplicado_e_recusado(self):
        registry = Registry()
        registry.add(fake_module("x"))
        with self.assertRaisesRegex(ValueError, "duplicado"):
            registry.add(fake_module("x"))

    def test_todo_modulo_declara_estabilidade_e_resumo(self):
        for spec, _ in build_registry({}).specs():
            with self.subTest(module=spec.name):
                self.assertTrue(spec.summary)
                self.assertIn(spec.stability, {"experimental", "beta", "stable"})

    def test_todo_modulo_tem_add_parser_e_run(self):
        for module in build_registry({}).enabled_modules():
            with self.subTest(module=module.SPEC.name):
                self.assertTrue(callable(module.add_parser))
                self.assertTrue(callable(module.run))


if __name__ == "__main__":
    unittest.main()
