import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def module():
    path = ROOT / 'scripts/benchmark_local_single_image_alias_v1.py'
    spec = importlib.util.spec_from_file_location('batch1_alias_test', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_explicit_kth_alias():
    assert module().deit_archive_path('/cache', 'KTHTIPS2b') == Path('/cache/KTH-TIPS2-b/deit_s.npy')


def test_other_datasets_unchanged():
    for name in ('DTD', 'FMD', 'CUReT', 'SoilOriginal', 'Outex13Official1360'):
        assert module().deit_archive_path('/cache', name) == Path('/cache') / name / 'deit_s.npy'


def test_no_numerical_or_timing_change():
    original = ast.parse((ROOT / 'scripts/benchmark_local_single_image.py').read_text())
    amended = ast.parse((ROOT / 'scripts/benchmark_local_single_image_alias_v1.py').read_text())
    amended.body = [n for n in amended.body if not isinstance(n, ast.FunctionDef) or n.name != 'deit_archive_path']
    class UndoAlias(ast.NodeTransformer):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == 'deit_archive_path':
                root, dataset = node.args
                return ast.BinOp(left=ast.BinOp(left=root, op=ast.Div(), right=dataset),
                                 op=ast.Div(), right=ast.Constant(value='deit_s.npy'))
            return self.generic_visit(node)
    amended = UndoAlias().visit(amended)
    assert ast.dump(original, include_attributes=False) == ast.dump(amended, include_attributes=False)
