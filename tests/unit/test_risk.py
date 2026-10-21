"""T105 / ADR-0002: classes L0–L3, nega por padrão e aprovação presa ao hash do plano."""

import unittest

from ryx.permissions import (
    Approval,
    Level,
    Plan,
    Risk,
    decide,
    decide_plan,
    level_of,
)


def plan(**over):
    base = {"operation": "packages.install", "args": ("curl",), "target": "a15", "version": "1"}
    base.update(over)
    return Plan(**base)


class LevelOfTest(unittest.TestCase):
    def test_riscos_atuais_mapeiam_para_l0_l2_l3(self):
        self.assertIs(level_of(Risk.READ), Level.L0)
        self.assertIs(level_of(Risk.REVERSIBLE), Level.L2)
        self.assertIs(level_of(Risk.SENSITIVE), Level.L3)

    def test_classe_ausente_ou_desconhecida_e_l3(self):
        for raw in (None, "inventada", 7, object()):
            self.assertIs(level_of(raw), Level.L3)


class HashDoPlanoTest(unittest.TestCase):
    def test_mesmo_plano_mesmo_hash(self):
        self.assertEqual(plan().digest(), plan().digest())

    def test_qualquer_campo_muda_o_hash(self):
        base = plan().digest()
        for over in ({"operation": "x"}, {"args": ("wget",)}, {"target": "b"}, {"version": "2"}):
            self.assertNotEqual(base, plan(**over).digest(), over)

    def test_separador_nao_confunde_argumentos(self):
        self.assertNotEqual(plan(args=("a b",)).digest(), plan(args=("a", "b")).digest())


class DecidePlanTest(unittest.TestCase):
    def test_l0_executa_sem_aprovacao(self):
        self.assertTrue(decide_plan(plan(), Level.L0).execute)

    def test_l1_nao_existe_e_nega(self):
        p = plan()
        d = decide_plan(p, Level.L1, apply=True, yes=True, approval=Approval(p.digest(), "human"))
        self.assertFalse(d.execute)

    def test_sem_classe_nega_mesmo_aprovado(self):
        p = plan()
        d = decide_plan(p, None, apply=True, yes=True, approval=Approval(p.digest(), "human"))
        self.assertFalse(d.execute)

    def test_classe_inventada_nega_mesmo_aprovada(self):
        p = plan()
        d = decide_plan(p, "L2", apply=True, yes=True, approval=Approval(p.digest(), "human"))
        self.assertFalse(d.execute)

    def test_l2_sem_apply_simula(self):
        p = plan()
        self.assertFalse(decide_plan(p, Level.L2, approval=Approval(p.digest(), "human")).execute)

    def test_l2_sem_aprovacao_nega(self):
        self.assertFalse(decide_plan(plan(), Level.L2, apply=True).execute)

    def test_l2_aprovado_executa(self):
        p = plan()
        self.assertTrue(decide_plan(p, Level.L2, apply=True, approval=Approval(p.digest(), "human")).execute)

    def test_plano_mudou_depois_da_aprovacao_nega(self):
        aprovado = plan()
        approval = Approval(aprovado.digest(), "human")
        executado = plan(args=("curl", "wget"))
        d = decide_plan(executado, Level.L2, apply=True, approval=approval)
        self.assertFalse(d.execute)
        self.assertIn("plano mudou", d.reason)

    def test_l3_com_hash_errado_nega_mesmo_com_yes(self):
        d = decide_plan(plan(), Level.L3, apply=True, yes=True, approval=Approval(plan(args=("x",)).digest(), "human"))
        self.assertFalse(d.execute)

    def test_hash_de_tipo_errado_nega(self):
        self.assertFalse(decide_plan(plan(), Level.L2, apply=True, approval=Approval(None, "human")).execute)

    def test_l3_exige_yes(self):
        p = plan()
        a = Approval(p.digest(), "human")
        self.assertFalse(decide_plan(p, Level.L3, apply=True, approval=a).execute)
        self.assertTrue(decide_plan(p, Level.L3, apply=True, yes=True, approval=a).execute)

    def test_l3_nunca_aprovado_por_agente(self):
        p = plan()
        d = decide_plan(p, Level.L3, apply=True, yes=True, approval=Approval(p.digest(), "agent"))
        self.assertFalse(d.execute)

    def test_aprovacao_de_origem_desconhecida_nega_em_l2(self):
        p = plan()
        self.assertFalse(decide_plan(p, Level.L2, apply=True, approval=Approval(p.digest(), "")).execute)


class CompatibilidadeTest(unittest.TestCase):
    def test_decide_atual_continua_igual(self):
        esperado = {
            (Risk.READ, False, False): True,
            (Risk.READ, True, True): True,
            (Risk.REVERSIBLE, False, False): False,
            (Risk.REVERSIBLE, True, False): True,
            (Risk.SENSITIVE, True, False): False,
            (Risk.SENSITIVE, True, True): True,
            (Risk.SENSITIVE, False, True): False,
        }
        for (risk, apply, yes), execute in esperado.items():
            self.assertIs(decide(risk, apply, yes).execute, execute, (risk, apply, yes))


if __name__ == "__main__":
    unittest.main()
