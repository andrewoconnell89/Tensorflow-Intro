import tensorflow as tf
import numpy as np
import pandas as pd

(X_train, y_train), (X_test, y_test) = tf.keras.datasets.mnist.load_data()
X_train = X_train.astype(np.float32).reshape(-1, 28*28) / 255.0
X_test = X_test.astype(np.float32).reshape(-1, 28*28) / 255.0
y_train = y_train.astype(np.int32)
y_test = y_test.astype(np.int32)
X_valid, X_train = X_train[:5000], X_train[5000:]
y_valid, y_train = y_train[:5000], y_train[5000:]

def shuffle_batch(X, y, batch_size):
    rnd_idx = np.random.permutation(len(X))
    n_batches = len(X) // batch_size
    for batch_idx in np.array_split(rnd_idx, n_batches):
        X_batch, y_batch = X[batch_idx], y[batch_idx]
        yield X_batch, y_batch

n_inputs = 28 * 28  # MNIST
n_hidden1 = 300
n_hidden2 = 100
n_hidden3 = 50
n_outputs = 10

learning_rate = 0.001

n_epochs = 20
batch_size = 100

X = tf.placeholder(tf.float32, shape=(None, n_inputs), name="X")
y = tf.placeholder(tf.int32, shape=(None), name="y")

with tf.name_scope("dnn"):
    hidden_layer_1 = tf.layers.dense(X, n_hidden1, activation=tf.nn.relu, name="hidden_layer_1")
    hidden_layer_2 = tf.layers.dense(hidden_layer_1, n_hidden2, activation=tf.nn.relu, name="hidden_layer_2")
    hidden_layer_3 = tf.layers.dense(hidden_layer_2, n_hidden3, activation=tf.nn.relu, name="hidden_layer_3")
    logits = tf.layers.dense(hidden_layer_3, n_outputs, name="outputs")

    tf.summary.histogram('hidden_layer_1', hidden_layer_1)
    tf.summary.histogram('hidden_layer_2', hidden_layer_2)
    tf.summary.histogram('hidden_layer_3', hidden_layer_3)

with tf.name_scope("loss"):
    xentropy = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=y, logits=logits)
    loss = tf.reduce_mean(xentropy, name="loss")

with tf.name_scope("train"):
    optimizer = tf.train.GradientDescentOptimizer(learning_rate)
    training_op = optimizer.minimize(loss)

with tf.name_scope("eval"):
    correct = tf.nn.in_top_k(logits, y, 1)
    accuracy = tf.reduce_mean(tf.cast(correct, tf.float32))
    tf.summary.scalar('accuracy', accuracy)

init = tf.global_variables_initializer()
merged_summaries = tf.summary.merge_all()

saver = tf.train.Saver()

means = X_train.mean(axis=0, keepdims=True)
stds = X_train.std(axis=0, keepdims=True) + 1e-10
X_val_scaled = (X_valid - means) / stds

train_saver = tf.summary.FileWriter('./model/train', tf.get_default_graph())  # async file saving object
test_saver = tf.summary.FileWriter('./model/test')  # async file saving object

with tf.Session() as sess:
    init.run()
    for epoch in range(n_epochs):
        for X_batch, y_batch in shuffle_batch(X_train, y_train, batch_size):
            X_batch_scaled = (X_batch - means) / stds
            summaries, _ = sess.run([merged_summaries, training_op], feed_dict={X: X_batch_scaled, y: y_batch})
        train_saver.add_summary(summaries, epoch)
        _, acc_batch = sess.run([merged_summaries, accuracy], feed_dict={X: X_batch_scaled, y: y_batch})
        train_summaries, acc_valid = sess.run([merged_summaries, accuracy], feed_dict={X: X_val_scaled, y: y_valid})
        test_saver.add_summary(train_summaries, epoch)
        print(epoch, "Batch accuracy:", acc_batch, "Validation accuracy:", acc_valid)

    train_saver.flush()