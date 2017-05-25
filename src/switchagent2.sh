#!/bin/bash
./bin/HFO --headless --frames-per-trial=500 --untouched-time=500 --offense-agents 2 --defense-npcs 1 --fullstate --port 5500 --no-logging --seed 121 &
sleep 5
python ../DDPG/src/switchagent2.py 5500 1 122 &
sleep 5
python ../DDPG/src/switchagent2.py 5500 2 123 &
#python ~/git/DDPG/tflearn/continuous_space_test_agent.py 6000 &

# sleep 5
# python ../DDPG/tflearn/continuous_space_test_agent.py 6000 &

# The magic line
#   $$ holds the PID for this script
#   Negation means kill by process group id instead of PID
trap "kill -TERM -$$" SIGINT
wait
