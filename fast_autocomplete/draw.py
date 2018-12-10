import collections


class DrawGraphMixin:

    DRAW_POPULATION_ANIMATION = False
    DRAW_POPULATION_ANIMATION_PATH = ''
    DRAW_POPULATION_ANIMATION_FILENO_PADDING = 6
    SHOW_OBJ_IDS_OF_WORDS = {}

    def draw_graph(self, file_path):
        """
        Draws the graph of autocomplete words.

        parameters:

        - file_path: the full path to the file to save the graph into.
        Graphviz library will determine the format of the file based on the extension you choose.
        """
        try:
            import pygraphviz as pgv
        except ImportError:
            print('You need to install pygraphviz in order to draw graphs')

        graph = pgv.AGraph(strict=False, directed=True)

        edges = set()
        que = collections.deque()
        que.append(('root', self._dwg, ''))
        node_alternative_names = {}
        while que:
            parent_name, node, edge_name = que.popleft()
            node_id = id(node)
            if node_id not in node_alternative_names:
                node_alternative_names[node_id] = f'.{len(node_alternative_names)}'
            if node.word:
                node_name = node.word
                if node_name in self.SHOW_OBJ_IDS_OF_WORDS:
                    node_name = f'{node_name} {id(node)}'
                graph.add_node(node_name, fontcolor='blue', fontname='Arial', shape='rectangle')
            else:
                node_name = node_alternative_names[node_id]
                graph.add_node(node_name, color='grey', shape='point')
            edge_name = "' '" if edge_name == ' ' else edge_name
            edge = (parent_name, node_name)
            if edge not in edges:
                edges.add(edge)
                graph.add_edge(*edge, color='blue', label=edge_name)
                for edge_name, child in node.children.items():
                    que.append((node_name, child, edge_name))
        graph.draw(file_path, prog='dot')

    def insert_word_callback(self, word):
        """
        Once word is inserted, this call back is run.
        """
        if self.DRAW_POPULATION_ANIMATION:
            if not hasattr(self, '_graph_fileno'):
                self._graph_fileno = 0
                self._graph_filepath = self.DRAW_POPULATION_ANIMATION_PATH.replace('.', r'{}.')

            fileno = str(self._graph_fileno).zfill(self.DRAW_POPULATION_ANIMATION_FILENO_PADDING)
            file_path = self._graph_filepath.format(fileno)
            self.draw_graph(file_path=file_path)
            self._graph_fileno += 1
