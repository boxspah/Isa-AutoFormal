# Data generation
<!-- pip install SimCSE -->


- Use data_gen for gpt4 generation
```python3
python3 predict.py --dataset <MATH or miniF2F> --root_dir_list <root_dir_list>
```
- notice:
Current data_gen is for minif2f & batch math data, for the preprocess part of origin math , please refer to the comments and [dataset](../dataset/)
- For gpt4 api key ,please see [gpt_utils](./utils/gpt_utils.py)
