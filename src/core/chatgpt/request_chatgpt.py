import copy
import math
import os
import shutil
import time
import json
from dotenv import dotenv_values
import openai

# from core.database.engine import count_collected_samples_by_conditions, save
from core.tools.java_lang import get_node_by_position, load_ast_nodes, load_origin_code_node
from core.tools.log import printlog
from core.tools.patch import load_patch_file, read_patch_file
from core.tools.persist import write_to_file
from core.tools.tokenizer import chatgpt_tokenize
from core.tools.prompt import chatgpt_prompt_generation
from core.tools.extract_code import extract_code
from core.utils import get_benchmark
from core.chatgpt.chat import request_chatgpt_pr


config = dotenv_values(".env")
openai.api_key = config.get('OPENAI_API_KEY')
DEFS4J_HOME = config.get("DEFS4J_HOME")


def load_code_node(fixed_file_path, buggy_file_path, countable_diffs):
    fixed_node, i = load_origin_code_node(
        fixed_file_path, countable_diffs[0].sorted_changes())
    buggy_nodes = load_ast_nodes(buggy_file_path)
    buggy_node = get_node_by_position(buggy_nodes, fixed_node, i)
    return fixed_node, buggy_node


# def request_chatgpt_pr(prompt, request_params, args):
#     # https://beta.openai.com/docs/api-reference/completions/create
#     if args.prompt_level == 'easy':
#         response = openai.ChatCompletion.create(
#             model=request_params['model'],
#             messages=[{"role": "user", "content": prompt}],
#             temperature=request_params['temperature'],
#             top_p=request_params['top_p'],
#             frequency_penalty=request_params['frequency_penalty'],
#             presence_penalty=request_params['presence_penalty'],
#         )
#     elif args.prompt_level == 'advanced':
#         response = openai.ChatCompletion.create(
#             model=request_params['model'],
#             messages=[{'role': 'system', 'content': prompt[0]},
#                     {"role": "user", "content": prompt[1]}],
#             temperature=request_params['temperature'],
#             top_p=request_params['top_p'],
#             frequency_penalty=request_params['frequency_penalty'],
#             presence_penalty=request_params['presence_penalty'],
#         )
#     # TODO: add more domain prompt
#     printlog('--->', response)
#     return response


def apply_text_to_buggy_version(buggy_bug_path, response_text, buggy_node):
    printlog('fixed_bug_path: ', buggy_bug_path)
    printlog('fixed_node: ', buggy_node)
    printlog('response_text:\n ', response_text)
    try:
        response_text_lines = response_text.split("\n")
        with open(buggy_bug_path, 'r') as file:
            buggy_bug_lines = file.readlines()
        new_buggy_bug_file = "".join(buggy_bug_lines[0:buggy_node.start_pos - 1]) + \
            "\n".join(response_text_lines) + \
            "".join(buggy_bug_lines[buggy_node.end_pos:])
        write_to_file(buggy_bug_path, new_buggy_bug_file)
        return True, None
    except Exception as e:
        printlog('Error: ', e)
        printlog('buggy_bug_path: ', buggy_bug_path)
        return False, e


def get_fixed_bug_path(bug_dir, patch_file_path):
    countable_diffs, _ = load_patch_file(None, patch_file_path)
    return bug_dir + "_fixed/" + countable_diffs[0].file_path


# revert fixed bug file after testing codex response
def revert_response_to_buggy_version(bug_dir, benchmark, working_directory, project, bug_id):
    printlog('revert buggy bug file after testing codex response')
    buggy_path = bug_dir + "_buggy/"
    printlog('clean buggy_bug_path: ', buggy_path)
    shutil.rmtree(buggy_path)
    buggy_bug = checkout_bug(
        benchmark, working_directory, project, bug_id, 'buggy')
    buggy_bug.compile()


def checkout_bug(benchmark, working_directory, project, bug_id, version):
    bug_identifier = project + '_' + bug_id

    bug_path = os.path.join(working_directory,
                            "%s_%s_%s_%s" % (benchmark.name, project, bug_id, version))

    printlog('bug_identifier: ', bug_identifier)
    bug = benchmark.get_bug(bug_identifier)
    printlog('bug: ', bug)
    is_buggy_version = version == 'buggy'
    bug.checkout(bug_path, is_buggy_version)

    return bug


