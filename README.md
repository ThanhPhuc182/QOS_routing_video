# 🚀 Autonomous QoS-Aware Video Routing via Deep Reinforcement Learning

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![PyTorch](https://img.shields.io/badge/PyTorch-Reforcement_Learning-EE4C2C?style=for-the-badge&logo=pytorch)
![SDN](https://img.shields.io/badge/SDN-Mininet%20%7C%20Ryu-005571?style=for-the-badge)
![OpenFlow](https://img.shields.io/badge/Protocol-OpenFlow_1.3-111111?style=for-the-badge)

## 📌 Project Overview
This repository contains the architecture design, mathematical MDP formulation, PyTorch source code, and evaluation reports of a **Closed-loop Autonomous SDN Routing System**. 

Instead of relying on traditional, rigid routing protocols (like OSPF or STP) which fail to address application-layer degradation during network bottlenecks, this project deploys a **Deep Q-Network (DQN)** agent. The AI agent performs real-time network telemetry and dynamically reroutes UDP video streams to maximize the **Quality of Experience (QoE / MOS)**, achieving seamless failover with zero manual intervention.

## ✨ Key Features & Capabilities
*   **Pure Data-Driven AI (White-box DQN):** Designed and trained a custom Neural Network using PyTorch from scratch, bypassing black-box libraries to tightly control the Replay Buffer and Bellman equation updates for a continuous 20-dimensional state space.
*   **QoE-Driven Reward Shaping:** Shifted the optimization paradigm from traditional QoS (Bandwidth/Delay) to QoE. The reward function mathematically approximates the ITU-T E-model for Video **Mean Opinion Score (MOS)**, forcing the agent to learn the critical trade-off between propagation delay and packet loss.
*   **Real-Time Network Telemetry:** Implemented a lightweight, passive monitoring module that calculates link utilization (Mbps) from OpenFlow `tx_bytes` counters, translating physical metrics into state representations without flooding the control plane with active probes.
*   **High Availability (HA) & Seamless Switchover:** The agent acts as an out-of-band dictator, injecting `Priority=65535` flow rules to override default STP behaviors during congestion, and autonomously reverting to the shortest path when the network stabilizes (Hitless Switchback).

---

## 🏗️ Architecture & Network Topology

The system is deployed across a 3-tier Software-Defined Networking architecture (Data Plane, Control Plane, and AI Management Plane) utilizing a Diamond Topology to simulate multi-path routing.

| Component / Node | Role | Protocol / Port | Description |
| :--- | :--- | :--- | :--- |
| `h1` (Sender) | Video Streaming Server | UDP: 1234 | Streams H.264/MPEG video via FFmpeg. Also acts as iPerf3 client for stress testing. |
| `h2` (Receiver)| End-user Client | UDP: 1234 | Plays video via VLC Media Player (Hardware Acceleration disabled for VM stability). |
| `s1, s2, s3, s4` | Open vSwitch (OVS) Nodes | OpenFlow 1.3 | Forms a diamond topology providing 4 end-to-end routing paths. |
| **Ryu Controller** | SDN Control Plane | REST API (8080)| Manages network state and exposes APIs for flow manipulation. |
| **DQN Agent** | AI Management Plane | Python Script | Runs 24/7 inference loop, fetching telemetry and pushing proactive routing decisions. |

---

## 🛠️ Technology Stack
*   **Operating System:** Ubuntu Server 20.04 LTS (Data/Control Plane) & Windows (Training Plane)
*   **Networking & SDN:** Mininet, Ryu Controller, Open vSwitch (OVS), OpenFlow 1.3
*   **AI & MLOps:** Python 3.9+, PyTorch, Gymnasium, Stable-Baselines3 (legacy comparison), Numpy, Matplotlib
*   **Multimedia & Chaos Engineering:** FFmpeg, VLC Media Player, iPerf3, Linux network utilities (`dpctl`, `ovs-ofctl`)

---

## 📊 System Evaluation & Chaos Engineering

To validate the robustness of the AI-driven routing, we conducted rigorous chaos engineering by injecting UDP floods into the data plane, comparing the DQN agent against the Baseline (Spanning Tree Protocol - STP).

### 1. Dynamic Congestion Response (Single Point Failure)
*   **Action:** Injected an 8.5 Mbps `iPerf3` UDP flood into the primary path (`s1 -> s2 -> s4`), saturating the 10 Mbps link bandwidth while the video was streaming.
*   **Observation:** The baseline STP failed to detect the application-layer packet loss, causing the VLC video to severely pixelate and freeze. Conversely, the **RL Agent detected the throughput spike (>8.0 Mbps) within 1 second**. The PyTorch model calculated the Q-values, identifying the primary path's MOS degrading to 1.2, while the secondary path (`s1 -> s3 -> s4`) remained at 4.8. 
*   **Self-healing:** The Agent immediately POSTed `Priority=65535` OpenFlow rules to bypass STP. The video stream recovered to pristine quality instantly.


### 2. Double Congestion Simulation (The "Lesser Evil" Decision)
*   **Action:** Simultaneously congested both the Primary (Path 1) and Secondary (Path 2) routes.
*   **Observation:** The agent evaluated the continuous state space and correctly inferred that both optimal paths were compromised. Instead of routing traffic into a bottleneck (which would cause catastrophic I-frame drops), the agent dynamically shifted the flow to suboptimal, longer backup paths (Path 0 / Path 3).
*   **Conclusion:** This proved the theoretical advantage of **Global Optimization** in Deep Q-Networks. The agent successfully avoided the "Trade-off Trap" by sacrificing marginal latency to maintain 0% packet loss, keeping the MOS stable at ~4.95.

### 3. Seamless Switchback & Resource Optimization
*   **Action:** Terminated the `iPerf3` background traffic to restore normal network conditions.
*   **Observation:** The telemetry module detected the bandwidth drop. The AI re-evaluated the state, realized the primary shortest path was safe, and autonomously executed a **Hitless Switchback** by clearing its custom flow rules.
*   **Conclusion:** The transition caused zero jitter on the client side, demonstrating the system's ability to not only survive faults but also proactively optimize network resources when conditions improve.

### 4. Algorithm Convergence Analysis
Trained the DQN agent over 1,500 episodes in the custom `UltimateDynamicMosEnv`. 
*   **Result:** The moving average reward steadily climbed and stabilized at **~981/1000**, correlating with an average MOS of 4.90/5.0 per step. The Epsilon decay curve aligned perfectly with the exploitation phase, confirming the mathematical soundness of the Reward Shaping function.

---

## 📁 Repository Structure
*   `/project_v5.ipynb` - The core Jupyter Notebook containing MDP formulation, PyTorch DQN architecture, training loop, and Matplotlib visualizations.
*   `/agent_controller.py` - The production-ready Python daemon running the real-time telemetry and PyTorch inference loop.
*   `/topology.py` - Custom Mininet Python script defining the Diamond topology and bandwidth constraints.
*   `/dqn_routing_ultimate.pth` - The exported Neural Network weights (State Dict).



---
*This project was completed as part of the Reinforcement Learning for Networked Systems (NT549) coursework at VNUHCM-UIT.*
