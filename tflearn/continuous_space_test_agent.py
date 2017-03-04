#!/usr/bin/env python
# encoding: utf-8

# Before running this program, first Start HFO server:
# $> ./bin/HFO --offense-agents 1

import sys, itertools
from hfo import *

import numpy as np
import tensorflow as tf
import tflearn

from replay_buffer import ReplayBuffer
from actor_hfo import ActorNetwork
from critic_hfo import CriticNetwork


# Max training steps
MAX_EPISODES = 50000
# Max episode length
MAX_EP_STEPS = 1000
# Base learning rate for the Actor network
ACTOR_LEARNING_RATE = .01
# Base learning rate for the Critic Network
CRITIC_LEARNING_RATE = .1
# Discount factor
GAMMA = 0.9
# Soft target update param
TAU = 0.001

# Noise for exploration
EPS_GREEDY_INIT = 1.0
EPS_EPISODES_ANNEAL = 100000
# Parameters in format of theta-mu-sigma
# OU_NOISE_PARAMS = [[5.0, 0.0, 3.0], [5.0, 0.0, 3.0], [5.0, 0.0, 3.0],
#                    [5.0, 0.0, 3.0], [5.0, 0.0, 3.0], [5.0, 0.0, 3.0]]

OU_NOISE_PARAMS = [[.1, 0.0, 3.0]] * 6

# Directory for storing tensorboard summary results
SUMMARY_DIR = './results/tf_ddpg'
RANDOM_SEED = 1234
# Size of replay buffer
BUFFER_SIZE = 10000
MINIBATCH_SIZE = 256


# ===========================
#   Tensorflow Summary Ops
# ===========================
def build_summaries():
    episode_reward = tf.Variable(0.)
    tf.summary.scalar("Reward", episode_reward)
    episode_ave_max_q = tf.Variable(0.)
    tf.summary.scalar("Qmax Value", episode_ave_max_q)

    summary_vars = [episode_reward, episode_ave_max_q]
    summary_ops = tf.summary.merge_all()

    return summary_ops, summary_vars


