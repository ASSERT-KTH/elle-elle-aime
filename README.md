# elle-elle-aime ❤️

Framework to use LLMs for automated program repair.

Supported benchmarks: 
  * Defects4J
  * Bugs-dot-jar
  * Refactory
  
## Installation

Requires python3.9 (or latest) and python-poetry
The repository uses many submodules.
```bash
git clone --recurse-submodules https://github.com/ASSERT-KTH/elle-elle-aime.git
cd elle-elle-aime
poetry install # installs dependencies

# for D4J
cd benchmarks/defects4j/
./init.sh
cd ../../
```
## Execution

Be sure to be in the correct environment:
```bash
poetry shell
```

Example of how to generate samples for Defects4J using the zero-shot-cloze strategy for CodeLlama:
```bash
python generate_samples.py defects4j zero-shot-cloze --model_name codellama
```
---

Example of how to generate patches for the samples
```bash
python generate_patches.py samples_defects4j_zero-shot-cloze_model_name_codellama.jsonl.gz codellama-7B --n_workers 1 --generation_strategy beam_search --n_beams 10 --num_return_sequences 10
```
---

Example of how to evaluate the generated patches:
```bash
python evaluate_patches.py defects4j evaluation_defects4j_zero-shot-cloze_codellama-7B.jsonl.gz --correctness
```
The option `--correctness`, enabled by default, will enable compilation and test execution of the generated patches.

---

Example of how to generate statistical reports and export patches:
```bash
python evaluate_patches.py defects4j evaluation_defects4j_zero-shot-cloze_codellama-7B.jsonl.gz --correctness False --statistics --export
```
Note: This command will output the reports and patches to the same directory of the evaluation file



## Development

How to run tests:
```bash
pytest -s tests/
```

## Check out the results

We store all the results (prompts, patches, evaluation) in a separate repository.
Please visit https://github.com/ASSERT-KTH/elle-elle-aime-results for these.
