import os
import time
import json
import ctypes
import resource
import tempfile
import traceback
import threading
import subprocess
import multiprocessing as mp
from pprint import pprint

import numpy as np

# from prover.lean.ast_parser import lean4_parser
# from prover.workers import ProcessScheduler
# from prover.utils import AttrDict


HOME_DIR = os.path.expanduser('~')
DEFAULT_LAKE_PATH = f'{HOME_DIR}/.elan/bin/lake'
DEFAULT_LEAN_WORKSPACE = '/home/hanyuan/Desktop/reason/DeepSeek-Prover-V1.5/mathlib4'


def verify_lean4_file(code, lake_path=DEFAULT_LAKE_PATH, lean_workspace=DEFAULT_LEAN_WORKSPACE, last_env=None, verbose=False, timeout=300, allTactics=False, ast=False, premises=False, tactics=False):
    '''
    this code is copied from Deepseek-Prover-V1.5
    '''
    
    command = dict(cmd=code, allTactics=allTactics, ast=ast, tactics=tactics, premises=premises)
    if last_env is not None:
        command.update(env=last_env)
    message_str = json.dumps(command, ensure_ascii=False)
    if verbose:
        print(message_str)
    start_time = time.time()
    system_messages = ''
    try:
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as temp_file:
            temp_file.write(message_str + "\r\n\r\n")
            temp_file.seek(0)
            outputs = subprocess.run([lake_path, "exe", 'repl'], stdin=temp_file, capture_output=True, text=True, cwd=lean_workspace, timeout=timeout)
        result = json.loads(outputs.stdout)
        #ast_results = lean4_parser(code, result['ast']) if 'ast' in result and result['ast'] else {}
        result = {
            "sorries" : result.get('sorries', []), 
            "tactics" : result.get('tactics', []),
            "errors" : [m for m in result.get('messages', []) if m['severity'] == 'error'],
            "warnings" : [m for m in result.get('messages', []) if m['severity'] == 'warning'],
            "infos" : [m for m in result.get('messages', []) if m['severity'] == 'info'],
            "system_messages" : system_messages,
            "system_errors" : None,
            #"ast" : ast_results,
            "verified_code" : code,
        }
        result['pass'] = not result['errors']
        result['complete'] = result['pass'] and not result['sorries'] and not any("declaration uses 'sorry'" in warning['data'] or 'failed' in warning['data'] for warning in result['warnings'])
    except:
        result = {
            "pass": False,
            "complete": False,
            "system_errors": traceback.format_exc(),
            "system_messages": system_messages
        }
    result['verify_time'] = time.time() - start_time
    return result

if __name__ == '__main__':
    # # read in a MiniF2F problem
    # miniF2F_path = "/home/hanyuan/Desktop/reason/DeepSeek-Prover-V1.5/datasets/minif2f.jsonl"
    # with open(miniF2F_path, 'r') as f:
    #     miniF2F = f.readlines()[0]

    # print(f"Problem:\n{miniF2F}\n")

    # code: str = miniF2F['header'] + 

    deepseek_path = "/home/hanyuan/Desktop/reason/DeepSeek-Prover-V1.5"
    code_path = os.path.join(deepseek_path,
                             "mathlib4/.lake/packages/REPL/test/aime_1983_p9.in")
    with open(code_path, 'r') as f:
        problem = json.load(f)

    print(f"Problem:\n{problem}\n")

    result = verify_lean4_file(problem['cmd'])
    import pdb; pdb.set_trace()