def main(_):
    with tf.Session() as sess:

        # Create the HFO Environment
        hfo = HFOEnvironment()
        # Connect to the server with the specified
        # feature set. See feature sets in hfo.py/hfo.hpp.
        hfo.connectToServer(HIGH_LEVEL_FEATURE_SET,
                            'bin/teams/base/config/formations-dt', 6000,
                            'localhost', 'base_left', False)

        np.random.seed(RANDOM_SEED)
        tf.set_random_seed(RANDOM_SEED)

        state_dim = 13
        action_dim = 10
        low_action_bound = np.array([-100., -180., -180., -180., 0., -180.])
        high_action_bound = np.array([100., 180., 180., 180., 100., 180.])

        actor = ActorNetwork(sess, state_dim, action_dim, low_action_bound, \
            high_action_bound, ACTOR_LEARNING_RATE, TAU, OU_NOISE_PARAMS)

        critic = CriticNetwork(sess, state_dim, action_dim, low_action_bound, high_action_bound, \
            CRITIC_LEARNING_RATE, TAU, actor.get_num_trainable_vars(), MINIBATCH_SIZE)

        # Set up summary Ops
        summary_ops, summary_vars = build_summaries()

        sess.run(tf.global_variables_initializer())
        writer = tf.summary.FileWriter(SUMMARY_DIR, sess.graph)

        # Initialize target network weights
        actor.update_target_network()
        critic.update_target_network()

        # Initialize replay memory
        replay_buffer = ReplayBuffer(BUFFER_SIZE, RANDOM_SEED)

        for i in xrange(MAX_EPISODES):

            ep_reward = 0
            ep_ave_max_q = 0

            status = IN_GAME
            # Grab the state features from the environment
            s1 = hfo.getState()
            old_reward = 0
            # print "********************"
            # print "Episode", i
            # print "********************"

            for j in xrange(MAX_EP_STEPS):


                # # Grab the state features from the environment
                # features = hfo.getState()
                s = s1

                # Added exploration noise
                s_noise = np.reshape(s, (1, state_dim)) #+ np.random.rand(1, 19)
                # print s_noise
                a = actor.predict(s_noise)[0]
                if replay_buffer.size() > MINIBATCH_SIZE:
                    index, a = actor.add_noise(a, max(0.0, EPS_GREEDY_INIT - float(i) / EPS_EPISODES_ANNEAL))
                    # index = np.argmax(a[:4])
                else:
                    # index = np.random.choice(4, 1000, p=a[:4])[0]
                    index = 0
                    a[4] = np.random.uniform(-100, 100)
                    a[5] = np.random.uniform(-180, 180)
                    # print index
                # a += np.random.rand(10)
                # index = np.argmax(a[:4])
                print a
                print index

                if index == 0:
                    action  = (DASH, a[4], a[5])
                elif index == 1:
                    action = (TURN, a[6])
                elif index == 2:
                    action = (TACKLE, a[7])
                else:
                    action = (KICK, a[8], a[9])

                # Make action and step forward in time
                # print action
                hfo.act(*action)
                # print "\n"
                terminal = hfo.step()

                # Get new state s_(t+1)
                s1 = hfo.getState()

                curr_ball_prox = 1 - 2*(np.sqrt((s1[3] - s1[0])**2 + (s1[4]-s1[1])**2) / np.sqrt(20))
                curr_goal_dist = np.sqrt((s1[3] - 1)**2 + (s1[4])**2)
                curr_kickable = s[5]

                print curr_ball_prox
                print curr_goal_dist

                r = 0
                if j != 0:
                    # If game has finished, calculate reward based on whether or not a goal was scored
                    if terminal != IN_GAME:
                        if status == 1:
                            r += 5

                    # Else calculate reward as distance between ball and goal
                    r += curr_ball_prox - old_ball_prox
                    r += 0.6 * -(curr_goal_dist - old_goal_dist)
                    if (not old_kickable) and (curr_kickable):
                        r += 1

                old_ball_prox = curr_ball_prox
                old_goal_dist = curr_goal_dist
                old_kickable = curr_kickable

                # if r == 0:
                #     r = -1
                print "Current Reward", r


                replay_buffer.add(np.reshape(s, (actor.s_dim,)), np.reshape(a, (actor.a_dim,)), r, \
                    terminal, np.reshape(s1, (actor.s_dim,)))

                # Keep adding experience to the memory until
                # there are at least minibatch size samples
                if replay_buffer.size() > MINIBATCH_SIZE:
                    s_batch, a_batch, r_batch, t_batch, s1_batch = \
                        replay_buffer.sample_batch(MINIBATCH_SIZE)

                    print "REPLAY SIZE ", replay_buffer.size()

                    # Calculate targets
                    # print s1_batch
                    # print s1_batch.shape
                    # print s1_batch.dtype
                    # print s1_batch.shape
                    # print actor.predict_target(s1_batch)
                    target_q = critic.predict_target(s1_batch, actor.predict_target(s1_batch))

                    y_i = []
                    for k in xrange(MINIBATCH_SIZE):
                        if t_batch[k] != IN_GAME:
                            y_i.append(r_batch[k])
                        else:
                            y_i.append(r_batch[k] + GAMMA * target_q[k])

                    # Update the critic given the targets
                    # predicted_q_value, _ = critic.train(s_batch, a_batch, np.reshape(y_i, (MINIBATCH_SIZE, 1)))
                    critic.train(s_batch, a_batch, np.reshape(y_i, (MINIBATCH_SIZE, 1)))

                    # ep_ave_max_q += np.amax(predicted_q_value)

                    # Update the actor policy using the sampled gradient
                    a_outs = actor.predict(s_batch)
                    grads = critic.action_gradients(s_batch, a_outs)
                    actor.train(s_batch, grads[0])

                    # Update target networks
                    actor.update_target_network()
                    critic.update_target_network()
                    # break

                ep_reward += r

                if terminal:

                    summary_str = sess.run(summary_ops, feed_dict={
                        summary_vars[0]: ep_reward,
                        summary_vars[1]: ep_ave_max_q / float(j+1)
                    })

                    writer.add_summary(summary_str, i)
                    writer.flush()

                    print '| Reward: %.4i' % float(ep_reward), " | Episode", i, \
                        '| Qmax: %.4f' % (ep_ave_max_q / float(j+1))

                    break
            # print "FINISH"
            # break

if __name__ == '__main__':
    tf.app.run()
