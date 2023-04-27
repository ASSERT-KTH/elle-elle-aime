import copy
import paramiko
import uuid
import os
import shutil
import json
import time
from dotenv import dotenv_values
from core.database.engine import count_collected_samples_by_conditions, save
from core.database.schema import Result
from core.tools.java_lang import get_node_by_position, load_ast_nodes, load_origin_code_node
from core.tools.log import printlog
from core.tools.patch import load_patch_file, read_patch_file
from core.tools.persist import write_to_file
from core.tools.prompt import generate_prompt
from core.tools.tokenizer import calculate_request_counter, number_of_tokens
from core.utils import get_benchmark
from typing import List

config = dotenv_values(".env")

CODEX_MODEL = "HF"
EXAMPLE_BUGGY_FILEPATH = 'data/example/codex_prompt_example_buggy.source'
EXAMPLE_FIXED_FILEPATH = 'data/example/codex_prompt_example_fixed.source'
PROJECT_EXAMPLE_BUGGY_PATH_FORMAT = 'data/example/codex_project_example_{}_buggy.source'
PROJECT_EXAMPLE_FIXED_PATH_FORMAT = 'data/example/codex_project_example_{}_fixed.source'

STOP_SIGN = "//"

class ClusterInference:

    def __init__(self):
        self.hostname = config.get("hostname")
        self.username = config.get("username")
        self.password = config.get("password")
        

    def generate(self, prompt, request_params) -> List[str]:
        # Generate unique id
        unique_id = str(uuid.uuid4())

        # Connect to remote cluster using paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.hostname, username=self.username, password=self.password)

        # Create scripts and test data on the remote cluster
        self._create_scripts(ssh, prompt, unique_id, request_params)

        # Submit job to Slurm on the remote cluster and wait for its conclusion
        self._submit_job(ssh, unique_id)

        # Retrieve the results
        results = self._retrieve_results(ssh, unique_id)

        # Close the SSH connection
        ssh.close()

        return results


    def _create_scripts(self, ssh, prompt, unique_id, request_params):
        # Write the test samples file to a file on the remote cluster
        with ssh.open_sftp() as sftp:
            with sftp.open(f"/cephyr/users/andreafo/Alvis/llms/jobs/{unique_id}_inputs.txt", "w+") as f:
                f.write(prompt)

        # Write the HuggingFace script to a file on the remote cluster
        with ssh.open_sftp() as sftp:
            with sftp.open(f"/cephyr/users/andreafo/Alvis/llms/jobs/{unique_id}_inference.py", "w+") as f:
                with open('./resources/scripts/inference.py', 'r') as lf:
                    script = lf.read().format(model="Salesforce/codegen-2B-multi", 
                                              num_return_sequences=request_params["n"],
                                              unique_id=unique_id)
                    f.write(script)

        # Write the jobscript to a file on the remote cluster
        with ssh.open_sftp() as sftp:
            with sftp.open(f'/cephyr/users/andreafo/Alvis/llms/jobs/{unique_id}_jobscript', 'w+') as f:
                with open('./resources/scripts/jobscript', 'r') as lf:
                    script = lf.read().format(job_name="llm-repair-them-all",
                                              gpu_type="A100fat",
                                              gpu_number="1",
                                              job_time="00:10:00",
                                              script=f"/cephyr/users/andreafo/Alvis/llms/jobs/{unique_id}_inference.py")
                    f.write(script)


    def _submit_job(self, ssh, unique_id):
        # Submit job to Slurm
        command = f'cd llms && source setup_env.sh && cd jobs && sbatch --wait {unique_id}_jobscript && wait'
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()
        stderr.channel.recv_exit_status()
        print(stdout.readlines())
        print(stderr.readlines())


    def _retrieve_results(self, ssh, unique_id):
        with ssh.open_sftp() as sftp:
            sftp.get(f'/cephyr/users/andreafo/Alvis/llms/jobs/{unique_id}_predictions.txt', f'{unique_id}_predictions.txt')

        # Read the output file and return the results as a string
        with open(f'{unique_id}_predictions.txt', 'r') as f:
            results = json.loads(f.read())

        return results


def load_code_node(fixed_file_path, buggy_file_path, countable_diffs):
    fixed_node, i = load_origin_code_node(
        fixed_file_path, countable_diffs[0].sorted_changes())
    buggy_nodes = load_ast_nodes(buggy_file_path)
    buggy_node = get_node_by_position(buggy_nodes, fixed_node, i)
    return fixed_node, buggy_node


def request_codex_code_complition(prompt, request_params):
    cluster = ClusterInference()
    response = cluster.generate(prompt, request_params)
    return response


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


