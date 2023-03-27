
import json
import os
import subprocess
import javalang
from core.database.engine import find_all_success, find_samples_by_conditions
from core.large_language_models.verify_codex_defects4j import apply_text_to_buggy_version
from core.tools.java_lang import find_exact_match
from core.tools.patch import is_line_contain_statement
from core.utils import get_benchmark

DEFECTS4J_BUG_SIZE = {
    'Chart': 26,
    'Cli': 40,
    'Closure': 176,
    'Codec': 18,
    'Collections': 28,
    'Compress': 47,
    'Csv': 16,
    'Gson': 18,
    'JacksonCore': 26,
    'JacksonDatabind': 112,
    'JacksonXml': 6,
    'Jsoup': 93,
    'JxPath': 22,
    'Lang': 65,
    'Math': 106,
    'Mockito': 38,
    'Time': 27,
}

DEFECTS4J_PROJECTS = ['Chart', 'Cli', 'Closure', 'Codec', 'Collections', 'Compress', 'Csv', 'Gson',
                      'JacksonCore', 'JacksonDatabind', 'JacksonXml', 'Jsoup', 'JxPath', 'Lang', 'Math', 'Mockito', 'Time']


def sanitize_code_chunk(code_chunk):
    lines = []
    for line in code_chunk.split('\n'):
        # is_line_contain_statement
        if len(line.strip()) == 0:
            continue
        if is_line_contain_statement(line):
            lines.append(line.strip())
    return lines


if __name__ == "__main__":
    benchmark = get_benchmark('Defects4J')
    for project in DEFECTS4J_PROJECTS:
        for bug_id in range(1, DEFECTS4J_BUG_SIZE[project] + 1):
            statistics = {'total': 0, 'skipped': 0,
                          'plausible': 0, 'failed': 0, 'exact_match': 0}
            samples = find_samples_by_conditions(
                project, bug_id, 'TEST_SUCCESS', 0)
            total_samples_size = len(samples)
            statistics['total'] = total_samples_size
            if total_samples_size == 0:
                continue
            print('total success sampeles for {}-{}: {}'.format(project,
                  bug_id, total_samples_size))
            bug = benchmark.get_bug('{}_{}'.format(project, bug_id))
            # checkout the bug
            buggy_bug_path = os.path.join('/Users/pengyu/src/kth/repair',
                                          "%s_%s_%s_%s" % (bug.benchmark.name, bug.project, bug.bug_id, 'buggy'))
            bug.checkout(buggy_bug_path, True)
            print('buggy bug path: {}'.format(buggy_bug_path))
            result_dir = '/Users/pengyu/src/kth/llm-repair-them-all-results' + \
                '/{}-{}'.format(project, bug_id)
            mkdir = 'mkdir -p {}'.format(result_dir)
            subprocess.call(mkdir, shell=True)
            with open(result_dir + '/prompt.txt', 'w') as f:
                f.write(samples[0].prompt_text)
            with open(result_dir + '/fixed_code_chunk.txt', 'w') as f:
                f.write(samples[0].fixed_code_chunk)
            with open(result_dir + '/buggy_code_chunk.txt', 'w') as f:
                f.write(samples[0].buggy_code_chunk)
            with open(result_dir + '/reversed-correct.patch', 'w') as f:
                f.write(samples[0].patch)
            print('total samples: {}'.format(len(samples)))
            for i in range(len(samples)):
                print('sample: {}'.format(i + 1))
                sample = samples[i]
                result_type = samples[i].result_type
                if result_type == 'RESPONDED_NULL' or result_type == 'EXCEED_MAX_LENGTH':
                    statistics['skipped'] += 1
                    continue

                with open(result_dir + '/sample_{}_respond_origin_code_chunk.txt'.format(i + 1), 'w') as f:
                    f.write(sample.respond_origin_code_chunk)
                with open(result_dir + '/sample_{}_respond_clean_code_chunk.txt'.format(i + 1), 'w') as f:
                    f.write(sample.respond_clean_code_chunk)

                match_type = 'failed'
                if (samples[i].result_type == 'TEST_SUCCESS'):
                    match_type = 'plausible'
                    statistics['plausible'] += 1
                is_exact_match = find_exact_match(sample)
                is_exact_match = find_exact_match(sample)
                print('try javalang...', is_exact_match)
                is_exact_match = find_exact_match(sample)
                print('try javalang...', is_exact_match)
                if is_exact_match:
                    match_type = 'correct'
                    statistics['exact_match'] += 1
                else:
                    statistics['failed'] += 1

                patch = sample.patch
                buggy_file = buggy_bug_path + "/" + sample.buggy_file_path

                applied, error = apply_text_to_buggy_version(
                    buggy_file, sample)

                patch_path = result_dir + '/{}-{}_sample-{}_{}_{}.patch'.format(
                    project, bug_id, i + 1, sample.result_type, match_type)
                cmd = """
                    cd %s; git diff --ignore-blank-lines --ignore-cr-at-eol --ignore-space-at-eol > %s; git checkout -f .;
                """ % (buggy_bug_path, patch_path)
                subprocess.call(cmd, shell=True)

            statistics['plausible'] -= statistics['exact_match']
            # save statistics
            with open(result_dir + '/{}-{}-result-statistics.txt'.format(project, bug_id), 'w') as f:
                f.write(json.dumps(statistics))

            # create a file to save id of possbile correct patches
            if statistics['exact_match'] == 0 and statistics['plausible'] > 0:
                with open(result_dir + '/{}-{}-possible-correct.txt'.format(project, bug_id), 'w') as f:
                    f.write("sample_id=[]")
