import os
SEED = 42
os.environ['PYTHONHASHSEED'] = str(SEED)
os.environ['CUDA_DEVICE_ORDER'] = "PCI_BUS_ID"
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import random
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import cv2
from keras import layers
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras import Model, Input, activations
from sklearn.model_selection import train_test_split
from keras.optimizers import Adam
from keras.utils import to_categorical
from sklearn.metrics import classification_report

# Set up

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

# Visualization function
def show_sns_image(X, Encoded, Recons,  n = 5, height = 28, width = 28, title =''):
    plt.figure(figsize=(10,5))
    for i in range(n):
        j = np.random.randint(0, len(X))
        print(j)
        ax = plt.subplot(3, n, i + 1)
        plt.imshow(X[j])
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)

        ax = plt.subplot(3, n, i + 6)
        plt.imshow(Encoded[j].reshape((height, width)))
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)

        ax = plt.subplot(3, n, i + 11)
        plt.imshow(Recons[j])
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        #print("Error for image", i, "is", np.sum((X[j] - Recons[j]) ** 2))
    plt.suptitle(title, fontsize = 20)

# model path name
autoencoder_path = 'NonIdeal_Models/2/train_22PMU_MissingOneData_10dB_autoencoder_group4_1.hdf5'
model_path = 'NonIdeal_Models/2/train_22PMU_MissingOneData_10dB_fullmodel_group4_1.hdf5'


DATA_DIR_TRAIN = os.getcwd() + "/Validation/AE_Train&Test/CNN_22PMU_MissingOneData_add10dB/Train/"
DATA_DIR_TEST = os.getcwd() + "/Validation/AE_Train&Test/CNN_22PMU_MissingOneData_add10dB/Test/"
DATA_DIR_VAL = os.getcwd() + "/Validation/AE_Train&Test/CNN_22PMU_MissingOneData_add10dB/Val/"

RESIZE_TO = 96

#-------------------- Training Data --------------------
x_train, y_train = [], []

for file in os.listdir(DATA_DIR_TRAIN):
    print(file)
    for image in os.listdir(DATA_DIR_TRAIN + '/' + file + '/'):
        x_train.append(cv2.resize(cv2.imread(DATA_DIR_TRAIN + '/' + file + '/' + image, cv2.IMREAD_UNCHANGED), (RESIZE_TO, RESIZE_TO)))
        y_train.append(int(file))

x_train, y_train = np.array(x_train), np.array(y_train)
print(x_train.shape, y_train.shape)

# Counting how many targets for each class in training data
classes, counts = np.unique(y_train, return_counts=True, axis=0)
classes = classes.tolist()  # Converting to list
counts = counts.tolist()  # Converting to list
print(classes, counts)

#-------------------- Testing Data --------------------
x_test, y_test = [], []

for file in os.listdir(DATA_DIR_TEST):
    print(file)
    for image in os.listdir(DATA_DIR_TEST + '/' + file + '/'):
        x_test.append(cv2.resize(cv2.imread(DATA_DIR_TEST + '/' + file + '/' + image, cv2.IMREAD_UNCHANGED), (RESIZE_TO, RESIZE_TO)))
        y_test.append(int(file))

x_test, y_test = np.array(x_test), np.array(y_test)
print(x_test.shape, y_test.shape)

# Counting how many targets for each class in testing data
classes, counts = np.unique(y_test, return_counts=True, axis=0)
classes = classes.tolist()  # Converting to list
counts = counts.tolist()  # Converting to list
print(classes, counts)

#-------------------- Validation Data --------------------
x_val, y_val = [], []

for file in os.listdir(DATA_DIR_VAL):
    print(file)
    for image in os.listdir(DATA_DIR_VAL + '/' + file + '/'):
        x_val.append(cv2.resize(cv2.imread(DATA_DIR_VAL + '/' + file + '/' + image, cv2.IMREAD_UNCHANGED), (RESIZE_TO, RESIZE_TO)))
        y_val.append(int(file))

x_val, y_val = np.array(x_val), np.array(y_val)
print(x_val.shape, y_val.shape)

# Counting how many targets for each class in testing data
classes, counts = np.unique(y_val, return_counts=True, axis=0)
classes = classes.tolist()  # Converting to list
counts = counts.tolist()  # Converting to list
print(classes, counts)

# Normalizing the images
x_train, x_test, x_val = x_train / 255, x_test / 255, x_val / 255


#-------------------- Building autoencoder model --------------------
# Hyper parameters
N_EPOCHS = 30
Batch_size = 512
LR = 0.001 # decreased the learning rate from the ideal model (from 0.01 to 0.001)
DROPOUT = 0.5

