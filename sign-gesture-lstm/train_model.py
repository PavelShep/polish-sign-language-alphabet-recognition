import os
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
import matplotlib.pyplot as plt

# Path to data
DATA_PATH = "data"

# List of actions (classes) — must match collect_data.py
actions = [
    "a", "a_nosowe", "b", "c", "c_kreska", "ch",
    "cz", "d", "e", "e_kreska", "f", "g",
    "h", "i", "j", "k", "l", "l_przekreslone",
    "m", "n", "n_kreska", "o", "o_kreska", "p",
    "r", "rz", "s", "s_kreska", "sz", "t",
    "u", "w", "y", "z", "z_kreska", "z_kropka"
]

# Create label map
label_map = {label: idx for idx, label in enumerate(actions)}

# Load data
X, y = [], []
print("Loading data...")
for action in actions:
    action_path = os.path.join(DATA_PATH, action)
    if not os.path.exists(action_path):
        print(f"Warning: Folder {action_path} not found — skipping.")
        continue
    files = [f for f in os.listdir(action_path) if f.endswith('.npy')]
    print(f"  {action}: {len(files)} samples")
    for file in files:
        seq = np.load(os.path.join(action_path, file))
        X.append(seq)
        y.append(label_map[action])

X = np.array(X)
y = to_categorical(y).astype(int)

if len(X) == 0:
    print("Error: No data loaded. Check the 'data' folder.")
    exit()

print(f"Total samples: {len(X)}")

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build the model
model = Sequential()
model.add(LSTM(64, return_sequences=True, activation='relu', input_shape=(30, 63)))
model.add(LSTM(128, return_sequences=False, activation='relu'))
model.add(Dense(64, activation='relu'))
model.add(Dense(len(actions), activation='softmax'))

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Optional: Early stopping to prevent overfitting
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Train the model and save history
print("Training the model...")
history = model.fit(
    X_train, y_train,
    epochs=100,  # Increased epochs with early stopping
    batch_size=32,
    validation_data=(X_test, y_test),
    callbacks=[early_stopping],
    verbose=1
)

# Save the trained model
model.save("model.h5")
print("Model saved as 'model.h5'")

# Plot training history
print("Generating training plots...")

# Accuracy plot
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)

# Loss plot
plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('training_history.png')
plt.show()

print("Training plots saved as 'training_history.png'")
print("Training completed.")