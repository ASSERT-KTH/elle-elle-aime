import json
from elleelleaime.core.utils.benchmarks import get_benchmark
from elleelleaime.core.utils.jsonl import write_jsonl
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.sample.prompting.strategy import PromptingStrategy
from elleelleaime.core.benchmarks.bug import Bug
from elleelleaime.core.utils.java_tools.java import (
    extract_single_function,
    compute_diff,
    remove_java_comments,
    remove_empty_lines,
)

with open(
    "/home/andre/Repos/mufin-results/mufin/bears/compiler/round1-breaker-training/with_newline/samples_bears_mufin-breaker_2000.jsonl",
    "r",
) as f:
    bugs = [json.loads(x) for x in f.readlines()]

for i, bug in enumerate(bugs):
    fixed_code = remove_empty_lines(remove_java_comments(bug["fixed_code"].strip()))
    emptied_code = remove_empty_lines(
        remove_java_comments(
            bug["prompt"]
            .strip()
            .replace("<fim_prefix>", "")
            .replace("<fim_suffix>", "")
            .replace("<fim_middle>", "")
        )
    )
    diff = compute_diff(fixed_code.strip(), emptied_code.strip())

    prefix = bug["prompt"].split("<fim_suffix>")[0]
    sufix = bug["prompt"].split("<fim_suffix>")[1].split("<fim_middle>")[0]
    removed_code = "// buggy code\n"
    for line in diff:
        if line.startswith("-") and not line.startswith("---"):
            removed_code += "//" + line[1:]
    bug["prompt"] = prefix + "<|mask:0|>\n" + sufix + "<|mask:1|>\n"
    bug["prompt"] = (
        bug["prompt"]
        .replace("<fim_prefix>", "")
        .replace("<fim_suffix>", "")
        .replace("<fim_middle>", "")
    )

with open(
    "/home/andre/Repos/mufin-results/mufin/bears/compiler/round1-breaker-training/with_newline/samples_bears_mufin-breaker-incoder_2000.jsonl",
    "w",
) as f:
    for sample in bugs:
        f.write(json.dumps(sample) + "\n")
