# Deepfake-Detection
This project focuses on detecting AI-generated deepfake videos using a fine-tuned XceptionNet model. The model is trained on a combination of FaceForensics++ (Meta) and DFDC (DeepFake Detection Challenge) datasets from Kaggle.
The pipeline extracts faces from video frames, preprocesses them, and feeds them into the XceptionNet architecture, which has proven highly effective for visual forgery detection due to its depthwise separable convolutions and efficient feature extraction.