def checkout_buggy_version(result_template, benchmark, working_directory, project, bug_id):
    try:
        # checkout buggy bug
        buggy_bug = checkout_bug(
            benchmark, working_directory, project, bug_id, 'buggy')

        complied_output = buggy_bug.compile()
        if complied_output.count('OK') == 2:
            _, buggy_test_output = buggy_bug.run_test()
            result_template.buggy_test_output = buggy_test_output
            return result_template, buggy_bug
        else:
            result_template.buggy_test_output = 'Compile error'
            return result_template, None
    except Exception as e:
        printlog(
            'Something went wrong when checkout buggy version of bug {} {}-------\n'.format(project, bug_id), e)
        return result_template, None


def checkout_fixed_version(result_template, benchmark, working_directory, project, bug_id):
    try:
        # checkout fixed bug
        fixed_bug = checkout_bug(
            benchmark, working_directory, project, bug_id, 'fixed')

        complied_output = fixed_bug.compile()
        if complied_output.count('OK') == 2:
            _, fixed_test_output = fixed_bug.run_test()
            result_template.fixed_test_output = fixed_test_output
            return result_template, fixed_bug
        else:
            result_template.fixed_test_output = 'Compile error'
            return result_template, None
    except Exception as e:
        printlog(
            'Something went wrong when checkout fixed version of bug {} {}-------\n'.format(project, bug_id), e)
        return result_template, None


def build_result_template(args, bug_id):
    result_template = Result()
    result_template.model = args.model
    result_template.benchmark = args.benchmark
    result_template.project = args.project
    result_template.bug_id = bug_id
    result_template.request_type = 'SINGLE_FUNCTION'
    result_template.sample_number = 0
    return result_template


def load_buggy_fixed_code_nodes(result_template, working_directory, countable_diffs, fixed_bug, bug_id):
    # prepare fixed and buggy code ast node
    bug_dir = os.path.join(working_directory, "%s_%s_%s" %
                           (fixed_bug.benchmark, fixed_bug.project, bug_id))
    fixed_bug_path = bug_dir + "_fixed/" + countable_diffs[0].file_path
    buggy_bug_path = bug_dir + "_buggy/" + countable_diffs[0].file_path
    fixed_node, buggy_node = load_code_node(
        fixed_bug_path, buggy_bug_path, countable_diffs)

    result_template.bug_start_pos = buggy_node.start_pos
    result_template.bug_end_pos = buggy_node.end_pos

    result_template.buggy_code_chunk = buggy_node.code_lines_str()
    result_template.buggy_code_token = number_of_tokens(
        result_template.buggy_code_chunk)
    result_template.fixed_code_chunk = fixed_node.code_lines_str()
    result_template.fixed_code_token = number_of_tokens(
        result_template.fixed_code_chunk)

    # run original fixed version unit tests
    # must checkout the fixed bug again
    # fixed_bug = checkout_bug(
    #     fixed_bug.benchmark, working_directory, fixed_bug.project, bug_id, 'fixed')
    # template_fixed_complied_output = fixed_bug.compile()
    # if template_fixed_complied_output.count('OK') == 2:
    #     _, fixed_test_output = fixed_bug.run_test()
    #     result_template.fixed_test_output = fixed_test_output
    #     printlog('fixed_test_output: \n', fixed_test_output)
    # else:
    #     result_template.fixed_test_output = 'Compile error'

    # run buggy code against fixed unit tests, then revert the source to the fixed code
    # applied, error, original_func_lines = apply_text_to_fixed_version(
    #     fixed_bug_path, buggy_node.code_lines_str(), fixed_node)
    # if applied:
    #     template_buggy_complied_output = fixed_bug.compile()
    #     if template_buggy_complied_output.count('OK') == 2:
    #         _, buggy_test_output = fixed_bug.run_test()
    #         result_template.buggy_test_output = buggy_test_output
    #         printlog('buggy_test_output: \n', buggy_test_output)
    #     else:
    #         result_template.buggy_test_output = 'Compile error'
    #     revert_response_to_fixed_version(
    #         original_func_lines, working_directory, fixed_bug, patch_file_path)

    return result_template, fixed_node, buggy_node


