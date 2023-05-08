from elleelleaime.core.benchmarks.bug import Bug

import tempfile


def generate_sample(bug: Bug, prompt_strategy: str) -> dict[str, Bug|str]:
    """
    Generates the sample for the given bug with the given prompt strategy.
    """
    # TODO: Implement this function for an arbitrary prompt_strategy
    # TODO: For now, we only support one-shot prompts

    with tempfile.TemporaryDirectory() as buggy_dir:
        bug.checkout(buggy_dir)        

    with tempfile.TemporaryDirectory() as fixed_dir:
        bug.checkout(fixed_dir, fixed=True)


    return {
        "identifier": bug.get_identifier(),
        "buggy_code": "buggy_code",
        "fixed_code": "fixed_code",
        "prompt_strategy": prompt_strategy,
        "prompt": "prompt"
    }