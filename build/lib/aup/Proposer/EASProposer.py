"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later


aup.Proposer.EASProposer
========================

The code is based on `Efficient Architecture Search by Network Transformation, github commit 6ef7229 <https://github.com/han-cai/EAS>`_.

See `license <https://github.com/han-cai/EAS/blob/master/LICENSE>`_ for redistribution.

Configuration
-------------

General parameters
~~~~~~~~~~~~~~~~~~

============= ============== ========================================
Name          Default value  Explanation
============= ============== ========================================
proposer      eas            Efficient Architecture Search
============= ============== ========================================


The Proposer demonstrates how to integrate Neural Architecture Search based approaches with *Auptimizer*.

For other purpose, users need to modify this file with the following steps.
The ``init`` function is used to initialize the parameters and static values for the algorithm.
The ``get_param`` function uses the ``setup`` function to get different strings representing new NAS architectures based on previous architectures and their performance. A similar paradigm can be adopted for integrating other NAS based algorithms with *Auptimizer*.

"""
import re
import numpy as np

import logging
logger = logging.getLogger(__name__)

try:
    from .AbstractProposer import AbstractProposer
    from .eas.arch_search import arch_search_convnet_net2net
except ImportError as e:
    logger.critical("Error happend during importing. Check 3rd party package dependency")
    print(e)

class EASProposer(AbstractProposer):

    def get_net_str(self, net_configs):
        if isinstance(net_configs, list):
            if len(net_configs) == 1:
                net_config = net_configs[0]
                net_str = []
                for layer in net_config.layer_cascade.layers[:-1]:
                    if isinstance(layer, arch_search_convnet_net2net.ConvLayer):
                        net_str.append('conv-%d-%d' % (layer.filter_num, layer.kernel_size))
                    elif isinstance(layer, arch_search_convnet_net2net.FCLayer):
                        net_str.append('fc-%d' % layer.units)
                    else:
                        net_str.append('pool')
                return ['_'.join(net_str)]
            else:
                net_str_list = []
                for net_config in net_configs:
                    net_str_list += arch_search_convnet_net2net.get_net_str([net_config])
                return net_str_list
        else:
            return arch_search_convnet_net2net.get_net_str([net_configs])[0]

    def get_net_seq(net_configs, vocabulary, num_steps):
        net_str_list = arch_search_convnet_net2net.get_net_str(net_configs)
        net_seq = []
        seq_len = []
        for net_str in net_str_list:
            net_str = re.split('_', net_str)
            net_code = vocabulary.get_code(net_str)
            _len = len(net_code)
            net_code += [vocabulary.pad_code for _ in range(len(net_code), num_steps)]
            net_seq.append(net_code)
            seq_len.append(_len)
        return arch_search_convnet_net2net.np.array(net_seq), arch_search_convnet_net2net.np.array(seq_len)

    def get_block_layer_num(net_configs):
        if len(net_configs) == 1:
            net_config = net_configs[0]
            block_layer_num = []
            _count = 0
            for layer in net_config.layer_cascade.layers[:-1]:
                if isinstance(layer, arch_search_convnet_net2net.PoolLayer):
                    block_layer_num.append(_count)
                    _count = 0
                else:
                    _count += 1
            block_layer_num.append(_count)
            return arch_search_convnet_net2net.np.array([block_layer_num])
        else:
            block_layer_num = []
            for net_config in net_configs:
                block_layer_num.append(arch_search_convnet_net2net.get_block_layer_num([net_config]))
            return arch_search_convnet_net2net.np.concatenate(block_layer_num, axis=0)

    def apply_wider_decision(wider_decision, net_configs, filter_num_list, units_num_list, noise):
        if len(net_configs) == 1:
            decision = wider_decision[0]
            net_config = net_configs[0]
            decision_mask = []
            for _i, layer in enumerate(net_config.layer_cascade.layers[:-1]):
                if isinstance(layer, arch_search_convnet_net2net.ConvLayer):
                    if layer.filter_num >= filter_num_list[-1]:
                        decision_mask.append(0.0)
                    else:
                        decision_mask.append(1.0)
                        if decision[_i]:
                            new_filter_number = layer.filter_num
                            for fn in filter_num_list:
                                if fn > new_filter_number:
                                    new_filter_number = fn
                                    break
                            net_config.widen(
                                layer_idx=_i, new_width=new_filter_number, noise=noise
                            )
                elif isinstance(layer, arch_search_convnet_net2net.FCLayer):
                    if layer.units >= units_num_list[-1]:
                        decision_mask.append(0.0)
                    else:
                        decision_mask.append(1.0)
                        if decision[_i]:
                            new_units_num = layer.units
                            for un in units_num_list:
                                if un > new_units_num:
                                    new_units_num = un
                                    break
                            net_config.widen(
                                layer_idx=_i, new_width=new_units_num, noise=noise,
                            )
                else:
                    decision_mask.append(0.0)
            decision_mask += [0.0] * (len(decision) - len(decision_mask))
            return arch_search_convnet_net2net.np.array([decision_mask])
        else:
            decision_mask = []
            for _i, net_config in enumerate(net_configs):
                decision = wider_decision[_i]
                mask = arch_search_convnet_net2net.apply_wider_decision([decision], [net_config], filter_num_list,
                                                                        units_num_list, noise)
                decision_mask.append(mask)
            return arch_search_convnet_net2net.np.concatenate(decision_mask, axis=0)

    def apply_deeper_decision(deeper_decision, net_configs, kernel_size_list, noise):
        if len(net_configs) == 1:
            decision = deeper_decision[0]
            net_config = net_configs[0]

            block_decision, layer_idx_decision, ks_decision = decision
            decision_mask = [1.0, 1.0]
            block_idx, _pt = 0, 0
            to_set_layers = []
            for _i, layer in enumerate(net_config.layer_cascade.layers[:-1]):
                if _pt == block_decision:
                    real_layer_idx = _i + layer_idx_decision
                    prev_layer = net_config.layer_cascade.layers[real_layer_idx]
                    if isinstance(prev_layer, arch_search_convnet_net2net.ConvLayer):
                        if 'conv' in net_config.drop_scheme['type']:
                            keep_prob = net_config.drop_scheme.get('conv_drop', 1.0)
                        else:
                            keep_prob = 1.0
                        decision_mask.append(1.0)
                        ks = kernel_size_list[ks_decision]
                        new_layer, prev_layer = net_config.deepen(
                            layer_idx=real_layer_idx,
                            new_layer_config={'name': 'conv', 'kernel_size': ks, 'pre_activation': False,
                                              'keep_prob': keep_prob},
                        )
                        to_set_layers.append([new_layer, prev_layer])
                    elif isinstance(prev_layer, arch_search_convnet_net2net.FCLayer):
                        if 'fc' in net_config.drop_scheme['type']:
                            keep_prob = net_config.drop_scheme.get('fc_drop', 1.0)
                        else:
                            keep_prob = 1.0
                        decision_mask.append(0.0)
                        new_layer, prev_layer = net_config.deepen(
                            layer_idx=real_layer_idx,
                            new_layer_config={'name': 'fc', 'keep_prob': keep_prob},
                        )
                        to_set_layers.append([new_layer, prev_layer])
                    else:
                        raise ValueError
                    break
                if isinstance(layer, arch_search_convnet_net2net.PoolLayer):
                    _pt += 1
            return arch_search_convnet_net2net.np.array([decision_mask]), to_set_layers
        else:
            decision_mask = []
            to_set_layers = []
            for _i, net_config in enumerate(net_configs):
                decision = deeper_decision[_i]
                mask, to_set = arch_search_convnet_net2net.apply_deeper_decision([decision], [net_config],
                                                                                 kernel_size_list, noise)
                decision_mask.append(mask)
                to_set_layers.append(to_set)
            return arch_search_convnet_net2net.np.concatenate(decision_mask, axis=0), to_set_layers

    def __init__(self, config):
        super().__init__(config)
        self.start_net_path = '../start_nets/start_net_convnet_small_C10+'
        self.arch_search_folder = '../arch_search/Convnet/C10+/Conv_C10+_rl_small'
        self.net_pool_folder = '../net_pool/Convnet/C10+/Conv_C10+_rl_small'
        self.max_episodes = 3  # changed from 15
        self.random = False
        self.exp_list = []
        self.idx_to_task = {}
        self.episode_batches = 3
        self.nSamples = self.max_episodes * self.episode_batches
        self.finished_tasks = 0
        self.results = {}

        self.filter_num_list = [_i for _i in range(4, 44, 4)]
        self.units_num_list = [_i for _i in range(8, 88, 8)]
        # filter_num_list = [16, 32, 64, 96, 128, 192, 256, 320, 384, 448, 512, 576, 640]
        # units_num_list = [64, 128, 256, 384, 512, 640, 768, 896, 1024, 1152, 1280]
        self.kernel_size_list = [1, 3, 5]

        # encoder config
        self.layer_token_list = ['conv-%d-%d' % (f, k) for f in self.filter_num_list for k in [1, 3, 5]]
        self.layer_token_list += ['fc-%d' % u for u in self.units_num_list] + ['pool']
        self.encoder_config = {
            'num_steps': 50,
            'vocab': arch_search_convnet_net2net.Vocabulary(self.layer_token_list),
            'embedding_dim': 16,
            'rnn_units': 50,
            'rnn_type': 'bi_lstm',
            'rnn_layers': 1,
        }

        # wider actor config
        self.wider_actor_config = {
            'out_dim': 1,
            'num_steps': self.encoder_config['num_steps'],
            'net_type': 'simple',
            'net_config': None,
        }

        # deeper actor config
        self.deeper_actor_config = {
            'decision_num': 3,
            'out_dims': [5, 10, len(self.kernel_size_list)],
            'embedding_dim': self.encoder_config['embedding_dim'],
            'cell_type': 'lstm',
            'rnn_layers': 1,
            'attention_config': None,
        }

        # meta-controller config
        self.entropy_penalty = 1e-5
        self.learning_rate = 2e-3
        self.opt_config = ['adam', {}]

        # net2net noise config
        self.noise_config = {
            'wider': {'type': 'normal', 'ratio': 1e-2},
            'deeper': {'type': 'normal', 'ratio': 1e-3},
        }

        # episode config
        self.episode_config = {
            'batch_size': self.episode_batches,
            'wider_action_num': 4,
            'deeper_action_num': 5,
        }

        # arch search run config
        self.arch_search_run_config = {
            'n_epochs': 20,
            'init_lr': 0.02,
            'validation_size': 5000,
            'other_lr_schedule': {'type': 'cosine'},
            'batch_size': 64,
            'include_extra': False,
        }

        # reward config
        self.reward_config = {
            'func': 'tan',
            'decay': 0.95,
        }

        self.arch_manager = arch_search_convnet_net2net.ArchManager(self.start_net_path, self.arch_search_folder,
                                                                    self.net_pool_folder)
        _, self.run_config, _ = self.arch_manager.get_start_net()
        self.run_config.update(self.arch_search_run_config)

        self.encoder = arch_search_convnet_net2net.EncoderNet(**self.encoder_config)
        self.wider_actor = arch_search_convnet_net2net.WiderActorNet(**self.wider_actor_config)
        self.deeper_actor = arch_search_convnet_net2net.DeeperActorNet(**self.deeper_actor_config)
        self.meta_controller = arch_search_convnet_net2net.ReinforceNet2NetController(
            self.arch_manager.meta_controller_path, self.entropy_penalty,
            self.encoder, self.wider_actor, self.deeper_actor, self.opt_config)
        self.meta_controller.load()

        self.episode = 0

        logger.info("Finishing init")

        self.setup()

    def setup(self):

        logger.info('episode. %d start. current time: %s' % (self.episode,
                                                       arch_search_convnet_net2net.strftime("%a, %d %b %Y %H:%M:%S",
                                                                                            arch_search_convnet_net2net.gmtime())))
        start_time = arch_search_convnet_net2net.time()

        self.nets = [self.arch_manager.get_start_net(copy=True) for _ in range(self.episode_config['batch_size'])]
        self.net_configs = [net_config for net_config, _, _ in self.nets]
        logger.info(self.net_configs)
        # feed_dict for update the controller
        self.wider_decision_trajectory, self.wider_decision_mask = [], []
        self.deeper_decision_trajectory, self.deeper_decision_mask = [], []
        self.deeper_block_layer_num = []
        self.encoder_input_seq, self.encoder_seq_len = [], []
        self.wider_seg_deeper = 0
        if self.random:
            # random search
            self.remain_wider_num = self.episode_config['wider_action_num']
            self.remain_deeper_num = self.episode_config['deeper_action_num']
            while self.remain_wider_num > 0 or self.remain_deeper_num > 0:
                self.rand_idx = arch_search_convnet_net2net.np.random.randint(0,
                                                                              self.remain_wider_num + self.remain_deeper_num)
                if self.rand_idx < self.remain_wider_num:
                    self.wider_decision = arch_search_convnet_net2net.np.random.choice(2, [
                        self.episode_config['batch_size'], self.encoder.num_steps])
                    self.arch_search_convnet_net2net.apply_wider_decision(self.wider_decision, self.net_configs,
                                                                          self.filter_num_list, self.units_num_list,
                                                                          self.noise_config)
                    self.remain_wider_num -= 1
                else:
                    self.block_layer_num = arch_search_convnet_net2net.get_block_layer_num(self.net_configs)
                    self.deeper_decision = arch_search_convnet_net2net.np.zeros(
                        [self.episode_config['batch_size'], self.deeper_actor.decision_num],
                        arch_search_convnet_net2net.np.int)
                    self.deeper_decision[:, 0] = arch_search_convnet_net2net.np.random.choice(
                        self.deeper_actor.out_dims[0], self.deeper_decision[:, 0].shape)
                    for _k, block_decision in enumerate(self.deeper_decision[:, 0]):
                        available_layer_num = self.block_layer_num[_k, block_decision]
                        self.deeper_decision[_k, 1] = arch_search_convnet_net2net.np.random.randint(0,
                                                                                                    available_layer_num)
                        self.deeper_decision[:, 2] = arch_search_convnet_net2net.np.random.choice(
                            self.deeper_actor.out_dims[2], self.deeper_decision[:, 2].shape)

                    _, to_set_layers = arch_search_convnet_net2net.apply_deeper_decision(self.deeper_decision,
                                                                                         self.net_configs,
                                                                                         self.kernel_size_list,
                                                                                         self.noise_config)
                    for _k, net_config in enumerate(self.net_configs):
                        net_config.set_identity4deepen(to_set_layers[_k], self.arch_manager.data_provider,
                                                       batch_size=64, batch_num=1, noise=self.noise_config)
                    self.remain_deeper_num -= 1
        else:
            # on-policy training
            for _j in range(self.episode_config['wider_action_num']):
                self.input_seq, self.seq_len = arch_search_convnet_net2net.get_net_seq(self.net_configs,
                                                                                       self.encoder.vocab,
                                                                                       self.encoder.num_steps)
                self.wider_decision, self.wider_probs = self.meta_controller.sample_wider_decision(self.input_seq,
                                                                                                   self.seq_len)
                # modify net config according to wider_decision
                self.wider_mask = arch_search_convnet_net2net.apply_wider_decision(self.wider_decision,
                                                                                   self.net_configs,
                                                                                   self.filter_num_list,
                                                                                   self.units_num_list,
                                                                                   self.noise_config)

                self.wider_decision_trajectory.append(self.wider_decision)
                self.wider_decision_mask.append(self.wider_mask)
                self.wider_seg_deeper += len(self.net_configs)
                self.encoder_input_seq.append(self.input_seq)
                self.encoder_seq_len.append(self.seq_len)

            self.to_set_layers = [[] for _ in range(self.episode_config['batch_size'])]
            for _j in range(self.episode_config['deeper_action_num']):
                self.input_seq, self.seq_len = arch_search_convnet_net2net.get_net_seq(self.net_configs,
                                                                                       self.encoder.vocab,
                                                                                       self.encoder.num_steps)
                self.block_layer_num = arch_search_convnet_net2net.get_block_layer_num(self.net_configs)
                self.deeper_decision, self.deeper_probs = self.meta_controller.sample_deeper_decision(self.input_seq,
                                                                                                      self.seq_len,
                                                                                                      self.block_layer_num)
                # modify net config according to deeper_decision
                self.deeper_mask, self.to_set = arch_search_convnet_net2net.apply_deeper_decision(self.deeper_decision,
                                                                                                  self.net_configs,
                                                                                                  self.kernel_size_list,
                                                                                                  self.noise_config)
                for _k in range(self.episode_config['batch_size']):
                    self.to_set_layers[_k] += self.to_set[_k]

                self.deeper_decision_trajectory.append(self.deeper_decision)
                self.deeper_decision_mask.append(self.deeper_mask)
                self.deeper_block_layer_num.append(self.block_layer_num)
                self.encoder_input_seq.append(self.input_seq)
                self.encoder_seq_len.append(self.seq_len)

            for _k, self.net_config in enumerate(self.net_configs):
                self.net_config.set_identity4deepen(self.to_set_layers[_k], self.arch_manager.data_provider,
                                                    batch_size=64, batch_num=1, noise=self.noise_config)
            # prepare feed dict
            self.encoder_input_seq = arch_search_convnet_net2net.np.concatenate(self.encoder_input_seq, axis=0)
            self.encoder_seq_len = arch_search_convnet_net2net.np.concatenate(self.encoder_seq_len, axis=0)
            if self.episode_config['wider_action_num'] > 0:
                self.wider_decision_trajectory = arch_search_convnet_net2net.np.concatenate(
                    self.wider_decision_trajectory, axis=0)
                self.wider_decision_mask = arch_search_convnet_net2net.np.concatenate(self.wider_decision_mask, axis=0)
            else:
                self.wider_decision_trajectory = -arch_search_convnet_net2net.np.ones(
                    [1, self.meta_controller.encoder.num_steps])
                self.wider_decision_mask = -arch_search_convnet_net2net.np.ones(
                    [1, self.meta_controller.encoder.num_steps])
            if self.episode_config['deeper_action_num'] > 0:
                self.deeper_decision_trajectory = arch_search_convnet_net2net.np.concatenate(
                    self.deeper_decision_trajectory, axis=0)
                self.deeper_decision_mask = arch_search_convnet_net2net.np.concatenate(self.deeper_decision_mask,
                                                                                       axis=0)
                self.deeper_block_layer_num = arch_search_convnet_net2net.np.concatenate(self.deeper_block_layer_num,
                                                                                         axis=0)
            else:
                self.deeper_decision_trajectory = - arch_search_convnet_net2net.np.ones(
                    [1, self.meta_controller.deeper_actor.decision_num])
                self.deeper_decision_mask = - arch_search_convnet_net2net.np.ones(
                    [1, self.meta_controller.deeper_actor.decision_num])
                self.deeper_block_layer_num = arch_search_convnet_net2net.np.ones(
                    [1, self.meta_controller.deeper_actor.out_dims[0]])

        self.run_configs = [self.run_config] * len(self.net_configs)

        self.net_str_list = self.get_net_str(self.net_configs)

        tasks = self.arch_manager.get_net_tasks(self.net_str_list, self.net_configs, self.run_configs)
        self.idx_to_task = {}
        self.exp_list = []
        for task in tasks:
            self.idx_to_task[task[0]] = task[1][0]
            self.exp_list.append(task[0])

    def get_param(self, **kwargs):

        if (self.finished_tasks != self.episode_batches and len(self.exp_list) == 0):
            return None

        if (self.finished_tasks == self.episode_batches and len(self.exp_list) == 0):

            logger.info("finished episode" + str(self.episode))
            net_val_list = [-1] * len(self.net_str_list)
            logger.info(self.results)
            logger.info(self.idx_to_task)
            for folder in self.idx_to_task.keys():
                net_val_list[self.idx_to_task[folder]] = self.results[folder]
            rewards = self.arch_manager.reward(net_val_list, self.reward_config)
            rewards = np.concatenate([rewards for _ in range(self.episode_config['wider_action_num'] +
                                                             self.episode_config['deeper_action_num'])])
            rewards /= self.episode_config['batch_size']
            # update the agent
            if not self.random:
                self.meta_controller.update_controller(self.learning_rate, self.wider_seg_deeper,
                                                       self.wider_decision_trajectory,
                                                       self.wider_decision_mask, self.deeper_decision_trajectory,
                                                       self.deeper_decision_mask,
                                                       rewards, self.deeper_block_layer_num, self.encoder_input_seq,
                                                       self.encoder_seq_len)

                self.meta_controller.save()
            self.episode += 1

            self.exp_list = []
            self.idx_to_task = {}
            self.finished_tasks = 0
            self.results = {}

            if (self.episode == self.max_episodes):
                raise Exception("Exceeded Max Episodes")
            self.setup()

            logger.info("Starting Episode " + str(self.episode))

        logger.debug("***********************Exp_list*****************")
        logger.debug(self.exp_list)
        logger.debug("***********************Fin_list*****************")
        logger.debug(self.finished_tasks)
        logger.debug("************************************************")
        logger.info("Starting Task")
        task = self.exp_list.pop()

        return {"expdir": task}

    def update(self, score, job):
        # super().update(score, job)
        logger.debug(score)
        logger.debug(job.config)
        logger.debug(job.script)
        logger.debug("************************************************")
        self.finished_tasks += 1
        self.results[job.config["folderpath"]] = score

    def failed(self, job):
        super().failed(job)
        raise NotImplementedError("EASProposer does not support failed jobs")

    def save(self, path):
        msg = "Save and restore not supported yet"
        logger.fatal(msg)
        raise NotImplementedError(msg)

    def reload(self, path):
        msg = "Save and restore not supported yet"
        logger.fatal(msg)
        raise NotImplementedError(msg)