def checkout_buggy_version(defects4j_config, benchmark, working_directory, project, bug_id):
    try:
        # checkout buggy bug
        buggy_bug = checkout_bug(
            benchmark, working_directory, project, bug_id, 'buggy')

        complied_output = buggy_bug.compile()
        if complied_output.count('OK') == 2:
            _, buggy_test_output = buggy_bug.run_test()
            defects4j_config.buggy_test_output = buggy_test_output
            return defects4j_config, buggy_bug
        else:
            defects4j_config.buggy_test_output = 'Compile error'
            return defects4j_config, None
    except Exception as e:
        printlog(
            'Something went wrong when checkout buggy version of bug {} {}-------\n'.format(project, bug_id), e)
        return defects4j_config, None


def checkout_fixed_version(defects4j_config, benchmark, working_directory, project, bug_id):
    try:
        # checkout fixed bug
        fixed_bug = checkout_bug(
            benchmark, working_directory, project, bug_id, 'fixed')

        complied_output = fixed_bug.compile()
        if complied_output.count('OK') == 2:
            _, fixed_test_output = fixed_bug.run_test()
            defects4j_config.fixed_test_output = fixed_test_output
            return defects4j_config, fixed_bug
        else:
            defects4j_config.fixed_test_output = 'Compile error'
            return defects4j_config, None
    except Exception as e:
        printlog(
            'Something went wrong when checkout fixed version of bug {} {}-------\n'.format(project, bug_id), e)
        return defects4j_config, None


def load_buggy_fixed_code_nodes(args, defects4j_config, working_directory, countable_diffs, fixed_bug, bug_id):
    # prepare fixed and buggy code ast node
    bug_dir = os.path.join(working_directory, "%s_%s_%s" %
                           (fixed_bug.benchmark, fixed_bug.project, bug_id))
    fixed_bug_path = bug_dir + "_fixed/" + countable_diffs[0].file_path
    buggy_bug_path = bug_dir + "_buggy/" + countable_diffs[0].file_path
    fixed_node, buggy_node = load_code_node(
        fixed_bug_path, buggy_bug_path, countable_diffs)

    defects4j_config.bug_start_pos = buggy_node.start_pos
    defects4j_config.bug_end_pos = buggy_node.end_pos
    
    # buggy_code_chunk and fixed_code_chunk with comments
    defects4j_config.buggy_code_chunk = buggy_node.code_lines_str()
    defects4j_config.fixed_code_chunk = fixed_node.code_lines_str()

    defects4j_config.fixed_code_size = chatgpt_tokenize(
        defects4j_config.fixed_code_chunk, args.model)

    return defects4j_config, fixed_node, buggy_node


def build_prompt(args, defects4j_config, fixed_bug, buggy_node, fixa_config, bug_dir):

    # output_file_path = 'output/{}'.format(bug_dir.split('/')[-1])
    prompt, prompt_size, bug_size = chatgpt_prompt_generation(args, buggy_node, fixa_config['include_document'], fixa_config['include_comments'])
    # write_to_file(output_file_path + '.codex_prompt', prompt) # output_file_path is the bug dir
    defects4j_config.prompt_text = prompt
    defects4j_config.prompt_size = prompt_size
    defects4j_config.buggy_code_size = bug_size

    return defects4j_config


def build_request_params(args, defects4j_config, fixa_config):
    temperature = args.temperature
    request_params = {
        'model': args.model,
        'temperature': temperature,
        'max_tokens': args.max_tokens,
        'top_p': args.top_p,
        'frequency_penalty': args.frequency_penalty,
        'presence_penalty': args.presence_penalty,
    }
    defects4j_config.request_params = request_params
    defects4j_config.prompt_params = fixa_config
    defects4j_config.temperature = request_params['temperature']

    return defects4j_config


def sanitize_choice_text(choice_text):
    cleaned_text = []
    for l in choice_text.split('\n'):
        if l.startswith('#'):
            continue
        if len(l.strip()) == 0:
            continue
        cleaned_text.append(l)
    return '\n'.join(cleaned_text)


# def extract_code(choice_text):
#     code = []
#     cnt = 0
#     for l in choice_text.split('\n'):
#         if l.startswith('```'):
#             if cnt == 0:
#                 cnt += 1
#                 continue
#             else:
#                 break
#         code.append(l)
#     return '\n'.join(code)


