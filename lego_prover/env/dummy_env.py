import gymnasium as gym
from typing import List, SupportsFloat, Any, Tuple, Dict
from copy import copy
import re
import time

SPECIAL_SYMBOL = {
    "≥": "\<ge>",
    "≤": "\<le>",
    "≠": "\<noteq>",
    "∧": "\<and>",
    "∨": "\<or>",
    "¬": "\<not>",
    "⇒": "\<Rightarrow>",
    "⇔": "\<longleftrightarrow>",
    "→": "\<longrightarrow>",
    "∀": "\<forall>",
    "∃": "\<exists>",
    "∈": "\<in>",
    "⊆": "\<subseteq>",
    "∪": "\<union>",
    "∩": "\<inter>",
    "⊂": "\<subset>",
    "∅": "\<emptyset>",
    "∑": "\<sum>",
    "∫": "\<integral>",
    "≡": "\<equiv>",
    "⊢": "\<turnstile>",
    "⊨": "\<models>",
    "⊥": "\<bottom>",
    "⊤": "\<top>",
    "≜": "\<triangleq>",
    "≈": "\<approx>",
    "≅": "\<cong>",
    "⋀": "\<And>",
    "⋁": "\<Or>",
    "⋂": "\<Inter>",
    "⋃": "\<Union>",
    "⊗": "\<otimes>",
    "∗": "\<star>",
    "λ": "\<lambda>",
    "∞": "\<infinity>",
    "ℕ": "\<nat>",
    "ℤ": "\<int>",
    "ℚ": "\<rat>",
    "ℝ": "\<real>",
    "ℂ": "\<complex>",
    "↔": "\<leftrightarrow>",
    "‹": "\<open>",
    "›": "\<close>",
    "α": "\<alpha>",
    "β": "\<beta>",
    "γ": "\<gamma>",
 
    # "𝑎": "a",
    # "¯": "?",
    # "∤": "?",
    "sorry": "sledgehammer",
    "oops": "sledgehammer",
}