########################################################################################################################
# building the model
input_image = Input(shape=(96, 96, 4))

### Downsampling ---- Encoder
print('-- Encoding --')
z = layers.Conv2D(16, (3,3), padding='same', activation='relu')(input_image) # shape 96 x 96
z = layers.BatchNormalization()(z)
print(z.shape)
z = layers.MaxPool2D((2,2))(z) # shape 48 x 48
print(z.shape)

z = layers.Conv2D(32, (3,3), padding='same')(z) # shape 48 x 48
z = layers.BatchNormalization()(z)
print(z.shape)
z = layers.MaxPool2D((2,2))(z) # shape 24 x 24
print(z.shape)
z = activations.relu(z)

z = layers.Conv2D(64, (3,3), padding='same', activation='relu')(z) # 24 x 24
z = layers.BatchNormalization()(z)
print(z.shape)
encoder = layers.MaxPool2D((2,2))(z) # shape 12 x 12
print(encoder.shape)

### Upsampling ---- Decoder
print('-- Decoding')
z = layers.Conv2D(64, (3, 3), padding ='same', activation='relu')(encoder) # shape 12 x 12
z = layers.BatchNormalization()(z)
print(z.shape)
z = layers.UpSampling2D((2,2))(z) # shape 24 x 24
print(z.shape)

z = layers.Conv2D(32, (3, 3), padding ='same')(z) # shape 24 x 24
z = layers.BatchNormalization()(z)
print(z.shape)
z = layers.UpSampling2D((2,2))(z) # shape 48 x 48
print(z.shape)
z = activations.relu(z)

z = layers.Conv2D(16, (3, 3), padding ='same', activation='relu')(z) # shape 96 x 96
z = layers.BatchNormalization()(z)
print(z.shape)
z = layers.UpSampling2D((2,2))(z) # shape 48 x 48
print(z.shape)

# 4 channels because we have 4 channels in the input
decoder = layers.Conv2D(4, (3, 3), activation = 'sigmoid', padding = 'same')(z) # shape 48 x 48
print(decoder.shape)

# Building the model
autoencoder = Model(input_image, decoder)

# Printing the model summary
print(autoencoder.summary())
########################################################################################################################

# Callbacks for fitting
early_stop = EarlyStopping(monitor='val_loss', mode='min', patience=3)
model_check_point = ModelCheckpoint(filepath=autoencoder_path, save_best_only=True, monitor="val_loss")

# Compiling the autoencoder model
autoencoder.compile(optimizer=Adam(learning_rate= LR), loss='mse')

# Fitting the autoencoder model
# WATCH OUT THE OUTPUT
history_autoencoder = autoencoder.fit(x_train, x_train, epochs= N_EPOCHS, batch_size= Batch_size, validation_data=(x_val, x_val),
                callbacks=[early_stop, model_check_point])

# Saving the autoencoder model
autoencoder.save(autoencoder_path)

# Making model to get the encoded representation
get_encoder = Model(autoencoder.input, autoencoder.get_layer('max_pooling2d_2').output)

# Getting the encoded sns heatmaps
encoded_heatmap = get_encoder.predict(x_val)
encoded_heatmap = encoded_heatmap.reshape((len(x_val), 12*12*64)) # depends on the channel
print(encoded_heatmap.shape)

# Getting the reconstructed sns heatmaps
reconstructed_maps = autoencoder.predict(x_val)

test_pred = autoencoder.evaluate(x_test, x_test)
print(test_pred)
# Visualizing data
show_sns_image(x_val, encoded_heatmap, reconstructed_maps, height= 96, width= 96, title='Test Images - Encoded Test Images - Reconstructed Test Images')
plt.savefig('NonIdeal_Models/2/Autoencoder_Test_22PMU_MissingOneData_10dB')
plt.show()

# Plotting training error and validation error for autoencoder
plt.loglog(history_autoencoder.history['loss'], label='training')
plt.loglog(history_autoencoder.history['val_loss'], label='validation')
plt.title('Training loss vs Validation loss for Autoencoder')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.grid(b = True, which = 'both')
plt.legend()
plt.savefig('NonIdeal_Models/2/Autoencoder_Loss_22PMU_MissingOneData_10dB')
plt.show()


#-------------------- Building the classification model --------------------
# One hot encoding labels
y_test = to_categorical(y_test - 1)
y_train = to_categorical(y_train - 1)
y_val = to_categorical(y_val - 1)

# Classification Model
# --- First we get the same encoding layers from the autoencoder ---
z = layers.Conv2D(16, (3,3), padding='same', activation='relu')(input_image) # shape 96 x 96
z = layers.BatchNormalization()(z)
z = layers.MaxPool2D((2,2))(z) # shape 48 x 48

