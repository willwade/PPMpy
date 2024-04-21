# python language_model_driver.py 30 path_to_train.txt path_to_test.txt

import sys
from vocabulary import Vocabulary
from ppm_language_model import PPMLanguageModel, Context
import math

import matplotlib.pyplot as plt


def train_model(train_file, max_order, debug=False):
    with open(train_file, 'r', encoding='utf-8') as file:
        contents = file.read()

    vocab = Vocabulary()
    for char in set(contents):  
        vocab.add_item(char)

    lm = PPMLanguageModel(vocab, max_order, debug=debug)
    context = Context(lm.root, 0)
    for char in contents:
        symbol_id = vocab.get_id_or_oov(char)  # Ensuring OOV handling
        lm.add_symbol_and_update(context, symbol_id)

    return lm, vocab

def test_model(lm, vocab, test_file):
    with open(test_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    total_log_prob = 0
    num_symbols = 0
    for line in lines:
        if line.strip():
            context = Context(lm.root, 0)
            for char in line.strip():
                symbol = vocab.get_id_or_oov(char)
                probs = lm.get_probs(context)
                prob = probs[symbol] if symbol < len(probs) else 0  # Handling OOV and checking bounds
                if prob > 0:
                    total_log_prob += math.log10(prob)
                    num_symbols += 1
                lm.add_symbol_to_context(context, symbol)

    entropy = -(total_log_prob / num_symbols) / math.log10(2) if num_symbols > 0 else 0
    perplexity = 10 ** (-total_log_prob / num_symbols) if num_symbols > 0 else float('inf')
    print(f"Results: numSymbols = {num_symbols}, ppl = {perplexity}, entropy = {entropy} bits/char")

def predict_next_from_fixed_input(lm, vocab, input_text, num_predictions=3):
    context = lm.create_context()
    try:
        for char in input_text:
            char_id = vocab.get_id_or_oov(char)  
            lm.add_symbol_to_context(context, char_id)
            if lm.debug:
                print(f"Adding '{char}' to context, ID: {char_id}, Current Head ID: {id(context.head)}, Order: {context.order}")
        
        if lm.debug:
            print("Attempting to predict next symbols...")
        top_prediction_ids = lm.predict_next_ids(context, num_predictions)
        # Sample data: probabilities and their corresponding indices
        indices = [index for index, prob in top_prediction_ids]
        probabilities = [prob for index, prob in top_prediction_ids]
        
        plt.figure(figsize=(10, 5))
        plt.bar(indices, probabilities, color='blue')
        plt.xlabel('Token Index')
        plt.ylabel('Probability')
        plt.title('Probability Distribution of Predictions')
        plt.show()
        
        if lm.debug:
            print("Prediction IDs retrieved, processing output...")
        
        predicted_chars = [vocab.get_item_by_id(index) if index != vocab.oov_index else '<OOV>' for index, _ in top_prediction_ids]
        
        if lm.debug:
            print(f"Final Context State before Prediction: Head at {id(context.head)}, Order: {context.order}")
        return predicted_chars
    except Exception as e:
        print(f"Error during context update: {str(e)}")


def tokenize(text):
    return text.split()

def train_model_word_level(train_file, max_order, debug=False):
    with open(train_file, 'r', encoding='utf-8') as file:
        contents = file.read()
    
    words = tokenize(contents)
    vocab = Vocabulary()  
    for word in set(words):
        vocab.add_item(word)

    lm = PPMLanguageModel(vocab, max_order, debug=debug)
    context = Context(lm.root, 0)
    for word in words:
        word_id = vocab.get_id_or_oov(word)  
        lm.add_symbol_and_update(context, word_id)

    return lm, vocab

def predict_next_from_fixed_input_word_level(lm, vocab, input_text, num_predictions=3):
    context = lm.create_context()
    for word in tokenize(input_text):
        word_id = vocab.get_id_or_oov(word) 
        lm.add_symbol_to_context(context, word_id)

    top_predictions = lm.predict_next_ids(context, num_predictions)

    predicted_words = []
    for index, _ in top_predictions:
        if index == vocab.oov_index:
            predicted_words.append('<OOV>')
        else:
            predicted_word = vocab.get_item_by_id(index)  
            predicted_words.append(predicted_word)
    return predicted_words


'''
    So this next chunk is really code to give you a very pretty graph of the trie
    I'm going to comment out the imports. Sometimes installing graphviz isnt fun

'''

#import networkx as nx
#import matplotlib.pyplot as plt

def build_graph_iterative(root, vocab, max_depth=20):
    graph = nx.DiGraph()
    stack = [(root, "Root", "", 0)]  # node, parent ID, symbol, current depth
    
    while stack:
        node, parent_id, symbol, depth = stack.pop()
        
        if depth >= max_depth:
            continue
        
        symbol_label = f"<space>" if symbol == " " else symbol
        node_id = f"{id(node)}_{symbol if symbol else 'Root'}"
        
        graph.add_node(node_id, label=f"{symbol_label}\nCount: {node.count}")
        if parent_id != "Root":
            graph.add_edge(parent_id, node_id)
        
        for child_symbol_id, child in node.children.items():
            child_symbol = vocab.get_symbol_by_id(child_symbol_id)
            stack.append((child, node_id, child_symbol, depth + 1))

    return graph

def draw_graph(graph):
    # Use a default label if 'label' key is not found
    labels = {n: data.get('label', 'No Label') for n, data in graph.nodes(data=True)}

    pos = nx.drawing.nx_agraph.graphviz_layout(graph, prog='dot')
    nx.draw(graph, pos, labels=labels, with_labels=True, node_size=2000, node_color='lightblue')
    plt.show()

import time

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python script.py max_order train_file test_file")
        sys.exit(1)

    max_order, train_file, test_file = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    lm, vocab = train_model(train_file, max_order, debug=True)
    test_model(lm, vocab, test_file)
    fixed_input = "he"
    predicted_chars= predict_next_from_fixed_input(lm, vocab, fixed_input, 5)
    print(f"Top 5 character predictions for '{fixed_input}': {predicted_chars}")
    #lm.print_to_console()
    #g = build_graph_iterative(lm.root, vocab)
    #draw_graph(g)
    
    # Now words
    start_time = time.perf_counter()
    lm, vocab = train_model_word_level(train_file, max_order*4, debug=False)  # Use the word-level training function
    test_model(lm, vocab, test_file)
    fixed_input = "What "
    predicted_words = predict_next_from_fixed_input_word_level(lm, vocab, fixed_input, 5)  # Use the word-level prediction function
    print(f"Top 5 character predictions for '{fixed_input}': {predicted_words}")
    



