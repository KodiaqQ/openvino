"""
 Copyright (c) 2017-2018 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import networkx as nx

from mo.front.common.replacement import FrontReplacementSubgraph
from mo.front.mxnet.extractors.utils import get_json_layer_attrs
from mo.graph.graph import erase_node


class SsdPatternRemoveReshape(FrontReplacementSubgraph):
    enabled = True

    def pattern(self):
        return dict(
            nodes=[
                ('multi_box_prior', dict(op='_contrib_MultiBoxPrior')),
                ('concat', dict(op='Concat')),
                ('reshape', dict(op='Reshape'))
            ],
            edges=[
                ('multi_box_prior', 'concat', {'in': 0}),
                ('concat', 'reshape', {'in': 0})
            ]
        )

    def replace_sub_graph(self, graph: nx.MultiDiGraph, match: dict):
        """
        Need to find each occurrence of pattern: _contrib_MultiBoxPrior(s) -> Concat -> Reshape
        remove Reshape layer - IE does not expect outputs from concatenation of _contrib_MultiBoxPrior to be reshaped

        Parameters
        ----------
        graph : nx.MultiDiGraph
           Graph with loaded model.
         match : dict
           Patterns which were found in graph structure.
        """
        erase_node(match['reshape'])

        # concat should be performed for the third axis
        concat_node = match['concat']
        attr = get_json_layer_attrs(concat_node.graph.node[concat_node.id]['symbol_dict'])
        if 'dim' in attr:
            attr['dim'] = 2
            concat_node['axis'] = 2
