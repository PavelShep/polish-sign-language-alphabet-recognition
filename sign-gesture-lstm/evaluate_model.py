import os
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
import seaborn as sns
import matplotlib.pyplot as plt

# Paths to data and model
DATA_PATH = "data"
MODEL_PATH = "model.h5"

# List of actions (classes) — must match train_model.py
actions = [
    "a", "a_nosowe", "b", "c", "c_kreska", "ch",
    "cz", "d", "e", "e_kreska", "f", "g",
    "h", "i", "j", "k", "l", "l_przekreslone",
    "m", "n", "n_kreska", "o", "o_kreska", "p",
    "r", "rz", "s", "s_kreska", "sz", "t",
    "u", "w", "y", "z", "z_kreska", "z_kropka"
]

# Load the trained model
print("Loading model...")
model = load_model(MODEL_PATH)
print("Model loaded successfully.")

# Prepare data
X = []
y_true = []

print("Loading test data...")
for action_idx, action in enumerate(actions):
    action_path = os.path.join(DATA_PATH, action)
    if not os.path.exists(action_path):
        print(f"Warning: Folder {action_path} not found — skipping.")
        continue
    
    files = [f for f in os.listdir(action_path) if f.endswith('.npy')]
    print(f"  {action}: {len(files)} samples")
    
    for file in files:
        seq = np.load(os.path.join(action_path, file))
        X.append(seq)
        y_true.append(action_idx)

X = np.array(X)
y_true = np.array(y_true)

if len(X) == 0:
    print("Error: No .npy files found in the 'data' folder.")
    exit()

print(f"Total samples loaded: {len(X)}")

# Make predictions
print("Making predictions...")
y_pred_probs = model.predict(X, verbose=0)
y_pred = np.argmax(y_pred_probs, axis=1)

# Calculate metrics
accuracy = accuracy_score(y_true, y_pred)
print(f"\nOverall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

# Detailed classification report by class
print("\nDetailed classification report:")
report = classification_report(y_true, y_pred, target_names=actions, digits=4, zero_division=0)
print(report)

# Average gesture recognition performance (macro and weighted F1-score)
macro_f1 = f1_score(y_true, y_pred, average='macro')
weighted_f1 = f1_score(y_true, y_pred, average='weighted')

print(f"\nAverage gesture recognition performance (Macro F1-score): {macro_f1:.4f} ({macro_f1*100:.2f}%)")
print(f"Weighted gesture recognition performance (Weighted F1-score): {weighted_f1:.4f} ({weighted_f1*100:.2f}%)")

# Confusion matrix
print("\nGenerating confusion matrix...")
cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(14, 12))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=actions, yticklabels=actions)
plt.title('Confusion Matrix')
plt.xlabel('Predicted Gesture')
plt.ylabel('True Gesture')
plt.tight_layout()
plt.savefig('confusion_matrix.png')
plt.show()

print("\nConfusion matrix saved as 'confusion_matrix.png'")
print("\nModel evaluation completed.")