def build_prompt(result_template, fixed_bug, buggy_node, fixa_config, bug_dir):
    # build prompt
    project_buggy_path = PROJECT_EXAMPLE_BUGGY_PATH_FORMAT.format(
        fixed_bug.project)
    project_fixed_path = PROJECT_EXAMPLE_FIXED_PATH_FORMAT.format(
        fixed_bug.project)
    smallest_bug_example_id = int(fixed_bug._get_project_data()['smallestBug'])
    include_project_specific_example = smallest_bug_example_id != 0 and smallest_bug_example_id != int(
        fixed_bug.bug_id)
    output_file_path = 'output/{}'.format(bug_dir.split('/')[-1])
    prompt, prompt_size, bug_size = generate_prompt(STOP_SIGN, EXAMPLE_BUGGY_FILEPATH, EXAMPLE_FIXED_FILEPATH,
                                                    project_buggy_path, project_fixed_path, buggy_node, fixa_config['include_document'], fixa_config['include_comments'], include_project_specific_example)
    write_to_file(output_file_path + '.codex_prompt', prompt)
    result_template.prompt_text = prompt
    result_template.prompt_size = prompt_size
    result_template.buggy_code_token = bug_size

    return result_template


def build_request_params(result_template, fixa_config):
    temperature = float(config.get('CODEX_TEMPERATURE') or 0.8)
    # finished_sample_counter = count_collected_samples_by_conditions(
    #     result_template.project, result_template.bug_id, temperature)
    real_sample_counter = fixa_config['sample']
    # max(
    #      - finished_sample_counter, 0)
    # printlog('Project {} bug {} finished_sample_counter: {}, need to request {} more'.format(
    #     result_template.project, result_template.bug_id, finished_sample_counter, real_sample_counter))
    request_counter, n_value, max_completion_size = calculate_request_counter(
        real_sample_counter, fixa_config['completion_ratio'], result_template.prompt_size, result_template.buggy_code_token)
    printlog('request_counter: ', request_counter)
    printlog('n_value: ', n_value)
    printlog('max_completion_size: ', max_completion_size)
    request_params = {
        'model': CODEX_MODEL,
        'temperature': temperature,
        'max_tokens': max_completion_size,
        'top_p': 0.95,
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0,
        'stop': [STOP_SIGN],
        'n': n_value,
    }
    result_template.request_params = request_params
    result_template.prompt_params = fixa_config
    result_template.temperature = request_params['temperature']

    return result_template, request_counter


def sanitize_choice_text(choice_text):
    cleaned_text = []
    for l in choice_text.split('\n'):
        if l.startswith('#'):
            continue
        if len(l.strip()) == 0:
            continue
        cleaned_text.append(l)
    return '\n'.join(cleaned_text)


def ask_hf_for_single_bug(args, bug_id, fixa_config):
    benchmark = get_benchmark(args.benchmark)

    # build a result template that will be used to save the result
    result_template = build_result_template(args, bug_id)

    # Run fixed version to get the test output
    result_template, fixed_bug = checkout_fixed_version(
        result_template, benchmark, args.working_directory, args.project, bug_id)
    if fixed_bug is None:
        return

    # Run buggy version to get the test output
    result_template, buggy_bug = checkout_buggy_version(
        result_template, benchmark, args.working_directory, args.project, bug_id)
    if buggy_bug is None:
        return

    # read patch file
    patch_file_path = 'benchmarks/defects4j/framework/projects/{}/patches/{}.src.patch'.format(
        args.project, bug_id)
    countable_diffs, patch_text = read_patch_file(patch_file_path)
    result_template.patch = patch_text
    if len(countable_diffs) > 1:
        result_template.result_type = 'ERROR'
        result_template.error_message = str(
            "Skip, more than one file changed")
        save(result_template)
        return

    result_template.buggy_file_path = countable_diffs[0].file_path

    # location of checkout bug dir
    bug_dir = os.path.join(args.working_directory, "%s_%s_%s" %
                            (fixed_bug.benchmark, fixed_bug.project, bug_id))

    # prepare fixed and buggy code ast node
    # run original fixed version unit tests
    # run buggy code against fixed unit tests, then revert the source to the fixed code
    result_template, fixed_node, buggy_node = load_buggy_fixed_code_nodes(
        result_template, args.working_directory, countable_diffs, fixed_bug, bug_id)

    # build prompt
    result_template = build_prompt(
        result_template, fixed_bug, buggy_node, fixa_config, bug_dir)

    # calculate number of requests
    result_template, request_counter = build_request_params(
        result_template, fixa_config)

    # send request to model
    response = request_codex_code_complition(result_template.prompt_text, result_template.request_params)

    for text in response:
        sample_result = copy.deepcopy(result_template) 
        sample_result.result_type = "SUCCESS"
        response_text = sanitize_choice_text(text)
        sample_result.respond_origin_code_chunk = text
        sample_result.respond_clean_code_chunk = text
        save(sample_result)
        time.sleep(1)  # prevent postgres error