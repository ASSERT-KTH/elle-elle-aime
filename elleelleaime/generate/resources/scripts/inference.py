import json
from typing import Optional
from dataclasses import dataclass
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


@dataclass
class GenerateSettings:
    name: str
    num_beams: Optional[int] = 1
    do_sample: Optional[bool] = False
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    temperature: Optional[float] = None
    num_return_sequences: int = {num_return_sequences}


beam_search = GenerateSettings(
    name="beam_search",
    num_beams=10,
)
top_pk_sampling = GenerateSettings(
    name="top_pk_sampling",
    do_sample=True,
    top_k=0,
    top_p=1.0,
    temperature=1.0,
)


def main():
    # Setup environment
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # cache_dir = "/mimer/NOBACKUP/groups/snic2021-7-150/llms"

    # Load the model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained("{model}")
    model = AutoModelForCausalLM.from_pretrained("{model}").to(device)
    # Read the buggy code file
    td_file = open("inputs.txt")
    prompt = td_file.read()
    td_file.close()

    # Tokenize the input
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    eos_id = tokenizer.convert_tokens_to_ids(tokenizer.eos_token)

    # Generate the outputs
    generate_setting = top_pk_sampling
    predicted_texts = []

    while len(predicted_texts) < generate_setting.num_return_sequences:
        output_ids = model.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens={max_new_tokens},
            pad_token_id=eos_id,
            eos_token_id=eos_id,
            num_beams=generate_setting.num_beams,
            do_sample=generate_setting.do_sample,
            top_k=generate_setting.top_k,
            top_p=generate_setting.top_p,
            temperature=generate_setting.temperature,
            num_return_sequences=min(
                10, generate_setting.num_return_sequences - len(predicted_texts)
            ),
        )

        decoded_outputs = tokenizer.batch_decode(
            output_ids[:, inputs.input_ids.shape[1] :],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        predicted_texts += list(text.split("//", 1)[0] for text in decoded_outputs)

    pd_file = open("predictions.txt", "w+")
    json.dump(predicted_texts, pd_file)
    pd_file.close()


if __name__ == "__main__":
    main()
