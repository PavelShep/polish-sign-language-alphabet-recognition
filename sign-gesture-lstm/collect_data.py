import os
import cv2
import numpy as np
import mediapipe as mp

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1)
DATA_PATH = "data"
actions = [
    "a", "a_nosowe", "b", "c", "c_kreska", "ch", 
    "cz", "d", "e", "e_kreska", "f", "g", 
    "h", "i", "j", "k", "l", "l_przekreslone",
    "m", "n", "n_kreska", "o", "o_kreska", "p",
    "r", "rz", "s", "s_kreska", "sz", "t",
    "u", "w", "y", "z", "z_kreska", "z_kropka"
    ]
seq_length = 30
samples_per_class = 30

for action in actions:
    dir_path = os.path.join(DATA_PATH, action)
    os.makedirs(dir_path, exist_ok=True)
    cap = cv2.VideoCapture(0)

    collected = 0
    while collected < samples_per_class:
        ret, frame = cap.read()
        frame_copy = frame.copy()
        cv2.putText(frame_copy, f"Press 'r', to record letter {action} {collected + 1}/{samples_per_class}", 
                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Ready', frame_copy)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            print(f"Recording sample {collected + 1} for '{action}'")
            sequence = []
            while len(sequence) < seq_length:
                ret, frame = cap.read()
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(image)
                keypoints = np.zeros(21 * 3)
                if results.multi_hand_landmarks:
                    hand = results.multi_hand_landmarks[0]
                    keypoints = np.array([[lm.x, lm.y, lm.z] for lm in hand.landmark]).flatten()
                sequence.append(keypoints)
                cv2.putText(frame, f'Recording {len(sequence)}/{seq_length}', (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow('Collecting', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            np.save(os.path.join(dir_path, f"{collected}.npy"), np.array(sequence))
            print(f"Saved sample {collected + 1} for '{action}'")
            collected += 1

    cap.release()
    cv2.destroyAllWindows()
