"""
Orquestrador do projeto JAM Mapper.
Inicia FastAPI (backend) e Streamlit (frontend) simultaneamente.
"""

import subprocess
import time
import sys
import os
from pathlib import Path


def main():
    """Inicia FastAPI e Streamlit em subprocessos simultâneos."""

    # Obter diretório do script (raiz do projeto)
    script_dir = Path(__file__).parent.absolute()

    print("=" * 60)
    print("🛡️  JAM Mapper - Iniciando Sistema".center(60))
    print("=" * 60)
    print()

    processos = []

    try:
        # 1. Iniciar FastAPI
        print("🚀 Iniciando FastAPI Backend...")
        print("   📡 Servidor em: http://localhost:8000")
        print("   📚 Documentação: http://localhost:8000/docs")
        print()

        processo_api = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "jam_mapper.api.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ],
            cwd=str(script_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        processos.append(("FastAPI", processo_api))
        print("✅ FastAPI iniciado!")
        print()

        # Aguardar 2 segundos para API iniciar
        print("⏳ Aguardando inicialização da API (2s)...")
        time.sleep(2)
        print()

        # 2. Iniciar Streamlit
        print("🚀 Iniciando Streamlit Frontend...")
        print("   🌐 Dashboard em: http://localhost:8501")
        print()

        processo_streamlit = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "jam_mapper/web/streamlit_app.py",
                "--logger.level=error",
                "--client.showErrorDetails=false",
            ],
            cwd=str(script_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        processos.append(("Streamlit", processo_streamlit))
        print("✅ Streamlit iniciado!")
        print()

        print("=" * 60)
        print("✨ Sistema JAM Mapper pronto!".center(60))
        print("=" * 60)
        print()
        print("📱 Acesse:")
        print("   🌐 Dashboard: http://localhost:8501")
        print("   📚 API Docs:  http://localhost:8000/docs")
        print()
        print("⌨️  Pressione CTRL+C para parar o sistema")
        print()

        # Manter processos rodando e monitorar
        while True:
            time.sleep(1)
            for nome, processo in processos:
                if processo.poll() is not None:
                    print(f"⚠️  {nome} foi encerrado!")

    except KeyboardInterrupt:
        print()
        print()
        print("=" * 60)
        print("🛑 Encerrando JAM Mapper...".center(60))
        print("=" * 60)

        for nome, processo in processos:
            try:
                print(f"Encerrando {nome}...", end=" ")
                processo.terminate()
                processo.wait(timeout=5)
                print("✅")
            except subprocess.TimeoutExpired:
                print("Force kill...", end=" ")
                processo.kill()
                print("✅")
            except Exception as e:
                print(f"Erro: {e}")

        print()
        print("👋 Sistema encerrado com sucesso!")
        print()
        sys.exit(0)

    except Exception as e:
        print(f"❌ Erro ao iniciar sistema: {e}")
        for nome, processo in processos:
            try:
                processo.terminate()
            except Exception:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
