import keras
from keras.datasets import mnist
from keras.models import Sequential, Model
from keras.layers import AveragePooling2D, Input, ZeroPadding2D, Add, Activation, Dense, Dropout, Flatten, BatchNormalization, Conv2D, MaxPooling2D
from keras.initializers import glorot_uniform
import numpy as np

# Properties
batch_size = 128
num_classes = 10
epochs = 500
img_rows, img_cols = 28, 28

(x_train, y_train), (x_test, y_test) = mnist.load_data()

x_train = x_train.reshape(60000, 28, 28, 1)
x_test = x_test.reshape(10000, 28, 28, 1)

# One hot encoder
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)


def identityBlock(f, filters, stage, block):
    def func(x):
        # Defining name basis
        conv_name_base = 'res' + str(stage) + block + '_branch'
        bn_name_base = 'bn' + str(stage) + block + '_branch'

        # Retrieve Filters
        F1, F2, F3 = filters
        X = x
        # Save the input value
        X_shortcut = X

        # First component of main path
        X = Conv2D(filters=F1,
                kernel_size=(1, 1),
                strides=(1, 1),
                padding='valid',
                name=conv_name_base + '2a',
                kernel_initializer=glorot_uniform(seed=0))(X)
        X = BatchNormalization(axis=3, name=bn_name_base + '2a')(X)
        X = Activation('relu')(X)

        # Second component of main path
        X = Conv2D(filters=F2,
                kernel_size=(1, 1),
                strides=(1, 1),
                padding='valid',
                name=conv_name_base + '2b',
                kernel_initializer=glorot_uniform(seed=0))(X)
        X = BatchNormalization(axis=3, name=bn_name_base + '2b')(X)
        X = Activation('relu')(X)

        # Third component of main path
        X = Conv2D(filters=F3,
                kernel_size=(1, 1),
                strides=(1, 1),
                padding='valid',
                name=conv_name_base + '2c',
                kernel_initializer=glorot_uniform(seed=0))(X)
        X = BatchNormalization(axis=3, name=bn_name_base + '2c')(X)
        X = Activation('relu')(X)

        # Final step: Add shortcut value to main path and pass it through a RELU activation
        X = Add()([X, X_shortcut])
        X = Activation('relu')(X)
        return X
    return func


def convolutionalBlock(f, filters, stage, block, s=2):
    def func(x):
        # Defining name basis
        conv_name_base = 'res' + str(stage) + block + '_branch'
        bn_name_base = 'bn' + str(stage) + block + '_branch'

        # Retrive Filters
        F1, F2, F3 = filters
        X = x
        # Save the input value
        X_shortcut = X

        ### MAIN PATH ###

        # First component of main path
        X = Conv2D(filters=F1,
                kernel_size=(1, 1),
                strides=(s, s),
                padding='valid',
                name=conv_name_base + '2a',
                kernel_initializer=glorot_uniform(seed=0))(X)
        X = BatchNormalization(axis=3, name=bn_name_base + '2a')(X)
        X = Activation('relu')(X)

        # Second component of main path
        X = Conv2D(filters=F2,
                kernel_size=(f, f),
                strides=(1, 1),
                padding='same',
                name=conv_name_base + '2b',
                kernel_initializer=glorot_uniform(seed=0))(X)
        X = BatchNormalization(axis=3, name=bn_name_base + '2b')(X)
        X = Activation('relu')(X)

        # Third component of main path
        X = Conv2D(filters=F3,
                kernel_size=(1, 1),
                strides=(1, 1),
                padding='valid',
                name=conv_name_base + '2c',
                kernel_initializer=glorot_uniform(seed=0))(X)
        X = BatchNormalization(axis=3, name=bn_name_base + '2c')(X)
        X = Activation('relu')(X)

        ### SHORTCUT PATH ###
        X_shortcut = Conv2D(filters=F3,
                            kernel_size=(1, 1),
                            strides=(s, s),
                            padding='valid',
                            name=conv_name_base + '1',  
                            kernel_initializer=glorot_uniform(seed=0))(X_shortcut)
        X_shortcut = BatchNormalization(
            axis=3, name=bn_name_base + '1')(X_shortcut)

        # Final step: Add shortcut value to main path. and pass it through a RELU activation
        X = Add()([X, X_shortcut])
        X = Activation('relu')(X)

        return X
    return func


def resnet50(input_shape=(64, 64, 3), classes=6):

    # Define the input as a tensor with shape input_shape
    X_input = Input(input_shape)

    # Zero padding
    X = ZeroPadding2D((3, 3))(X_input)

    # Stage 1
    X = Conv2D(64, kernel_size=(7, 7), strides=(2, 2), name='conv1',
               kernel_initializer=glorot_uniform(seed=0))(X)
    X = BatchNormalization(axis=3, name='bn_conv1')(X)
    X = Activation('relu')(X)
    X = MaxPooling2D((3, 3), strides=(2, 2))(X)

    # Stage 2
    X = convolutionalBlock(f=3, filters = [64,64,256],   stage=2, block='a', s=1)(X)
    X = identityBlock(3, [64,64,256], stage = 2, block='b')(X)
    X = identityBlock(3, [64,64,256], stage = 2, block='c')(X)

    # Stage 3
    X = convolutionalBlock(f=3, filters=[128, 128, 512], stage=3, block='a', s=2)(X)
    X = identityBlock(3, [128, 128, 512], stage=3, block='b')(X)
    X = identityBlock(3, [128, 128, 512], stage=3, block='c')(X)
    X = identityBlock(3, [128, 128, 512], stage=3, block='d')(X)

    # Stage 4
    X = convolutionalBlock(f=3, filters=[256, 256, 1024], stage=4, block='a', s=2)(X)
    X = identityBlock(3, [256, 256, 1024], stage=4, block='b')(X)
    X = identityBlock(3, [256, 256, 1024], stage=4, block='c')(X)
    X = identityBlock(3, [256, 256, 1024], stage=4, block='d')(X)
    X = identityBlock(3, [256, 256, 1024], stage=4, block='e')(X)
    X = identityBlock(3, [256, 256, 1024], stage=4, block='f')(X)

    # Stage 5
    X = convolutionalBlock(f=3, filters=[512, 512, 2048], stage=5, block='a', s=2)(X)
    X = identityBlock(3, [512, 512, 2048], stage=5, block='b')(X)
    X = identityBlock(3, [512, 512, 2048], stage=5, block='c')(X)
    
    # AVGPOOL
    X = AveragePooling2D(pool_size=(2,2), padding='same')(X)

    # Output layer
    X = Flatten()(X)
    X = Dense(classes, activation='softmax', name='fc' + str(classes), kernel_initializer = glorot_uniform(seed=0))(X)
    
    # Create model
    model = Model(inputs = X_input, outputs = X, name='ResNet50')
    
    # The model should be compiled before training
    model.compile(loss=keras.losses.categorical_crossentropy,
                  optimizer=keras.optimizers.Adadelta(),
                  metrics=['accuracy'])
    return model

model = resnet50(input_shape=(28,28,1),classes=num_classes)

callbacks = [
    keras.callbacks.EarlyStopping(monitor='val_loss',min_delta=0,patience=5,mode='auto')
]

# Fit the model to dataset
model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          callbacks = callbacks,
          validation_split=0.2)

score = model.evaluate(x_test, y_test, verbose=0)

print('Test loss:', score[0])
print('Test accuracy:', score[1])