def ask_chatgpt(args, defects4j_config, fixa_config):
    # Only support Codex with Defects4J for now
    if args.benchmark != 'Defects4J':
        printlog('Only support Defects4J now')
        exit(1)

    benchmark = get_benchmark(args.benchmark)

    # Run fixed version to get the test output
    defects4j_config, fixed_bug = checkout_fixed_version(
        defects4j_config, benchmark, args.working_directory, args.project, args.bug_id)
    if fixed_bug is None:
        return defects4j_config

    # Run buggy version to get the test output
    defects4j_config, buggy_bug = checkout_buggy_version(
        defects4j_config, benchmark, args.working_directory, args.project, args.bug_id)

    if buggy_bug is None:
        return defects4j_config
    
    target_path = args.working_directory + '/' + args.benchmark + '/' + args.project + '/' + str(args.bug_id)

    try:
        # read patch file
        patch_file_path = DEFS4J_HOME + '/framework' + '/projects/{}/patches/{}.src.patch'.format(
            args.project, args.bug_id)
        countable_diffs, patch_text = read_patch_file(patch_file_path)      
        defects4j_config.patch = patch_text

        if not os.path.exists(target_path):
            os.makedirs(target_path)

        if len(countable_diffs) > 1:
            defects4j_config.respond_type = 'UNRESPONDED'
            defects4j_config.error_message = str(
                "Skip, more than one file changed")
            response = "Skip, more than one file changed."
            printlog(response)
            output_file_path = os.path.join(target_path, "response.txt")
            with open(output_file_path, 'w') as f:
                f.write(response)
            return defects4j_config

        defects4j_config.buggy_file_path = countable_diffs[0].file_path

        # location of checkout bug dir
        bug_dir = os.path.join(args.working_directory, "%s_%s_%s" %
                               (fixed_bug.benchmark, fixed_bug.project, args.bug_id))
        # prepare fixed and buggy code ast node
        # run original fixed version unit tests
        # run buggy code against fixed unit tests, then revert the source to the fixed code
        defects4j_config, fixed_node, buggy_node = load_buggy_fixed_code_nodes(
            args, defects4j_config, args.working_directory, countable_diffs, fixed_bug, args.bug_id)

        # build prompt
        defects4j_config = build_prompt(
            args, defects4j_config, fixed_bug, buggy_node, fixa_config, bug_dir)

        # Prepare request params
        defects4j_config = build_request_params(
            args, defects4j_config, fixa_config)

        # send requests to Codex
        sample_number = 0
        curr_request_counter = 0
        openai_error_counter = 0

        max_openai_error_counter = int(
            config.get('MAX_OPENAI_ERROR_COUNTER') or 2)

        if args.num_requests > 10:
            printlog('request_counter is too large, will reset to 10')
            args.num_requests = 10
        while curr_request_counter < args.num_requests and openai_error_counter < max_openai_error_counter:
            current_time = int(time.time())
            if defects4j_config.prompt_size > args.max_tokens:
                response = "Prompt size is too large, will skip"
                printlog(response)
                output_file_name = "response.txt"
                output_file_path = os.path.join(target_path, output_file_name)
                with open(output_file_path, 'w') as f:
                    f.write(response)
                defects4j_config.respond_type = 'UNRESPONDED'
                return defects4j_config
            try:
                response = request_chatgpt_pr(
                    defects4j_config.prompt_text, defects4j_config.request_params, args)
                curr_request_counter += 1
                current_time = int(time.time())
                openai_error_counter = 0  # reset the error counter
            except Exception as e:
                if 'Rate limit reached for' in str(e):
                    # for defect4j, we may not face this error becasue we are far away from the limit
                    printlog('Rate limit reached for this bug, will skip', str(e))
                    time.sleep(60)
                elif 'Error communicating with OpenAI' in str(e):
                    # sometimes OpenAI will return error, we will retry
                    printlog('OpenAI server error, will retry', str(e))
                    time.sleep(60)
                else:
                    printlog('Something went wrong when performing requesting', str(e))
                    time.sleep(60)
                openai_error_counter += 1
                if openai_error_counter >= max_openai_error_counter:
                    raise e
                continue

            fixed_code = response['choices'][0]['message']['content']
            defects4j_config.respond_original_text[str(curr_request_counter)] = fixed_code
            fixed_code = extract_code(fixed_code)
            defects4j_config.respond_code_chunk[str(curr_request_counter)] = fixed_code

        defects4j_config.respond_type = 'RESPONDED'
        if args.only_request:
            with open(os.path.join(target_path, 'defects4j_config.json'), 'w') as f:
                json.dump(defects4j_config, f, indent=4)
            return
        return defects4j_config
    except Exception as e:
        defects4j_config.respond_type = 'UNRESPONDED'
        defects4j_config.error_message = str(e)
        printlog('Error when processing bug: ', args.bug_id, str(e))
        output_file_path = os.path.join(target_path, "response.txt")
        with open(output_file_path, 'w') as f:
            f.write(str(e))
        return defects4j_config