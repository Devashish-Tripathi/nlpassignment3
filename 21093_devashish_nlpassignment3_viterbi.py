# -*- coding: utf-8 -*-
"""21093_Devashish_nlpassignment3_viterbi.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1xM9yudZPMaVAe5HFdPFQ11DDdaiNYjcQ

### Load the data
"""

import numpy as np
import collections

!wget https://raw.githubusercontent.com/debajyotimaz/nlp_assignment/refs/heads/main/Viterbi_assignment/train_data.txt;
!wget https://raw.githubusercontent.com/debajyotimaz/nlp_assignment/refs/heads/main/Viterbi_assignment/test_data.txt;
!wget https://raw.githubusercontent.com/debajyotimaz/nlp_assignment/refs/heads/main/Viterbi_assignment/noisy_test_data.txt;

def load_data(file_path):
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            sentence = []
            for token in line.strip().split():
                word, tag = token.rsplit('/', 1)  # Split word and tag
                sentence.append((word, tag))
            data.append(sentence)
    return data

# Load train and test data from files
train_data_file = '/content/train_data.txt'  # Path to your training data file
test_data_file = '/content/test_data.txt'    # Path to your test data file
noisy_test_data_file = '/content/noisy_test_data.txt'  # Path to your noisy test data file

train_data = load_data(train_data_file)
test_data = load_data(test_data_file)
noisy_test_data = load_data(noisy_test_data_file)

# Print a sample from the training data
print(train_data[0])
# Print a sample from the testing data
print(test_data[0])
# Print a sample from the noisy testing data
print(noisy_test_data[0])

"""### Viterbi implementation

Assume that the current state depends on the previous state only i.e. consider only $p(q_i=a|q_{i-1})$. This gives us the Markov Chain.

We also assume that the outputs depend only on the current state i.e. consider only $p(o_i|q_i)$

The events that we are interested in may be hidden, especially considering POS tags are not given in the test case.

So, we shall use the Hidden Markov Model to talk about these hidden states.

Q-> N states

A-> Transition Probability matrix NxN with elements $a_{11}, a_{12}, ..., a_{1N}, a_{21}, ..., a_{NN}$

P-> Initial State Probability of size N with elements $p_1, ..., p_N$

B-> Emission Probabilities. The probability of observation $o_t \in V$ being generated from the state $q_i$. Can also consider this to be the probability of a tag's association with a word

A: $P(t_i|t_{i-1}) = C(t_{i-1}t_i)/C(t_{i-1})$

B: $P(w_i|t_{i}) = C(w_{i},t_i)/C(t_{i})$


where C is the count function.

So for HMM tagging: Given an input HMM k = (A,B), with the sequence of observations $O = o_1o_2...o_T$, we need to find the most probable sequence of states (tags) $Q = q_1q_2...q_T$ , which comes down to choosing the most probable sequence of tags $t_{1:n}$ for the word sequence $w_{1:n}$ such that using the assumptions, the best tag sequence

$T_{1:n} = argmax_{t_{1:n}}∏ P(w_i|t_i)P(t_i|t_{i-1})$

As such, we will have to 'learn' the transition and emission matrices from the training data, accounting for noise along the way.

Preprocessing the vocabulary data
"""

def preprocess(data):
  clean_data = []
  puncts = ['@', '#', '$', '^', '.', '!', '?', '%', '\'', '\"', ',', '_',
            '-', '&', '=', '+', '{', '}', '[', ']', ':', ';', '<','>', '\\'
            , '/', '~', '`', '|']
  for sentence in data:
    clean_sentence = []
    for word, tag in sentence:
      word = word.lower()
      if len(word) >= 2:
        for punct in puncts: word = word.replace(punct, '')
      if word.isdigit(): word = 'NUMBER'
      if word.isalnum():
        for digit in range(10): word = word.replace(str(digit), '')
      clean_sentence.append((word, tag))
    clean_data.append(clean_sentence)
  return clean_data

train_data = preprocess(train_data)
test_data = preprocess(test_data)

"""Getting the vocabulary and the tags"""

def get_vocab_and_tags(data):
  vocab, tags, pairs = set(), set(), []
  for sent in data:
    for pair in sent:
      vocab.add(pair[0])
      tags.add(pair[1])
      pairs.append(pair)
  return sorted(vocab), sorted(tags), pairs

vocab, tags, pairs = get_vocab_and_tags(train_data)

"""Initialise Counters for tag-tag and word-tag and tags"""

def init_counters(data):
  word_tag_counts = collections.Counter()
  tag_counts = collections.Counter()
  tag_transition_counts = collections.Counter()

  for sentence in data:
    prev_tag = '<s>'
    for pair in sentence:
      word_tag_counts[pair] += 1
      tag_counts[pair[1]] += 1
      tag_transition_counts[(prev_tag, pair[1])] += 1
      prev_tag = pair[1]
    tag_transition_counts[(prev_tag, '</s>')] += 1

  return word_tag_counts, tag_counts, tag_transition_counts

word_tag_counts, tag_counts, tag_transition_counts = init_counters(train_data)

"""  Getting the initial state probabilities"""

