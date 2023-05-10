import os
from core.tools.test_argument import tuple_of_possible_birthdays


def load_test_cases(test_cases_dir):
    """Load all test cases from the txt file in the test_cases_dir directory."""
    input_files = sorted([file for file in os.listdir(test_cases_dir) if file.startswith("input")], key=lambda x: int(x.split(".")[0].split("_")[1]))
    # read all input files and store them in a list
    test_cases = []
    for file in input_files:
        with open(os.path.join(test_cases_dir, file), "r") as f:
            test_cases.append(f.read())

    output_files = sorted([file for file in os.listdir(test_cases_dir) if file.startswith("output")], key=lambda x: int(x.split(".")[0].split("_")[1]))
    # read all output files and store them in a list
    test_cases_results = []
    for file in output_files:
        with open(os.path.join(test_cases_dir, file), "r") as f:
            test_cases_results.append(f.read().replace("\n", ""))
    return test_cases, test_cases_results


def verify_chatgpt_refactory(test_cases_dir, results_dict):
    """Verify the chatgpt model with the test cases."""
    test_cases, test_cases_results = load_test_cases(test_cases_dir)
    # verify the chatgpt model with the test cases
    for idx, patch in enumerate(results_dict.patches):
        try:
            # c = compile(patch, '', 'exec')
            exec(patch, globals(), globals())
        except Exception as e:
            print("Failed to execute the patch!")
            print(f"Error: {e}")
            results_dict.test_results[idx] = "sample_error"
            break
        for i, test_case in enumerate(test_cases):
            result = None
            try:
                # create a null vaule to store the result
                # log = {}
                # exec("temp = " + test_case, locals(), log)
                result = eval(test_case, globals(), globals())
            except Exception as e:
                print("Failed to execute the test case!")
                print(patch)
                print(f"Error: {e}")
                print(i)
                results_dict.test_results[idx] = "sample_error"
                break
            # result = RESULT.copy()
            result_type = type(result)
            test_case_result_type = type(test_cases_results[i])
            if result_type != test_case_result_type:
                try:
                    result = str(result)
                except Exception as e:
                    print("Type error: failed to unify the type of patch output and test case output!")
                    print(f"Error: {e}")
                    results_dict.test_results[idx] = "failed"
                    break
            if result != test_cases_results[i]:
                print(f"Test case {i} failed!")
                print(f"Input: {test_case}")
                print(f"Expected output: {test_cases_results[i]}")
                print(f"Actual output: {result}")
                results_dict.test_results[idx] = "failed"
                # Stop the current for loop
                break
        if results_dict.test_results[idx] == "":
            print("Test passed!")
            results_dict.test_results[idx] = "passed"
                
    return results_dict


# if __name__ == "__main__":
#     with open('src/core/chatgpt/test.py', 'r') as f:
#         print(f.read())
#     with open('src/core/chatgpt/test.py', 'w') as f:
#         f.write('print("hello")')