z = layers.Conv2D(32, (3,3), padding='same')(z) # shape 48 x 48
z = layers.BatchNormalization()(z)
z = layers.MaxPool2D((2,2))(z) # shape 24 x 24
z = activations.relu(z)

z = layers.Conv2D(64, (3,3), padding='same', activation='relu')(z) # 24 x 24
z = layers.BatchNormalization()(z)
encoder = layers.MaxPool2D((2,2))(z) # shape 12 x 12

# Then, we flatten the encoder layer and add some fully connected layers to classify the 8 classes (0 - 7)
flat = layers.Flatten()(encoder)
den = layers.Dense(512, activation='relu')(flat)
drop = layers.Dropout(DROPOUT)(den)
#den = layers.Dense(128, activation='relu')(den)
out = layers.Dense(8, activation='softmax')(drop)

# Hyper parameters
N_EPOCHS = 10 # The remaining hyper-parameters are the same (learning rate and batch size)

# Building the model
full_model = Model(input_image, out)

# Assigned weights to the encoding layers
for l1,l2 in zip(full_model.layers[:11],autoencoder.layers[0:11]):
    l1.set_weights(l2.get_weights())

# Freezing the encoding layers
for layer in full_model.layers[0:11]:
    layer.trainable = False

# Printing the model summary
print(full_model.summary())

model_check_point = ModelCheckpoint(filepath=model_path, save_best_only=True, monitor="val_loss")

# Compiling the classification model
full_model.compile(optimizer=Adam(learning_rate= LR) , loss='categorical_crossentropy', metrics=['accuracy'])

# Fitting the classification model
history_classification = full_model.fit(x_train, y_train, batch_size= Batch_size,epochs= N_EPOCHS,validation_data=(x_val, y_val),
                                        callbacks=[model_check_point])

# Saving the full model
full_model.save(model_path)

# Plotting training error and validation error
# Plotting training error vs validation error and training accuracy vs validation accuracy for the full model
plt.loglog(history_classification.history['loss'], label='training')
plt.loglog(history_classification.history['val_loss'], label='validation')
plt.title('Training Loss vs Validation Loss for Full Model')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.grid(b = True, which = 'both')
plt.legend()
plt.savefig('NonIdeal_Models/2/FullModel_Loss_22PMU_MissingOneData_10dB')
plt.show()

plt.plot(history_classification.history['accuracy'], label='training')
plt.plot(history_classification.history['val_accuracy'], label='validation')
plt.title('Training Accuracy vs Validation Accuracy for Full Model')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.grid(b = True, which = 'both')
plt.legend()
plt.savefig('NonIdeal_Models/2/FullModel_Accuracy_22PMU_MissingOneData_10dB')
plt.show()


# Testing the last model
test_pred = full_model.evaluate(x_test, y_test)
print('Test loss on test set:', test_pred[0])
print('Test accuracy on test set:', test_pred[1])

# Predicting labels
class_pred = full_model.predict(x_test)
class_pred = np.argmax(np.round(class_pred),axis=1)
print(class_pred.shape, y_test.shape)

# Counting the correctly labeled images and plot some images that were correctly classified
correct = np.where(class_pred == np.argmax(y_test, axis=1))[0]
print("Found %d correct labels" % len(correct))
plt.figure(figsize=(10,5))
for i, correct in enumerate(correct[:9]):
    plt.subplot(3, 3, i + 1)
    plt.imshow(x_test[correct])
    plt.title("Predicted {}, Class {}".format(class_pred[correct], np.argmax(y_test, axis=1)[correct]))
plt.savefig('NonIdeal_Models/2/FullModel_Correctly_Labeled_22PMU_MissingOneData_10dB')
plt.show()

# Counting the incorrectly labeled images and plot some images that were incorrectly classified
incorrect = np.where(class_pred != np.argmax(y_test, axis=1))[0]
print("Found %d incorrect labels" % len(incorrect))
for i, incorrect in enumerate(incorrect[:9]):
    plt.subplot(3, 3, i + 1)
    plt.imshow(x_test[incorrect])
    plt.title("Predicted {}, Class {}".format(class_pred[incorrect], np.argmax(y_test, axis=1)[incorrect]))
plt.savefig('NonIdeal_Models/2/FullModel_Incorrectly_Labeled_22PMU_MissingOneData_10dB')
plt.show()


# Printing the classification report of the full model
class_names = ["Class {}".format(i) for i in range(8)]
print(classification_report(np.argmax(y_test, axis=1), class_pred, target_names=class_names))