def get_init_probs(tags, data):
  n_sents = len(data)
  init_counts = collections.Counter([sentence[0][1] for sentence in data])
  return {tag: init_counts[tag]/n_sents for tag in tags}

init_probs = get_init_probs(tags, train_data)

"""Getting the final state probabilities. This increases the score for the algorithm, as now, the final state is clear at '.' most of the time, so the model doesn't assign the last found state as the state for all the tags, leading to erronous results"""

def get_end_probs(tags, data):
  n_sents = len(data)
  end_counts = collections.Counter([sentence[-1][1] for sentence in data])
  return {tag: end_counts[tag]/n_sents for tag in tags}

end_probs = get_end_probs(tags, train_data)

"""Getting the emission probabilities"""

def get_emission(word_tag_counts, tag_counts, tags, vocab, alpha=1e-6):
  vocab_len = len(vocab)
  den = alpha * vocab_len
  B = np.zeros((vocab_len, len(tags)), dtype= np.float32)
  for i, word in enumerate(vocab):
    for j, tag in enumerate(tags):
      B[i][j] = (word_tag_counts[(word, tag)] + alpha)/(tag_counts[tag] + den)
  return B

emission_mat = get_emission(word_tag_counts, tag_counts, tags, vocab, 1e-4)

"""Getting the transition probabilities"""

def get_transition(tag_counts, tag_transition_counts, tags, alpha = 1e-6):
  n_tags = len(tags)
  den = n_tags*alpha
  A = np.zeros((n_tags, n_tags), dtype= np.float32)
  for i, tag1 in enumerate(tags):
    for j, tag2 in enumerate(tags):
      A[i][j] = (tag_transition_counts[(tag1, tag2)] + alpha)/(tag_counts[tag1] + den)
  return A

transition_mat = get_transition(tag_counts, tag_transition_counts, tags)

"""Applying viterbi's algorithm to predict tag sequence"""

def viterbi(tags, init_probs, end_probs, transition_mat, emission_mat, sentence, vocab):
  length, n_tags = len(sentence), len(tags)
  prob = np.zeros((length, n_tags))
  pathx = {}

  word0 = sentence[0][0]
  word0_idx = vocab.index(word0) if word0 in vocab else None
  for tag_idx, tag in enumerate(tags):
    if word0_idx is not None:
      prob[0, tag_idx] = init_probs[tag] * emission_mat[word0_idx, tag_idx]
    else:
      prob[0, tag_idx] = init_probs[tag] * 1e-6  # Small value for OOV
    pathx[tag] = [tag]

  for i in range(1, length):
    wordi = sentence[i][0]
    wordi_idx = vocab.index(wordi) if wordi in vocab else None

    newpathx = {}
    for tag1 in range(n_tags):
      max_prob, best_tag = -1, -1
      for tag2 in range(n_tags):
        trans_prob = transition_mat[tag2, tag1]
        emit_prob = emission_mat[wordi_idx, tag1] if wordi_idx is not None else 1e-6
        new_prob = prob[i-1, tag2] * trans_prob * emit_prob
        if new_prob > max_prob:
          max_prob = new_prob
          best_tag = tag2
      prob[i, tag1] = max_prob

      tag = tags[tag1]
      best_prev_tag = tags[best_tag]
      newpathx[tag] = pathx[best_prev_tag] + [tag]

    pathx = newpathx

  fin = []
  for tag_idx, tag in enumerate(tags):
    fin = prob[length-1, tag_idx] * end_probs[tag]
  bestest_tag = tags[np.argmax(fin)]

  pred_tags = pathx[bestest_tag]
  actual_tags = [tag for _, tag in sentence]
  words = [word for word, _ in sentence]

  return pred_tags, actual_tags, words

# Function to get tag sequence for all the sequences
def word_seq(transition_mat, emission_mat, tags, vocab, pairs, init_probs, data):
  all_preds = []
  for sentence in data:
    pred_tags, actual_tags, words = viterbi(tags, init_probs, end_probs, transition_mat, emission_mat, sentence, vocab)
    # pred_tags, actual_tags, words = viterbi_log(transition_mat, emission_mat, tags, vocab, pairs, init_probs, sentence)
    for i in range(len(words)):
      x, y, z = pred_tags[i], actual_tags[i], words[i]
      tup = (x, y, z)
      all_preds.append(tup)
  return all_preds

# Function for metric evaluation
def eval_acc(all_preds, kind):
  # Order is (predicted_tags, actual_tags, words)
  correct = 0
  total = 0
  for pred in all_preds:
    if pred[0] == pred[1]: correct += 1
    total += 1
  acc = correct/total
  print(f'{kind} Accuracy: {acc*100:.2f}%')

train_preds = word_seq(transition_mat, emission_mat, tags, vocab, pairs, init_probs, train_data)
eval_acc(train_preds, 'Train')

test_preds = word_seq(transition_mat, emission_mat, tags, vocab, pairs, init_probs, test_data)
eval_acc(train_preds, 'Test')

test_preds = word_seq(transition_mat, emission_mat, tags, vocab, pairs, init_probs, noisy_test_data)
eval_acc(test_preds, 'Noisy Test')