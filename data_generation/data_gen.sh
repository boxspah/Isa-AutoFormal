#!/bin/bash

category=""
data=""
exp_name=""
version_name=""
api_id=""
iter=""

usage() { echo "Usage: $0 --category <algebra/...> --data <train/test> --exp_name <EXP_NAME> --version_name <e0> --api_id <1/...> --iter <1/2/...>" 1>&2; exit 1; }

# Check that we have at least one argument:
if [ $# -eq 0 ]; then
    usage
fi

# Parse the command line arguments:
while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        --category)
        category="$2"
        shift
        shift
        ;;
        --data)
        data="$2"
        shift
        shift
        ;;
        --exp_name)
        exp_name="$2"
        shift
        shift
        ;;
        --version_name)
        version_name="$2"
        shift
        shift
        ;;
        --api_id)
        api_id="$2"
        shift
        shift
        ;;
        --iter)
        iter="$2"
        shift
        shift
        ;;
        *)    # unknown option
        usage
        ;;
    esac
done

if [ -z "${category}" ] || [ -z "${data}" ] || [ -z "${version_name}" ] || [ -z "${api_id}" ] || [ -z "${iter}" ]; then
    usage
fi

IFS=',' read -ra category_array <<< "$category"
IFS=',' read -ra api_array <<< "$api_id"

if [ "$category" == "all" ]; then
    category_array=("algebra" "counting_and_probability" "geometry" "intermediate_algebra" "number_theory" "prealgebra" "precalculus")
fi

session_name="gen"

for i in "${!category_array[@]}"; do
    category="${category_array[i]}"
    if [ "$i" -lt "${#api_array[@]}" ]; then
        api="${api_array[i]}"
    else
        api="${api_array[-1]}"
    fi
    ARGS="--category ${category} --data ${data} --exp_name ${exp_name} --version_name ${version_name} --api_id ${api} --iter ${iter}"

    if [ "$i" -eq 0 ]; then
        tmux new-session -d -s "$session_name" "python data_gen.py ${ARGS}"
    else
        tmux split-window -t "$session_name" -v "python data_gen.py ${ARGS}"
    fi
    tmux select-layout -t "$session_name" tiled
done
