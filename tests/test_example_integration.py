"""
Smoke test: el ejemplo integrado (examples/ejemplo_recuperacion_calor_generico.py)
debe correr de principio a fin sin lanzar ninguna excepcion -- encadena los
5 modulos del toolkit, asi que es la prueba mas directa de que realmente
funcionan juntos, no solo por separado.
"""
import subprocess
import sys
import os

EXAMPLE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "examples", "ejemplo_recuperacion_calor_generico.py"
)


def test_integration_example_runs_without_error():
    result = subprocess.run(
        [sys.executable, EXAMPLE_PATH],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (
        f"El ejemplo integrado fallo (exit code {result.returncode}):\n"
        f"{result.stderr}"
    )
    # Confirma que efectivamente encadeno los 5 modulos, no que se salio
    # temprano silenciosamente
    for marca in ["[1] Balance de calor", "[2] Intercambiador de placas",
                  "[3] Tubería", "[4] Bomba", "[5] Estanque"]:
        assert marca in result.stdout, f"Falta la seccion '{marca}' en la salida"
