# Plastic Bag Detection System

A real-time plastic bag detection system using YOLOv5 and Raspberry Pi 5. The system processes low-resolution video (320×240 at 10 FPS), performs cloud-based object detection via Roboflow, and sends smart alerts through Pushbullet when plastic bags are detected.

♻️ Low-cost (<$100) embedded vision system for automated plastic waste sorting. Achieves 85% accuracy at 10 FPS using a custom-trained model.

---

## Features

- Real-time plastic bag detection
- Cloud-based YOLOv5 model inference
- Morphological filtering to reduce false positives
- Smart notifications via Pushbullet
- Lightweight for Raspberry Pi 5

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/22olivia/Plastic-Bag-Detector.git
cd Plastic-Bag-Detector