class DummyEnv(gym.Env):
    def __init__(self):
        self.action_space = gym.spaces.Discrete(2)
        self.observation_space = gym.spaces.Discrete(2)

    def reset(self):
        return f"Starting is successful: {True}"
    
    def _verify_step_by_step(self, steps, quick_check=False):
        done = False
        reason = ''
        success = True
        step_results = []
        tls_name = 'default'
        error_step_index = None
        corrected_step = {}
        for i, step in enumerate(steps):
            step_time = time.time()
            step_time = time.time() - step_time
            obs = "obs_string"
            step_results.append({
                "index": i,
                "step": step,
                "output": obs,
                "step_time": step_time,
            })

        result = {
            'success': success,
            'reason': reason,
            'num_steps': len(steps),
            'last_step': len(step_results),
            'error_step_index': error_step_index,
            'step_results': step_results,
            'corrected_steps': corrected_step,
        }

        if quick_check is True:
            return success

        return result
    
    def _post_process_error_msg(self, code, parsed_code, verified_result):
        old_code = copy(code)
        only_refresh_code = False
        if "Timeout after" in verified_result["reason"]:
            verified_result["reason"] = \
            'Step timeout error (line 1): the step takes more than 10 seconds to run. At command "<cmd>" (line 1)'
        if verified_result["success"] is True:
            only_refresh_code = True
        elif re.search(r"\(line [0-9]+\)", verified_result["reason"]) is None and \
            re.search(r'At command "(.?)+"', verified_result["reason"]) is None:
            # self.logger.info("No line number or at command, skip...")
            # self.logger.info("The error is:")
            # self.logger.info(verified_result["reason"])
            only_refresh_code = True
        
        matched_codes = []
        for ix, step in enumerate(verified_result["step_results"]):
            step_code = step["step"].strip()
            if step_code not in code:
                # This error is too complicated, I give up
                if len(step["output"]) != 0:
                    return verified_result, old_code, "".join(matched_codes), code
                else:
                    if step_code.startswith("(*"):
                        start_index = code.index("(*")
                        # self.logger.info(f"Parsed code: {step_code}")
                        # self.logger.info(f"ori code: {code}")
                        for i in range(len(step_code)):
                            if code[i+start_index] != step_code[i]:
                                assert step_code[i] == "?"
                                code = code[:i+start_index] + step_code[i] +  code[i+start_index+1:]
                        # self.logger.info(f"new code: {code}")
                    else:
                        # self.logger.info(f"Parsed code: {step_code}")
                        # self.logger.info(f"ori code: {code}")
                        assert False, "You should add the list!"
            new_step = None
            if ix in verified_result["corrected_steps"]:
                old_step, new_step = verified_result["corrected_steps"][ix]
                assert old_step == step_code
            matched_code = code[:code.index(step_code) + len(step_code)]
            code = code[code.index(step_code) + len(step_code):]
            if new_step is not None:
                matched_code = matched_code.replace(step_code.strip(), new_step.strip())
            matched_codes.append(matched_code)
        
        correct_code = "".join(matched_codes)
        incorrect_code = code

        if not only_refresh_code:
            previous_code = "".join(matched_codes)
            line_number = previous_code.strip().count("\n") + 1

            error_msg = re.sub(r"\(line [0-9]+\)", f"(line {line_number})", verified_result["reason"])
            error_msg = re.sub(r'At command "(.?)+"', f'At command "{repr(step_code)}"', error_msg)

            verified_result["reason"] = error_msg
        
        new_code = "".join(matched_codes + [code])

        return verified_result, new_code, correct_code, incorrect_code
    
    def _post_process_skill_code(self, correct_partial_code):
        start_keyword = ["lemma", "theorem", "definition", "fun", "end"]
        
        parsed_code = correct_partial_code
        all_codes = []
        current_code_set = []
        for code in parsed_code:
            if code.startswith(tuple(start_keyword)):
                if len(current_code_set) > 0:
                    skill_code = "\n".join(current_code_set)
                    all_codes.append(skill_code.strip())
                current_code_set = [code]
            else:
                assert len(all_codes) == 0 or len(current_code_set) > 0
                if len(current_code_set) != 0:
                    current_code_set.append(code)
        
        # remove empty code:
        tmp_code = []
        for code in all_codes:
            #code = self._beautify(code, correct_partial_code)
            if len(code) == 0:
                continue
            tmp_code.append(code)
        all_codes = tmp_code

        # resolve dependence
        all_names = []
        for code in all_codes:
            all_names.append(self.get_lemma_name(code))
        
        name_and_codes = list(zip(all_names, all_codes))
        name_and_codes = sorted(name_and_codes, key=lambda x: len(x[0]), reverse=True)
        if len(name_and_codes) > 0:
            all_names, all_codes = list(zip(*name_and_codes))
        else:
            all_names, all_codes = [], []
        
        new_codes = []
        for ix, code in enumerate(all_codes):
            current_code = code
            escape_names = [all_names[ix]]
            while True:
                updated = False
                for jx, name in enumerate(all_names):
                    if name in escape_names:
                        continue
                    if name in current_code:
                        current_code = f"{all_codes[jx]}\n\n{current_code}"
                        escape_names.append(name)
                        updated = True
                if updated is False:
                    break
            new_codes.append(current_code)
        
        return list(zip(all_codes, new_codes))
    
    def step(
        self,
        code: str,
        formal_statement: str = None,
        quick_check: bool = False,
    ) -> Tuple[ObsType, SupportsFloat, bool, bool, Dict[str, Any]]:
        # if "theory" in code:
        #     assert "begin" in code and "end" in code, \
        #         "Outer syntax error: not complete theorem file"
        #     code = code[code.index("begin") + len("begin"): code.index("end")].strip()
        
        # step 0: replace special token
        for symbol, value in SPECIAL_SYMBOL.items():
            if symbol in code:
                code = code.replace(symbol, value)

        # step 1: parse code
        parsed_code: List[str] = [code]

        # step 2: step by step verification
        verified_result = self._verify_step_by_step(parsed_code, quick_check=quick_check)
        if quick_check:
            return verified_result, None, None, None

        # step 3: post process error message
        verified_result, code, correct_partial_code, incorrect_code = self._post_process_error_msg(code, parsed_code, verified_result)

        # step 4: get skill code
        skill_codes = self._post_process_skill_code(correct_partial_code)

        # step 5: get request
        requests = ["requests"]
        
        return verified_result, code, skill_codes, requests
    
    def get_lemma_name(self, code):
        name = "no_name"
        try:
            if code.startswith('lemma'):
                name = re.findall(r"lemma (.+):", code)[0].strip()
            elif code.startswith('theorem'):
                name = re.findall(r"theorem (.+):", code)
                if len(name) == 0:
                    name = "theorem_with_no_name"
                else:
                    name = name[0].strip()
            elif code.startswith('fun') and not code.startswith('function'):
                name = re.findall(r"fun (.+) ::", code)[0].strip()
            elif code.startswith('function'):
                name = re.findall(r"function (.+) ::", code)[0].strip()
            elif code.startswith('definition'):
                name = re.findall(r"definition (.+) ::", code)[0].strip()
            else:
                assert False, f"new code type: {code}"
        except Exception as e:
            print(f"[get_lemma_name] Error get lemma name, error: {e}, code: {code}")
            #self.logger.info(f"Error get lemma name, error: {e}, code: {code}")
        return name
    
    def get_marker_statement(self, code):
        return code
    
    
