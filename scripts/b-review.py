"""B's supplementary review gate. Uses existing dependencies; owns isolated servers only."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from urllib.request import ProxyHandler, build_opener
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / os.environ.get('B_REVIEW_EVIDENCE', 'docs/evidence/b-candidate')


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ui-only', action='store_true', help='Partial browser recheck, not the full gate')
    args = parser.parse_args()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    runtime = ROOT / '.runtime/b-candidate'
    runtime.mkdir(parents=True, exist_ok=True)
    results = []
    environment = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', B_REVIEW_EVIDENCE=str(EVIDENCE))
    node = shutil.which('node')

    def run(name, command, cwd=ROOT, timeout=180):
        started = time.monotonic()
        log = runtime / f'{name}.log'
        with log.open('w', encoding='utf-8') as output:
            try:
                completed = subprocess.run(command, cwd=cwd, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=timeout)
                code = completed.returncode
            except (OSError, subprocess.TimeoutExpired):
                code = 2
        results.append({'check': name, 'exit_code': code, 'seconds': round(time.monotonic() - started, 2), 'log': log.relative_to(ROOT).as_posix()})
        print(f'{name}: exit {code}', flush=True)
        return code

    if not args.ui_only:
        run('lock', [sys.executable, 'scripts/check-lock.py'])
        run('pip-check', [sys.executable, '-m', 'pip', 'check'])
        for name, target in [('pytest', 'backend/tests'), ('candidate-tests', 'backend/review_tests')]:
            xml = runtime / f'{name}.xml'
            run(name, [sys.executable, '-m', 'pytest', '-c', 'backend/pytest.ini', target, '-q', f'--junitxml={xml}'])
            if xml.exists():
                suites = ET.parse(xml).getroot()
                # JSON keeps portable IDs/results; full traces stay in ignored .runtime.
                tests = [{'id': test.get('classname') + '.' + test.get('name'), 'status': 'failed' if test.find('failure') is not None or test.find('error') is not None else 'skipped' if test.find('skipped') is not None else 'passed'} for test in suites.iter('testcase')]
                (EVIDENCE / f'{name}.json').write_text(json.dumps(tests, indent=2) + '\n', encoding='utf-8')
        run('rule-boundary', [sys.executable, 'backend/scripts/validate_boundary.py'])
        if node:
            run('typecheck', [node, 'frontend/node_modules/typescript/bin/tsc', '--noEmit', '-p', 'frontend/tsconfig.json'])
            run('build', [node, 'node_modules/vite/bin/vite.js', 'build'], ROOT / 'frontend')
        else:
            results.append({'check': 'frontend-build', 'exit_code': 2, 'reason': 'Node missing'})
        package = json.loads((ROOT / 'frontend/package.json').read_text(encoding='utf-8-sig'))
        npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
        component_json = runtime / 'component-results.json'
        component_args = ['test', '--', '--reporter=json', f'--outputFile={component_json}']
        if component_json.exists():
            component_json.unlink()
        if package.get('scripts', {}).get('test') and os.environ.get('NPM_CLI') and node:
            run('A16-component-tests', [node, os.environ['NPM_CLI'], *component_args], ROOT / 'frontend')
        elif package.get('scripts', {}).get('test') and npm:
            command = ['cmd.exe', '/d', '/c', npm, *component_args] if sys.platform == 'win32' else [npm, *component_args]
            run('A16-component-tests', command, ROOT / 'frontend')
        else:
            results.append({'check': 'A16-component-test-command', 'exit_code': 2, 'reason': 'npm executable and test command required; component infrastructure owned by A'})
        if component_json.exists():
            component = json.loads(component_json.read_text(encoding='utf-8'))
            portable = {'passed': component['numPassedTests'], 'failed': component['numFailedTests'], 'tests': [{'name': case['fullName'], 'status': case['status']} for suite in component['testResults'] for case in suite['assertionResults']]}
            (EVIDENCE / 'component-tests.json').write_text(json.dumps(portable, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    processes = []
    try:
        if not node:
            raise RuntimeError('Node is required for browser checks')
        backend_port = free_port()
        frontend_port = free_port()
        while frontend_port == backend_port:
            frontend_port = free_port()
        with tempfile.TemporaryDirectory(prefix='database-', dir=runtime) as temp:
            environment.update(DATABASE_URL=f"sqlite:///{(Path(temp) / 'review.db').as_posix()}", LLM_API_KEY='', API_PROXY_TARGET=f'http://127.0.0.1:{backend_port}', VITE_API_BASE_URL='/api', PREVIEW_URL=f'http://127.0.0.1:{frontend_port}', B_REVIEW_ISOLATED='1')
            code = f"import os,uvicorn; from app.main import create_app; from app.core.config import Settings; uvicorn.run(create_app(Settings(_env_file=None,database_url=os.environ['DATABASE_URL'],llm_api_key='')),host='127.0.0.1',port={backend_port})"
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            try:
                for name, command, cwd in [('backend', [sys.executable, '-c', code], ROOT / 'backend'), ('frontend', [node, 'node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', str(frontend_port), '--strictPort'], ROOT / 'frontend')]:
                    with (runtime / f'{name}.log').open('w', encoding='utf-8') as log:
                        processes.append(subprocess.Popen(command, cwd=cwd, env=environment, stdout=log, stderr=subprocess.STDOUT, creationflags=flags))
                opener = build_opener(ProxyHandler({}))
                deadline = time.monotonic() + 40
                while time.monotonic() < deadline:
                    if any(p.poll() is not None for p in processes):
                        raise RuntimeError('Isolated service stopped; see local logs')
                    try:
                        with opener.open(environment['PREVIEW_URL'] + '/api/health', timeout=2) as response:
                            if json.load(response).get('database') == 'ok':
                                break
                    except Exception:
                        time.sleep(.25)
                else:
                    raise RuntimeError('Isolated service readiness timed out')
                with opener.open(f'http://127.0.0.1:{backend_port}/docs', timeout=3) as response:
                    assert response.status == 200 and b'swagger-ui' in response.read()
                with opener.open(f'http://127.0.0.1:{backend_port}/openapi.json', timeout=3) as response:
                    specification = json.load(response)
                (EVIDENCE / 'api-inventory.json').write_text(json.dumps({'health': 'database ok', 'docs': 200, 'version': specification['info']['version'], 'paths': sorted(specification['paths'])}, indent=2) + '\n', encoding='utf-8')
                results.append({'check': 'health-docs-openapi', 'exit_code': 0})
                run('browser', [node, 'frontend/tests/b-ui-review.mjs'], timeout=240)
                run('existing-real-smoke', [node, 'frontend/tests/d-ui-smoke.mjs'], timeout=90)
                smoke_report = ROOT / 'frontend/tests/artifacts/report.json'
                if smoke_report.exists():
                    shutil.copyfile(smoke_report, EVIDENCE / 'existing-smoke.json')
            finally:
                for process in reversed(processes):
                    if process.poll() is None:
                        if sys.platform == 'win32':
                            # venv's Windows launcher owns a child Python process.
                            # Stop only this runner's process tree before removing its DB.
                            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
    except Exception as error:
        results.append({'check': 'isolated-services', 'exit_code': 2, 'reason': type(error).__name__})
    summary = {'scope': 'A updated local folder, B candidate review; no release approval', 'run_at': datetime.now(timezone.utc).isoformat(), 'partial': args.ui_only, 'python': sys.version.split()[0], 'results': results, 'status': 'failed' if any(r['exit_code'] for r in results) else 'passed', 'candidate_git_commit': None}
    (EVIDENCE / ('ui-run-summary.json' if args.ui_only else 'summary.json')).write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)
    return 1 if summary['status'] == 'failed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
