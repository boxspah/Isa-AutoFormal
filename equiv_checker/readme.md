# The main process of ASSESS

This part is the main part of the experiment. You can conduct the experiment in the following order. More experimental scripts or operations can be found in [More tips](#more-tips)
![Framework](../framework.jpg)

### 1. Environment setup

We recommend using the [Dockerfile](../Dockerfile) for quick builds, but you can also configure the environment locally.
```
docker run -itd -v <repo_dir>:/app <image>
```

Our project uses scala-isabelle to interact with isabelle. Please see [scala-isa-project](../scala-isa-project/readme.md) for more details. If you used a Dockerfile in the previous step, you only need to run ```sbt assembly```

### 2. check syntax
```python3
python3 syntax.py --root_dir_list <root_dir_list>
```
### 3. majority voting

- It is recommended that each process correspond to eight cpus
- naive method is ATP only and symbolic is our method
```python3
python3 majority_voting.py --root_dir_list <root_dir_list> --total_node <total_node> --node_num <node_num> --num_process <num_process> --method <naive or symbolic>
```
### 4. calc scores
```python3
python3 score_label.py --root_dir_list <root_dir_list>
```
### 5. predict accuracy & draw alpha curve

```python3
python3 predict.py --dataset <MATH or miniF2F> --root_dir_list <root_dir_list>
```
---
## More tips
1. Some statistic and save human check
```python3
python3 cluster_statistic.py --dataset <MATH or miniF2F> --root_dir_list <root_dir_list>
```

2. Naive predict
- naive pred is ATP only
- naive majority voting is string matching majority voting
```python3
python3 naive_predict.py --dataset <MATH or miniF2F> --root_dir_list <root_dir_list>
```

3. You can change ```cases``` in [test_cases.py](./test_cases.py) and run [run_test.py](./run_test.py) for quick case testing.

4. You can run [single_majority_voting](./single_majority_voting.py) for files in single process mode.

5. For dataset, please refer [dataset](../dataset/)

6. For more data generation details, please see  [data-generation](../data_generation/)

7. For the For manual label websites, please see [website](../website/) or repo [MathData](https://dev.azure.com/ai4m/MathData/_git/MathData)
    - notice: The inter repo data is not synchronized automatically, you may need to manually synchronize some data between repos.
