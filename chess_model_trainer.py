import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
import pickle
import os

MODEL_PATH = 'trained_chess_model.h5'
DATA_PATH = 'chess_data.pkl'


def build_model(input_shape):
    """
    Definiuje prostą sieć neuronową do oceny pozycji szachowych.
    To jest bardzo podstawowy model. Prawdziwe modele są znacznie głębsze i bardziej złożone.
    """
    model = keras.Sequential([
        # Pierwsza warstwa gęsta (fully connected)
        layers.Dense(256, activation='relu', input_shape=(input_shape,)),
        layers.Dropout(0.3),  # Dropout dla regularyzacji
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(64, activation='relu'),
        # Ostatnia warstwa z jednym neuronem i aktywacją liniową (ocena pozycji to ciągła wartość)
        layers.Dense(1, activation='linear')
    ])

    # Kompilacja modelu:
    # Optimizer: Adam jest dobrym wyborem dla większości problemów.
    # Loss: MSE (Mean Squared Error) jest odpowiednie dla regresji (przewidywanie wartości ciągłej).
    model.compile(optimizer='adam', loss='mse')

    return model


def train_model():
    """
    Trenuje model TensorFlow na wygenerowanych danych.
    """
    if not os.path.exists(DATA_PATH):
        print(f"Błąd: Plik danych '{DATA_PATH}' nie znaleziony.")
        print("Uruchom najpierw 'chess_dataset_generator.py' aby wygenerować dane.")
        return

    # Wczytaj dane
    with open(DATA_PATH, 'rb') as f:
        data = pickle.load(f)

    X = data['X']
    y = data['y']

    print(f"Wczytano dane. Kształt X: {X.shape}, Kształt y: {y.shape}")

    # Zbuduj model
    model = build_model(X.shape[1])
    model.summary()

    # Trenuj model
    # epochs: Liczba przejść przez cały zbiór danych.
    # batch_size: Ile próbek jednocześnie podawać modelowi.
    # validation_split: Procent danych używanych do walidacji (monitorowania, czy model nie przetrenowuje się).
    history = model.fit(X, y, epochs=50, batch_size=32, validation_split=0.2, verbose=1)

    # Zapisz wytrenowany model
    model.save(MODEL_PATH)
    print(f"Model wytrenowany i zapisany jako '{MODEL_PATH}'")

    # Opcjonalnie: wizualizacja historii treningu (wymaga matplotlib)
    # import matplotlib.pyplot as plt
    # plt.plot(history.history['loss'], label='Loss (trening)')
    # plt.plot(history.history['val_loss'], label='Loss (walidacja)')
    # plt.xlabel('Epoka')
    # plt.ylabel('Strata')
    # plt.legend()
    # plt.show()


if __name__ == '__main__':
    train_model()