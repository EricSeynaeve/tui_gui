#! /bin/bash

result_file=$(mktemp)

./select_menu "${result_file}" '[sub1]' 'l1,text 1,t1|l2,text 2,t2' '[sub2]' 'l22,text22,t22'
echo "Exit code: ${?}"
result=$(cat ${result_file})
echo "Tag of choosen command: '${result}'"

./select_menu "${result_file}" --default_tag=t3 'l1,text 1,t1|\[\e[0;32m\]l2\[\e[0m\],text 2,t2|l3,text 3,t3|l4,text 4,t4|l5,text 5,t5|l6,text 6,t6|l7,text 7,t7|l10,text 10,t10'
echo "Exit code: ${?}"
result=$(cat ${result_file})
echo "Tag of choosen command: '${result}'"

./select_menu "${result_file}" --timeout=3 '[3 sec timeout]' 'l1,text 1,t1|\[\e[0;32m\]l2\[\e[0m\],text 2,t2|l3,text 3,t3|l4,text 4,t4|l5,text 5,t5|l6,text 6,t6|l7,text 7,t7|l10,text 10,t10'
echo "Exit code: ${?}"
result=$(cat ${result_file})
echo "Tag of choosen command: '${result}'"

./select_menu "${result_file}" --timeout=3 --default_tag=t3 '[3 sec timeout + default]' 'l1,text 1,t1|\[\e[0;32m\]l2\[\e[0m\],text 2,t2|l3,text 3,t3|l4,text 4,t4|l5,text 5,t5|l6,text 6,t6|l7,text 7,t7|l10,text 10,t10'
echo "Exit code: ${?}"
result=$(cat ${result_file})
echo "Tag of choosen command: '${result}'"

rm -rf "${result_file}"
