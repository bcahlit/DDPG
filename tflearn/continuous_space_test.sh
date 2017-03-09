#!/bin/bash
./bin/HFO --ball-x-min=.75 --ball-x-max=.8 --frames-per-trial=2000 --untouched-time=2000 --offense-agents=1  --defense-npcs=1 --headless --fullstate &
sleep 5
python ../DDPG/tflearn/continuous_space_test_agent.py 6000 &
#python ~/git/DDPG/tflearn/continuous_space_test_agent.py 6000 &

# sleep 5
# python ../DDPG/tflearn/continuous_space_test_agent.py 6000 &

# The magic line
#   $$ holds the PID for this script
#   Negation means kill by process group id instead of PID
trap "kill -TERM -$$" SIGINT
wait
