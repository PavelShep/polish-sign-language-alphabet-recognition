import cv2
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
from collections import deque

model = load_model("model.h5")
actions = ["a", "a_nosowe", "b", "c", "c_kreska", "ch"]

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
sequence = deque(maxlen=30)
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(image)
    keypoints = np.zeros(21 * 3)
    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        keypoints = np.array([[lm.x, lm.y, lm.z] for lm in hand.landmark]).flatten()
    sequence.append(keypoints)

    if len(sequence) == 30:
        prediction = model.predict(np.expand_dims(sequence, axis=0))[0]
        pred_class = np.argmax(prediction)
        confidence = prediction[pred_class]
        if confidence > 0.8:
            cv2.putText(frame, actions[pred_class], (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)

    cv2.imshow('Live', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()